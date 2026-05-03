from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import ArtifactType, EvidenceFormat, EvidenceStatus, PhaseStatus, ProjectStatus, RiskTier, SystemType


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    system_type: SystemType = SystemType.llm_chatbot
    risk_tier: RiskTier = RiskTier.tier_2


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    risk_tier: RiskTier | None = None
    project_metadata: dict[str, Any] | None = None


class ChecklistUpdate(BaseModel):
    completed: bool
    notes: str = ""


class ApprovalRequest(BaseModel):
    approved: bool = True
    notes: str = ""


class EvidenceRequest(BaseModel):
    phases_included: list[str]
    format: EvidenceFormat


class ArtifactCreate(BaseModel):
    artifact_type: ArtifactType = ArtifactType.other
    filename: str
    mime_type: str = "application/octet-stream"
    description: str = ""
    content_base64: str = ""


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: str
    role: str


class ChecklistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    item_key: str
    title: str
    description: str
    framework_refs: list[dict[str, Any]]
    required: bool
    completed: bool
    completed_at: datetime | None
    notes: str


class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    artifact_type: ArtifactType
    filename: str
    file_size: int
    mime_type: str
    uploaded_at: datetime
    description: str
    sha256: str


class PhaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    phase_key: str
    name: str
    description: str
    status: PhaseStatus
    submitted_at: datetime | None
    approved_at: datetime | None
    approver_notes: str
    phase_data: dict[str, Any]
    checklist_items: list[ChecklistOut]
    artifacts: list[ArtifactOut]


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str
    system_type: SystemType
    risk_tier: RiskTier
    status: ProjectStatus
    current_phase_key: str
    created_at: datetime
    updated_at: datetime
    project_metadata: dict[str, Any]
    phases: list[PhaseOut] = []


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    generated_at: datetime
    phases_included: list[str]
    format: EvidenceFormat
    package_hash: str
    status: EvidenceStatus
    generation_log: str
