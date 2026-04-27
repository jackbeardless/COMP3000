"""
Orgs router — organisation management, member invites, and deletion requests.
"""
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import get_admin_client
from models import OrgCreate, InviteMember, AcceptInvite, DeletionRequestCreate
from org_helpers import get_membership
from email_service import send_invite_email

router = APIRouter(prefix="/orgs", tags=["orgs"])


def _db():
    return get_admin_client()


# ── Create organisation ────────────────────────────────────────

@router.post("", status_code=201)
async def create_org(body: OrgCreate, user: dict = Depends(get_current_user)):
    """Create a new organisation. The creator becomes admin."""
    loop = asyncio.get_event_loop()

    # A user can only belong to one org
    existing = await get_membership(user["id"], loop)
    if existing:
        raise HTTPException(status_code=409, detail="You are already a member of an organisation.")

    # Insert org
    org_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("organisations").insert({
            "name": body.name,
            "admin_user_id": user["id"],
        }).execute()
    )
    if not org_resp.data:
        raise HTTPException(status_code=500, detail="Failed to create organisation.")
    org = org_resp.data[0]

    # Add creator as active admin member
    await loop.run_in_executor(
        None,
        lambda: _db().table("organisation_members").insert({
            "org_id": org["id"],
            "user_id": user["id"],
            "email": user["email"],
            "role": "admin",
            "status": "active",
            "joined_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    )
    return org


# ── Get my org ─────────────────────────────────────────────────

@router.get("/me")
async def get_my_org(user: dict = Depends(get_current_user)):
    """Return the current user's organisation and role, or 404 if not in one."""
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership:
        raise HTTPException(status_code=404, detail="Not in any organisation.")

    org_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("organisations").select("*").eq("id", membership["org_id"]).single().execute()
    )
    if not org_resp.data:
        raise HTTPException(status_code=404, detail="Organisation not found.")

    return {**org_resp.data, "role": membership["role"]}


# ── List members ───────────────────────────────────────────────

@router.get("/{org_id}/members")
async def list_members(org_id: str, user: dict = Depends(get_current_user)):
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership or membership["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Not a member of this organisation.")

    resp = await loop.run_in_executor(
        None,
        lambda: _db().table("organisation_members")
            .select("id, user_id, email, role, status, invited_at, joined_at")
            .eq("org_id", org_id)
            .order("joined_at", desc=False)
            .execute()
    )
    return resp.data


# ── Invite member ──────────────────────────────────────────────

@router.post("/{org_id}/invite", status_code=201)
async def invite_member(org_id: str, body: InviteMember, user: dict = Depends(get_current_user)):
    """Admin invites a user by email. Sends them an invite link."""
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership or membership["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Not a member of this organisation.")
    if membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invite members.")

    # Fetch org name for the email
    org_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("organisations").select("name").eq("id", org_id).single().execute()
    )
    org_name = org_resp.data["name"] if org_resp.data else "your organisation"

    # Check not already a member
    existing_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("organisation_members")
            .select("id, status")
            .eq("org_id", org_id)
            .eq("email", body.email)
            .limit(1)
            .execute()
    )
    if existing_resp.data:
        status = existing_resp.data[0]["status"]
        if status == "active":
            raise HTTPException(status_code=409, detail="This user is already a member.")
        # Re-use existing pending invite (return it)
        return existing_resp.data[0]

    # Insert pending invite
    invite_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("organisation_members").insert({
            "org_id": org_id,
            "email": body.email,
            "role": "member",
            "status": "pending",
        }).execute()
    )
    if not invite_resp.data:
        raise HTTPException(status_code=500, detail="Failed to create invite.")

    invite = invite_resp.data[0]

    # Send email (best-effort — don't fail the request if email breaks)
    try:
        send_invite_email(
            to_email=body.email,
            org_name=org_name,
            invite_token=str(invite["invite_token"]),
            admin_email=user["email"],
        )
    except Exception as e:
        print(f"Warning: failed to send invite email: {e}")

    return invite


# ── Accept invite ──────────────────────────────────────────────

