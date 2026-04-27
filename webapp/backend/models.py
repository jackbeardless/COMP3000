from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ── Organisations ──────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str


class InviteMember(BaseModel):
    email: str


class AcceptInvite(BaseModel):
    token: str


class DeletionRequestCreate(BaseModel):
    resource_type: str   # "case" | "scan"
    resource_id: str
    resource_name: Optional[str] = None


# ── Cases ─────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    name: str
    target: str = ""
    description: Optional[str] = None
    known_info: Optional[Dict] = None


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # "active" | "archived"
    known_info: Optional[Dict] = None


class CaseResponse(BaseModel):
    id: str
    user_id: str
    name: str
    target: str
    description: Optional[str]
    status: str
    known_info: Optional[Dict]
    created_at: datetime
    updated_at: datetime


# ── Scans ─────────────────────────────────────────────────────

class ScanConfig(BaseModel):
    """Pipeline configuration for a scan run."""
    threshold: float = 0.75
    model: str = "gemini-2.5-flash"
    batch_size: int = 20
    skip_noise: bool = True
    dry_run: bool = False
    skip_llm: bool = False
    run_spiderfoot: bool = True  # False = use latest existing SpiderFoot file


class ScanCreate(BaseModel):
    config: ScanConfig = ScanConfig()
    scan_target: Optional[str] = None  # override case target for this scan only


class ScanResponse(BaseModel):
    id: str
    case_id: str
    user_id: str
    target: str
    status: str
    config: Dict
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    created_at: datetime


# ── Clusters ──────────────────────────────────────────────────

class ClusterResponse(BaseModel):
    id: str
    scan_id: str
    cluster_key: str
    platform: Optional[str]
    handle: Optional[str]
    urls: List[str]
    heuristic_score: float
    final_confidence: Optional[float]
    verdict: Optional[str]
    llm_status: Optional[str]
    rationale: Optional[str]
    flags: List[str]
    signals: List[str]
    score_features: List[Dict]
    source_reliability: str
    contradiction_flags: List[str]
    raw_data: Dict
    analyst_verdict: Optional[str]
    analyst_note: Optional[str]
    analyst_updated_at: Optional[datetime]
    created_at: datetime


class AnnotationUpdate(BaseModel):
    analyst_verdict: Optional[str] = None  # "confirmed" | "disputed" | "needs_review"
    analyst_note: Optional[str] = None


# ── Progress (WebSocket messages) ─────────────────────────────

class ProgressMessage(BaseModel):
    step: str          # "spiderfoot" | "normalize" | "cluster" | "reduce" | "llm" | "saving"
    status: str        # "running" | "complete" | "failed"
    message: str
    done: bool = False # True on the final message (success or failure)
