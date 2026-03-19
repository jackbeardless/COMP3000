"""
Clusters router — retrieve scan results and submit analyst annotations.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user
from database import get_admin_client
from models import AnnotationUpdate

router = APIRouter(tags=["clusters"])


def _db():
    return get_admin_client()


@router.get("/scans/{scan_id}/clusters")
async def list_clusters(
    scan_id: str,
    verdict: Optional[str] = Query(None, description="Filter by verdict: likely, maybe, low"),
    platform: Optional[str] = Query(None, description="Filter by platform name"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    user: dict = Depends(get_current_user),
):
    """
    Return all clusters for a scan, sorted by final_confidence descending.
    Supports optional filtering by verdict, platform, and minimum confidence.
    """
    loop = asyncio.get_event_loop()

    # Verify scan belongs to the user via the scans table
    scan_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("scans").select("id").eq("id", scan_id).eq("user_id", user["id"]).execute()
    )
    if not scan_resp.data:
        raise HTTPException(status_code=404, detail="Scan not found.")

    def _query():
        q = _db().table("clusters").select("*").eq("scan_id", scan_id)
        if verdict:
            q = q.eq("verdict", verdict)
        if platform:
            q = q.eq("platform", platform)
        if min_confidence > 0:
            q = q.gte("final_confidence", min_confidence)
        return q.order("final_confidence", desc=True).execute()

    resp = await loop.run_in_executor(None, _query)
    return resp.data


@router.patch("/clusters/{cluster_id}/annotation")
async def annotate_cluster(
    cluster_id: str,
    body: AnnotationUpdate,
    user: dict = Depends(get_current_user),
):
    """
    Submit or update an analyst annotation on a cluster.
    Analysts can mark clusters as confirmed, disputed, or needs_review,
    and add a free-text note.
    """
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided.")

    updates["analyst_updated_at"] = datetime.now(timezone.utc).isoformat()

    loop = asyncio.get_event_loop()

    # Verify the cluster's scan belongs to the user
    cluster_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("clusters").select("scan_id").eq("id", cluster_id).single().execute()
    )
    if not cluster_resp.data:
        raise HTTPException(status_code=404, detail="Cluster not found.")

    scan_id = cluster_resp.data["scan_id"]
    scan_resp = await loop.run_in_executor(
        None,
        lambda: _db().table("scans").select("id").eq("id", scan_id).eq("user_id", user["id"]).execute()
    )
    if not scan_resp.data:
        raise HTTPException(status_code=403, detail="Not authorised.")

    resp = await loop.run_in_executor(
        None,
        lambda: _db().table("clusters").update(updates).eq("id", cluster_id).execute()
    )
    return resp.data[0]
