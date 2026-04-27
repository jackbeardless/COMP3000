"""
Cases router — create, list, update, and delete investigation cases.
All cases are scoped to the user's organisation.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import get_admin_client
from models import CaseCreate, CaseUpdate
from org_helpers import get_membership

router = APIRouter(prefix="/cases", tags=["cases"])


def _db():
    return get_admin_client()


async def _require_membership(user_id: str, loop):
    membership = await get_membership(user_id, loop)
    if not membership:
        raise HTTPException(status_code=403, detail="You must be in an organisation to manage cases.")
    return membership


@router.get("")
async def list_cases(user: dict = Depends(get_current_user)):
    """List all cases for the user's organisation, newest first."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)

    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("case_summaries")
            .select("*")
            .eq("org_id", membership["org_id"])
            .order("created_at", desc=True)
            .execute()
    )
    return resp.data


@router.post("", status_code=201)
async def create_case(body: CaseCreate, user: dict = Depends(get_current_user)):
    """Create a new investigation case within the user's organisation."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)

    resp = await loop.run_in_executor(
        None,
        lambda: _db().table("cases").insert({
            "user_id": user["id"],
            "org_id": membership["org_id"],
            "name": body.name,
            "target": body.target,
            "description": body.description,
            "known_info": body.known_info or {},
        }).execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create case.")
    return resp.data[0]


@router.get("/{case_id}")
async def get_case(case_id: str, user: dict = Depends(get_current_user)):
    """Get a single case by ID (must belong to user's org)."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)

    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("cases")
            .select("*")
            .eq("id", case_id)
            .eq("org_id", membership["org_id"])
            .single()
            .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Case not found.")
    return resp.data


@router.patch("/{case_id}")
async def update_case(case_id: str, body: CaseUpdate, user: dict = Depends(get_current_user)):
    """Update a case's name, description, or status."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)

    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("cases")
            .update(updates)
            .eq("id", case_id)
            .eq("org_id", membership["org_id"])
            .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Case not found.")
    return resp.data[0]


@router.get("/{case_id}/profile")
async def get_case_profile(case_id: str, user: dict = Depends(get_current_user)):
    """Return the case's known_info and all analyst-confirmed clusters across every scan."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)

    case_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("cases").select("known_info").eq("id", case_id).eq("org_id", membership["org_id"]).single().execute()
    )
    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found.")

    scans_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("scans").select("id").eq("case_id", case_id).execute()
    )
    scan_ids = [s["id"] for s in (scans_resp.data or [])]

    confirmed = []
    if scan_ids:
        clusters_resp = await loop.run_in_executor(
            None,
            lambda: _db().table("clusters")
                .select("id, scan_id, platform, handle, urls, final_confidence, heuristic_score, verdict, analyst_note, raw_data")
                .in_("scan_id", scan_ids)
                .eq("analyst_verdict", "confirmed")
                .order("final_confidence", desc=True)
                .execute()
        )
        confirmed = clusters_resp.data or []

    return {"known_info": case_resp.data.get("known_info") or {}, "confirmed_accounts": confirmed}


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: str, user: dict = Depends(get_current_user)):
    """Delete a case directly — admin only. Members should use the deletion request API."""
    loop = asyncio.get_event_loop()
    membership = await _require_membership(user["id"], loop)

    if membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete cases directly. Use the deletion request flow.")

    await loop.run_in_executor(
        None,
        lambda: _db()
            .table("cases")
            .delete()
            .eq("id", case_id)
            .eq("org_id", membership["org_id"])
            .execute()
    )
