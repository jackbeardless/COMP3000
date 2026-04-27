"""
Scans router — create/trigger scans and stream live progress via WebSocket.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from auth import get_current_user
from database import get_admin_client
from models import ScanCreate
from org_helpers import get_membership
from pipeline_runner import run_pipeline_async, get_progress

router = APIRouter(tags=["scans"])


def _db():
    return get_admin_client()


async def _require_membership(user_id: str, loop):
    membership = await get_membership(user_id, loop)
    if not membership:
        raise HTTPException(status_code=403, detail="You must be in an organisation to manage scans.")
    return membership


async def _verify_case_in_org(case_id: str, org_id: str, loop) -> dict:
    """Verify that a case belongs to the given org and return it."""
    resp = await loop.run_in_executor(
        None,
        lambda: _db().table("cases").select("*").eq("id", case_id).eq("org_id", org_id).single().execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Case not found.")
    return resp.data


@router.get("/cases/{case_id}/scans")
async def list_scans(case_id: str, user: dict = Depends(get_current_user)):
    """List all scans for a case, newest first."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)
    await _verify_case_in_org(case_id, membership["org_id"], loop)

    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("scan_summaries")
            .select("*")
            .eq("case_id", case_id)
            .order("created_at", desc=True)
            .execute()
    )
    return resp.data


@router.post("/cases/{case_id}/scans", status_code=201)
async def create_scan(
    case_id: str,
    body: ScanCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Create a scan record and immediately trigger the pipeline in the background."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)
    case = await _verify_case_in_org(case_id, membership["org_id"], loop)

    target = body.scan_target or case.get("target") or ""
    if not target:
        raise HTTPException(status_code=400, detail="A username is required to run a scan.")

    known_info = case.get("known_info") or {}
    config_dict = body.config.model_dump()
    config_dict["known_info"] = known_info

    scan_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("scans").insert({
            "case_id": case_id,
            "user_id": user["id"],
            "target": target,
            "status": "queued",
            "config": config_dict,
        }).execute()
    )
    if not scan_resp.data:
        raise HTTPException(status_code=500, detail="Failed to create scan.")
    scan = scan_resp.data[0]

    background_tasks.add_task(run_pipeline_async, scan["id"], target, config_dict)
    return scan


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str, user: dict = Depends(get_current_user)):
    """Get a single scan with aggregated cluster stats."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)

    # Get scan, then verify its case belongs to user's org
    scan_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("scan_summaries").select("*").eq("scan_id", scan_id).single().execute()
    )
    if not scan_resp.data:
        raise HTTPException(status_code=404, detail="Scan not found.")

    await _verify_case_in_org(scan_resp.data["case_id"], membership["org_id"], loop)
    return scan_resp.data


@router.delete("/scans/{scan_id}", status_code=204)
async def delete_scan(scan_id: str, user: dict = Depends(get_current_user)):
    """Delete a scan directly — admin only. Members should use the deletion request API."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)
    if membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete scans directly. Use the deletion request flow.")

    scan_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("scans").select("case_id").eq("id", scan_id).single().execute()
    )
    if not scan_resp.data:
        raise HTTPException(status_code=404, detail="Scan not found.")

    await _verify_case_in_org(scan_resp.data["case_id"], membership["org_id"], loop)

    await loop.run_in_executor(
        None,
        lambda: _db().table("scans").delete().eq("id", scan_id).execute()
    )


@router.websocket("/scans/{scan_id}/ws")
async def scan_progress_ws(websocket: WebSocket, scan_id: str):
    """
    WebSocket endpoint that streams pipeline progress for a scan.
    No auth on WS — the scan_id UUID is the effective token.
    """
    await websocket.accept()
    sent = 0
    try:
        while True:
            messages = get_progress(scan_id)
            new_messages = messages[sent:]
            for msg in new_messages:
                await websocket.send_json(msg)
                sent += 1
                if msg.get("done"):
                    await websocket.close()
                    return
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