@router.post("/accept-invite")
async def accept_invite(body: AcceptInvite, user: dict = Depends(get_current_user)):
    """Accept an invite by token. User must be logged in with the invited email."""
    loop = asyncio.get_event_loop()

    # Check user isn't already in an org
    existing = await get_membership(user["id"], loop)
    if existing:
        raise HTTPException(status_code=409, detail="You are already a member of an organisation.")

    # Find the invite by token
    invite_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("organisation_members")
            .select("*")
            .eq("invite_token", body.token)
            .eq("status", "pending")
            .limit(1)
            .execute()
    )
    if not invite_resp.data:
        raise HTTPException(status_code=404, detail="Invite not found or already used.")

    invite = invite_resp.data[0]

    # Security: email must match
    if invite["email"].lower() != user["email"].lower():
        raise HTTPException(status_code=403, detail="This invite was sent to a different email address.")

    # Activate membership
    await loop.run_in_executor(
        None,
        lambda: _db().table("organisation_members").update({
            "user_id": user["id"],
            "status": "active",
            "joined_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", invite["id"]).execute()
    )

    return {"org_id": invite["org_id"], "role": invite["role"]}


# ── Remove member ──────────────────────────────────────────────

@router.delete("/{org_id}/members/{member_id}", status_code=204)
async def remove_member(org_id: str, member_id: str, user: dict = Depends(get_current_user)):
    """Admin removes a member from the org."""
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership or membership["org_id"] != org_id or membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove members.")

    await loop.run_in_executor(
        None,
        lambda: _db().table("organisation_members")
            .delete()
            .eq("id", member_id)
            .eq("org_id", org_id)
            .execute()
    )


# ── Deletion requests ──────────────────────────────────────────

@router.post("/deletion-requests", status_code=201)
async def create_deletion_request(body: DeletionRequestCreate, user: dict = Depends(get_current_user)):
    """Any org member can request deletion of a case or scan."""
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership:
        raise HTTPException(status_code=403, detail="Not in any organisation.")

    resp = await loop.run_in_executor(
        None,
        lambda: _db().table("deletion_requests").insert({
            "org_id": membership["org_id"],
            "requested_by": user["id"],
            "resource_type": body.resource_type,
            "resource_id": body.resource_id,
            "resource_name": body.resource_name,
        }).execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create deletion request.")
    return resp.data[0]


@router.get("/{org_id}/deletion-requests")
async def list_deletion_requests(org_id: str, user: dict = Depends(get_current_user)):
    """Admin sees all pending requests; members see only their own."""
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership or membership["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="Not a member of this organisation.")

    query = (
        _db().table("deletion_requests")
        .select("*")
        .eq("org_id", org_id)
        .eq("status", "pending")
        .order("created_at", desc=True)
    )
    if membership["role"] != "admin":
        query = query.eq("requested_by", user["id"])

    resp = await loop.run_in_executor(None, lambda: query.execute())
    return resp.data


@router.post("/deletion-requests/{request_id}/approve", status_code=200)
async def approve_deletion_request(request_id: str, user: dict = Depends(get_current_user)):
    """Admin approves and executes the deletion."""
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership or membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can approve deletion requests.")

    req_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("deletion_requests")
            .select("*")
            .eq("id", request_id)
            .eq("org_id", membership["org_id"])
            .eq("status", "pending")
            .single()
            .execute()
    )
    if not req_resp.data:
        raise HTTPException(status_code=404, detail="Deletion request not found.")

    req = req_resp.data

    # Execute the deletion
    if req["resource_type"] == "case":
        await loop.run_in_executor(
            None,
            lambda: _db().table("cases").delete().eq("id", req["resource_id"]).execute()
        )
    elif req["resource_type"] == "scan":
        await loop.run_in_executor(
            None,
            lambda: _db().table("scans").delete().eq("id", req["resource_id"]).execute()
        )

    # Mark request as approved
    await loop.run_in_executor(
        None,
        lambda: _db().table("deletion_requests").update({
            "status": "approved",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": user["id"],
        }).eq("id", request_id).execute()
    )
    return {"status": "approved"}


@router.post("/deletion-requests/{request_id}/reject", status_code=200)
async def reject_deletion_request(request_id: str, user: dict = Depends(get_current_user)):
    """Admin rejects the deletion request."""
    loop = asyncio.get_event_loop()
    membership = await get_membership(user["id"], loop)
    if not membership or membership["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reject deletion requests.")

    await loop.run_in_executor(
        None,
        lambda: _db().table("deletion_requests").update({
            "status": "rejected",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": user["id"],
        }).eq("id", request_id).eq("org_id", membership["org_id"]).execute()
    )
    return {"status": "rejected"}
