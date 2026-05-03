import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Role(str, enum.Enum):
    viewer = "viewer"
    reviewer = "reviewer"
    approver = "approver"
    admin = "admin"


class SystemType(str, enum.Enum):
    llm_chatbot = "llm_chatbot"
    rag_system = "rag_system"
    agentic = "agentic"
    multi_agent = "multi_agent"
    ml_classifier = "ml_classifier"
    other = "other"


class RiskTier(str, enum.Enum):
    tier_1 = "1"
    tier_2 = "2"
    tier_3 = "3"


class ProjectStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    retired = "retired"
    archived = "archived"


class PhaseStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    pending_approval = "pending_approval"
    approved = "approved"
    skipped = "skipped"


class ArtifactType(str, enum.Enum):
    threat_model = "threat_model"
    test_report = "test_report"
    policy_document = "policy_document"
    architecture_diagram = "architecture_diagram"
    sbom = "sbom"
    red_team_report = "red_team_report"
    other = "other"


class EvidenceFormat(str, enum.Enum):
    pdf = "pdf"
    json = "json"
    yaml = "yaml"
    csv = "csv"


class EvidenceStatus(str, enum.Enum):
    generating = "generating"
    ready = "ready"
    failed = "failed"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    users: Mapped[list["User"]] = relationship(back_populates="org")
    projects: Mapped[list["AIProject"]] = relationship(back_populates="org")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.viewer)
    keycloak_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    org: Mapped[Organization] = relationship(back_populates="users")


class AIProject(Base):
    __tablename__ = "ai_projects"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    system_type: Mapped[SystemType] = mapped_column(Enum(SystemType))
    risk_tier: Mapped[RiskTier] = mapped_column(Enum(RiskTier))
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.active)
    current_phase_key: Mapped[str] = mapped_column(String(40), default="01_requirements")
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    project_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    org: Mapped[Organization] = relationship(back_populates="projects")
    phases: Mapped[list["Phase"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    evidence_packages: Mapped[list["EvidencePackage"]] = relationship(back_populates="project")


class Phase(Base):
    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_projects.id"), index=True)
    phase_key: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[PhaseStatus] = mapped_column(Enum(PhaseStatus), default=PhaseStatus.not_started)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approver_notes: Mapped[str] = mapped_column(Text, default="")
    phase_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    project: Mapped[AIProject] = relationship(back_populates="phases")
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(back_populates="phase", cascade="all, delete-orphan")
    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="phase", cascade="all, delete-orphan")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    phase_id: Mapped[int] = mapped_column(ForeignKey("phases.id"), index=True)
    item_key: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    framework_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    phase: Mapped[Phase] = relationship(back_populates="checklist_items")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = uuid_pk()
    phase_id: Mapped[int] = mapped_column(ForeignKey("phases.id"), index=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType))
    filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(160))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    description: Mapped[str] = mapped_column(Text, default="")
    framework_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    sha256: Mapped[str] = mapped_column(String(64))

    phase: Mapped[Phase] = relationship(back_populates="artifacts")


class EvidencePackage(Base):
    __tablename__ = "evidence_packages"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_projects.id"), index=True)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    phases_included: Mapped[list[str]] = mapped_column(JSONB, default=list)
    format: Mapped[EvidenceFormat] = mapped_column(Enum(EvidenceFormat))
    storage_key: Mapped[str] = mapped_column(String(512), default="")
    package_hash: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[EvidenceStatus] = mapped_column(Enum(EvidenceStatus), default=EvidenceStatus.generating)
    generation_log: Mapped[str] = mapped_column(Text, default="")

    project: Mapped[AIProject] = relationship(back_populates="evidence_packages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(120))
    entity_id: Mapped[str] = mapped_column(String(120))
    before_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    after_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str] = mapped_column(String(80), default="")
    user_agent: Mapped[str] = mapped_column(String(255), default="")


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1024))
    secret_hash: Mapped[str] = mapped_column(String(128))
    events: Mapped[list[str]] = mapped_column(JSONB, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FrameworkMapping(Base):
    __tablename__ = "framework_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phase_key: Mapped[str] = mapped_column(String(40), index=True)
    framework: Mapped[str] = mapped_column(String(80), index=True)
    reference_id: Mapped[str] = mapped_column(String(80), index=True)
    reference_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    control_type: Mapped[str] = mapped_column(String(20), default="control")
