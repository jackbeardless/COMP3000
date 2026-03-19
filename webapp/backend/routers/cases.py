"""
Cases router — create, list, update, and delete investigation cases.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import get_admin_client
from models import CaseCreate, CaseUpdate

router = APIRouter(prefix="/cases", tags=["cases"])


def _db():
    return get_admin_client()


@router.get("")
async def list_cases(user: dict = Depends(get_current_user)):
    """List all cases for the authenticated user, newest first."""
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("case_summaries")
            .select("*")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .execute()
    )
    return resp.data


@router.post("", status_code=201)
async def create_case(body: CaseCreate, user: dict = Depends(get_current_user)):
    """Create a new investigation case."""
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: _db().table("cases").insert({
            "user_id": user["id"],
            "name": body.name,
            "target": body.target,
            "description": body.description,
        }).execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create case.")
    return resp.data[0]


@router.get("/{case_id}")
async def get_case(case_id: str, user: dict = Depends(get_current_user)):
    """Get a single case by ID."""
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("cases")
            .select("*")
            .eq("id", case_id)
            .eq("user_id", user["id"])
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
    resp = await loop.run_in_executor(
        None,
        lambda: _db()
            .table("cases")
            .update(updates)
            .eq("id", case_id)
            .eq("user_id", user["id"])
            .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Case not found.")
    return resp.data[0]


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: str, user: dict = Depends(get_current_user)):
    """Delete a case and all its scans/clusters (cascades in DB)."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: _db()
            .table("cases")
            .delete()
            .eq("id", case_id)
            .eq("user_id", user["id"])
            .execute()
    )
