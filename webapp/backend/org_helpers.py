"""
org_helpers.py — shared utilities for org-scoped access control.
"""
import asyncio
from typing import Optional
from database import get_admin_client


async def get_membership(user_id: str, loop: asyncio.AbstractEventLoop) -> Optional[dict]:
    """
    Returns {'org_id': ..., 'role': 'admin'|'member'} for the user's active
    org membership, or None if they are not in any organisation.
    """
    resp = await loop.run_in_executor(
        None,
        lambda: get_admin_client()
            .table("organisation_members")
            .select("org_id, role")
            .eq("user_id", user_id)
            .eq("status", "active")
            .limit(1)
            .execute()
    )
    return resp.data[0] if resp.data else None
