"""
Scans router — create/trigger scans and stream live progress via WebSocket.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from auth import get_current_user
from database import get_admin_client
from models import ScanCreate
from pipeline_runner import run_pipeline_async, get_progress

router = APIRouter(tags=["scans"])


def _db():
    return get_admin_client()


@router.get("/cases/{case_id}/scans")
async def list_scans(case_id: str, user: dict = Depends(get_current_user)):
    """List all scans for a case, newest first."""
    # Verify the case belongs to the user
    loop = asyncio.get_event_loop()
    case_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("cases").select("id").eq("id", case_id).eq("user_id", user["id"]).execute()
    )
    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found.")

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
    """
    Create a scan record and immediately trigger the pipeline in the background.
    Returns the scan ID so the client can open the WebSocket progress stream.
    """
    loop = asyncio.get_event_loop()

    # Verify case ownership and get target
    case_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("cases").select("*").eq("id", case_id).eq("user_id", user["id"]).single().execute()
    )
    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found.")
    target = case_resp.data["target"]

    # Create the scan record
    config_dict = body.config.model_dump()
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

    # Kick off the pipeline as a background task
    background_tasks.add_task(run_pipeline_async, scan["id"], target, config_dict)

    return scan


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str, user: dict = Depends(get_current_user)):
    """Get a single scan with aggregated cluster stats."""
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("scan_summaries")
            .select("*")
            .eq("scan_id", scan_id)
            .eq("user_id", user["id"])
            .single()
            .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return resp.data


@router.websocket("/scans/{scan_id}/ws")
async def scan_progress_ws(websocket: WebSocket, scan_id: str):
    """
    WebSocket endpoint that streams pipeline progress for a scan.
    Sends one message per pipeline step. Closes when the pipeline finishes.

    No auth on WS (Supabase token can't be sent as a header in browser WS);
    the scan_id is effectively the access token here since it's a UUID.
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
