import base64
import csv
import hashlib
import io
import json
from datetime import datetime
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from minio import Minio
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.db import Base, engine, get_db
from app.models import (
    AIProject,
    Artifact,
    AuditLog,
    ChecklistItem,
    EvidenceFormat,
    EvidencePackage,
    EvidenceStatus,
    Organization,
    Phase,
    PhaseStatus,
    ProjectStatus,
    Role,
    User,
    Webhook,
)
from app.schemas import (
    ApprovalRequest,
    ArtifactCreate,
    ArtifactOut,
    ChecklistOut,
    ChecklistUpdate,
    EvidenceOut,
    EvidenceRequest,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)
from app.seed import PHASES, parse_refs, seed_frameworks

settings = get_settings()
app = FastAPI(title="AI-SGP API", version="0.1.0", openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl,
    )


def seed_demo(db: Session) -> None:
    seed_frameworks(db)
    org = db.query(Organization).filter_by(slug="demo").first()
    if not org:
        org = Organization(name="Demo Financial Services", slug="demo", settings={"tiering": "1/2/3"})
        db.add(org)
        db.flush()
    user = db.query(User).filter_by(email="admin@demo.ai-sgp.local").first()
    if not user:
        user = User(org_id=org.id, email="admin@demo.ai-sgp.local", full_name="Demo Admin", role=Role.admin)
        db.add(user)
        db.flush()
    project = db.query(AIProject).filter_by(org_id=org.id, name="Customer Support RAG Copilot").first()
    if project:
        db.commit()
        return
    project = AIProject(
        org_id=org.id,
        name="Customer Support RAG Copilot",
        description="Demo RAG system with agentic retrieval and human escalation.",
        system_type="rag_system",
        risk_tier="tier_2",
        current_phase_key="01_requirements",
        created_by=user.id,
    )
    db.add(project)
    db.flush()
    for phase_def in PHASES:
        status = PhaseStatus.in_progress if phase_def["key"] == "01_requirements" else PhaseStatus.not_started
        phase = Phase(
            project_id=project.id,
            phase_key=phase_def["key"],
            name=phase_def["name"],
            description=phase_def["description"],
            status=status,
            started_at=datetime.utcnow() if status == PhaseStatus.in_progress else None,
            phase_data={"required_artifacts": phase_def["artifacts"]},
        )
        db.add(phase)
        db.flush()
        for key, title, refs in phase_def["items"]:
            db.add(
                ChecklistItem(
                    phase_id=phase.id,
                    item_key=key,
                    title=title,
                    description=title,
                    framework_refs=parse_refs(refs),
                )
            )
    db.add(AuditLog(org_id=org.id, user_id=user.id, action="project.created", entity_type="AIProject", entity_id=str(project.id), after_state={"name": project.name}))
    db.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed_demo(db)
    try:
        client = minio_client()
        for bucket in [settings.minio_bucket_artifacts, settings.minio_bucket_evidence]:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
    except Exception:
        pass


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    if settings.auth_disabled:
        user = db.query(User).filter_by(email="admin@demo.ai-sgp.local").first()
        if not user:
            raise HTTPException(status_code=401, detail="Demo user not seeded")
        return user
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = auth_header.split(" ", 1)[1]
    jwks_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
    try:
        signing_key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            options={"verify_aud": False},
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    email = claims.get("email") or claims.get("preferred_username")
    if not email:
        raise HTTPException(status_code=401, detail="Token missing email")
    org = db.query(Organization).filter_by(slug="demo").first()
    if not org:
        raise HTTPException(status_code=401, detail="Organization not found")
    roles = claims.get("realm_access", {}).get("roles", [])
    role = Role.admin if "admin" in roles else Role.approver if "approver" in roles else Role.reviewer if "reviewer" in roles else Role.viewer
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(org_id=org.id, email=email, full_name=claims.get("name", email), role=role, keycloak_sub=claims.get("sub"))
        db.add(user)
        db.commit()
    return user


def audit(db: Session, user: User, action: str, entity: str, entity_id: str, after: dict[str, Any]) -> None:
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action=action, entity_type=entity, entity_id=entity_id, after_state=after))


def project_query(db: Session, user: User):
    return db.query(AIProject).filter(AIProject.org_id == user.org_id)


def get_project_or_404(project_id: UUID, db: Session, user: User) -> AIProject:
    project = (
        project_query(db, user)
        .options(selectinload(AIProject.phases).selectinload(Phase.checklist_items), selectinload(AIProject.phases).selectinload(Phase.artifacts))
        .filter(AIProject.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.phases.sort(key=lambda p: p.phase_key)
    return project


def get_phase(project: AIProject, phase_key: str) -> Phase:
    for phase in project.phases:
        if phase.phase_key == phase_key:
            return phase
    raise HTTPException(status_code=404, detail="Phase not found")


def build_evidence(project: AIProject, phases: list[str]) -> dict[str, Any]:
    selected = [phase for phase in project.phases if phase.phase_key in phases]
    framework_total: dict[str, int] = {}
    framework_done: dict[str, int] = {}
    for phase in selected:
        for item in phase.checklist_items:
            for ref in item.framework_refs:
                key = f"{ref['framework']}:{ref['id']}"
                framework_total[key] = framework_total.get(key, 0) + 1
                if item.completed:
                    framework_done[key] = framework_done.get(key, 0) + 1
    return {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "system_type": project.system_type.value,
            "risk_tier": project.risk_tier.value,
            "status": project.status.value,
        },
        "generated_at": datetime.utcnow().isoformat(),
        "phases": [
            {
                "phase_key": phase.phase_key,
                "name": phase.name,
                "status": phase.status.value,
                "approved_at": phase.approved_at.isoformat() if phase.approved_at else None,
                "approver_notes": phase.approver_notes,
                "checklist": [
                    {
                        "title": item.title,
                        "framework_refs": item.framework_refs,
                        "completed": item.completed,
                        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                    }
                    for item in phase.checklist_items
                ],
                "artifacts": [
                    {"filename": artifact.filename, "type": artifact.artifact_type.value, "sha256": artifact.sha256}
                    for artifact in phase.artifacts
                ],
            }
            for phase in selected
        ],
        "framework_coverage": {
            key: {"addressed": framework_done.get(key, 0), "total": count}
            for key, count in sorted(framework_total.items())
        },
    }


def evidence_bytes(payload: dict[str, Any], fmt: EvidenceFormat) -> tuple[bytes, str]:
    if fmt == EvidenceFormat.json:
        return json.dumps(payload, indent=2).encode(), "application/json"
    if fmt == EvidenceFormat.csv:
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["phase", "item", "completed", "framework_refs"])
        for phase in payload["phases"]:
            for item in phase["checklist"]:
                writer.writerow([phase["phase_key"], item["title"], item["completed"], json.dumps(item["framework_refs"])])
        return stream.getvalue().encode(), "text/csv"
    if fmt == EvidenceFormat.yaml:
        return json.dumps(payload, indent=2).encode(), "application/yaml"
    html = f"""
    <html><body>
      <h1>AI-SGP Evidence Package</h1>
      <h2>{payload['project']['name']}</h2>
      <p>Generated: {payload['generated_at']}</p>
      <p>System type: {payload['project']['system_type']} | Risk tier: {payload['project']['risk_tier']}</p>
      {''.join(f"<h2>{p['name']}</h2><p>Status: {p['status']}</p><ul>{''.join(f'<li>{i['title']}: {i['completed']}</li>' for i in p['checklist'])}</ul>" for p in payload['phases'])}
      <h2>Framework Coverage Appendix</h2>
      <pre>{json.dumps(payload['framework_coverage'], indent=2)}</pre>
    </body></html>
    """
    try:
        from weasyprint import HTML

        return HTML(string=html).write_pdf(), "application/pdf"
    except Exception:
        return html.encode(), "text/html"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("select 1"))
    return {"database": "ok", "api": "ok"}


@app.get("/api/v1/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return project_query(db, user).options(selectinload(AIProject.phases)).order_by(AIProject.created_at.desc()).all()


@app.post("/api/v1/projects", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    project = AIProject(org_id=user.org_id, name=payload.name, description=payload.description, system_type=payload.system_type, risk_tier=payload.risk_tier, created_by=user.id)
    db.add(project)
    db.flush()
    for phase_def in PHASES:
        status = PhaseStatus.in_progress if phase_def["key"] == "01_requirements" else PhaseStatus.not_started
        phase = Phase(project_id=project.id, phase_key=phase_def["key"], name=phase_def["name"], description=phase_def["description"], status=status, phase_data={"required_artifacts": phase_def["artifacts"]})
        db.add(phase)
        db.flush()
        for key, title, refs in phase_def["items"]:
            db.add(ChecklistItem(phase_id=phase.id, item_key=key, title=title, description=title, framework_refs=parse_refs(refs)))
    audit(db, user, "project.created", "AIProject", str(project.id), {"name": project.name})
    db.commit()
    return get_project_or_404(project.id, db, user)


@app.get("/api/v1/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return get_project_or_404(project_id, db, user)


@app.put("/api/v1/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: UUID, payload: ProjectUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    project = get_project_or_404(project_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    project.updated_at = datetime.utcnow()
    audit(db, user, "project.updated", "AIProject", str(project.id), payload.model_dump(exclude_unset=True))
    db.commit()
    return get_project_or_404(project.id, db, user)


@app.get("/api/v1/projects/{project_id}/status")
def project_status(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    project = get_project_or_404(project_id, db, user)
    return {
        "project_id": str(project.id),
        "current_phase": project.current_phase_key,
        "phases": [
            {
                "phase_key": phase.phase_key,
                "status": phase.status.value,
                "completed": sum(1 for item in phase.checklist_items if item.completed),
                "total": len(phase.checklist_items),
                "artifacts": len(phase.artifacts),
            }
            for phase in project.phases
        ],
    }


@app.get("/api/v1/projects/{project_id}/phases/{phase_key}/checklist", response_model=list[ChecklistOut])
def get_checklist(project_id: UUID, phase_key: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return get_phase(get_project_or_404(project_id, db, user), phase_key).checklist_items


@app.put("/api/v1/projects/{project_id}/phases/{phase_key}/checklist/{item_id}", response_model=ChecklistOut)
def update_checklist(project_id: UUID, phase_key: str, item_id: UUID, payload: ChecklistUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    phase = get_phase(get_project_or_404(project_id, db, user), phase_key)
    item = next((i for i in phase.checklist_items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    item.completed = payload.completed
    item.notes = payload.notes
    item.completed_by = user.id if payload.completed else None
    item.completed_at = datetime.utcnow() if payload.completed else None
    if phase.status == PhaseStatus.not_started:
        phase.status = PhaseStatus.in_progress
        phase.started_at = datetime.utcnow()
    audit(db, user, "checklist.updated", "ChecklistItem", str(item.id), {"completed": item.completed})
    db.commit()
    return item


@app.post("/api/v1/projects/{project_id}/phases/{phase_key}/submit")
def submit_phase(project_id: UUID, phase_key: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    phase = get_phase(get_project_or_404(project_id, db, user), phase_key)
    missing = [item.title for item in phase.checklist_items if item.required and not item.completed]
    required_artifacts = set(phase.phase_data.get("required_artifacts", []))
    uploaded_types = {artifact.artifact_type.value for artifact in phase.artifacts}
    missing_artifacts = sorted(required_artifacts - uploaded_types)
    if missing or missing_artifacts:
        raise HTTPException(status_code=409, detail={"missing_checklist": missing, "missing_artifacts": missing_artifacts})
    phase.status = PhaseStatus.pending_approval
    phase.submitted_at = datetime.utcnow()
    audit(db, user, "phase.submitted", "Phase", str(phase.id), {"phase_key": phase.phase_key})
    db.commit()
    return {"status": phase.status.value}


@app.post("/api/v1/projects/{project_id}/phases/{phase_key}/approve")
def approve_phase(project_id: UUID, phase_key: str, payload: ApprovalRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    project = get_project_or_404(project_id, db, user)
    phase = get_phase(project, phase_key)
    phase.approver_notes = payload.notes
    if payload.approved:
        phase.status = PhaseStatus.approved
        phase.approved_at = datetime.utcnow()
        phase.approved_by = user.id
        keys = [p["key"] for p in PHASES]
        next_index = keys.index(phase.phase_key) + 1
        if next_index < len(keys):
            project.current_phase_key = keys[next_index]
            next_phase = get_phase(project, keys[next_index])
            if next_phase.status == PhaseStatus.not_started:
                next_phase.status = PhaseStatus.in_progress
                next_phase.started_at = datetime.utcnow()
    else:
        phase.status = PhaseStatus.in_progress
    audit(db, user, "phase.approved" if payload.approved else "phase.rejected", "Phase", str(phase.id), {"approved": payload.approved})
    db.commit()
    return {"status": phase.status.value, "current_phase": project.current_phase_key}


async def store_artifact_bytes(project_id: UUID, phase_key: str, filename: str, data: bytes) -> str:
    key = f"{project_id}/{phase_key}/{hashlib.sha256(data).hexdigest()}-{filename}"
    try:
        client = minio_client()
        client.put_object(settings.minio_bucket_artifacts, key, io.BytesIO(data), len(data))
    except Exception:
        pass
    return key


@app.post("/api/v1/projects/{project_id}/phases/{phase_key}/artifacts", response_model=ArtifactOut)
async def upload_artifact(project_id: UUID, phase_key: str, artifact_type: str = Form("other"), description: str = Form(""), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Artifact exceeds 50MB")
    phase = get_phase(get_project_or_404(project_id, db, user), phase_key)
    digest = hashlib.sha256(data).hexdigest()
    artifact = Artifact(phase_id=phase.id, artifact_type=artifact_type, filename=file.filename or "artifact.bin", storage_key=await store_artifact_bytes(project_id, phase_key, file.filename or "artifact.bin", data), file_size=len(data), mime_type=file.content_type or "application/octet-stream", uploaded_by=user.id, description=description, sha256=digest)
    db.add(artifact)
    audit(db, user, "artifact.uploaded", "Artifact", str(artifact.id), {"filename": artifact.filename})
    db.commit()
    return artifact


@app.post("/api/v1/projects/{project_id}/phases/{phase_key}/artifacts/json", response_model=ArtifactOut)
async def upload_artifact_json(project_id: UUID, phase_key: str, payload: ArtifactCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    data = base64.b64decode(payload.content_base64 or "")
    phase = get_phase(get_project_or_404(project_id, db, user), phase_key)
    digest = hashlib.sha256(data).hexdigest()
    artifact = Artifact(phase_id=phase.id, artifact_type=payload.artifact_type, filename=payload.filename, storage_key=await store_artifact_bytes(project_id, phase_key, payload.filename, data), file_size=len(data), mime_type=payload.mime_type, uploaded_by=user.id, description=payload.description, sha256=digest)
    db.add(artifact)
    audit(db, user, "artifact.uploaded", "Artifact", str(artifact.id), {"filename": artifact.filename})
    db.commit()
    return artifact


@app.get("/api/v1/projects/{project_id}/phases/{phase_key}/artifacts", response_model=list[ArtifactOut])
def list_artifacts(project_id: UUID, phase_key: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return get_phase(get_project_or_404(project_id, db, user), phase_key).artifacts


@app.delete("/api/v1/artifacts/{artifact_id}")
def delete_artifact(artifact_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    db.delete(artifact)
    audit(db, user, "artifact.deleted", "Artifact", str(artifact_id), {})
    db.commit()
    return {"deleted": str(artifact_id)}


@app.post("/api/v1/projects/{project_id}/evidence", response_model=EvidenceOut)
def generate_evidence(project_id: UUID, payload: EvidenceRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    project = get_project_or_404(project_id, db, user)
    evidence_payload = build_evidence(project, payload.phases_included)
    content, _ = evidence_bytes(evidence_payload, payload.format)
    digest = hashlib.sha256(content).hexdigest()
    package = EvidencePackage(project_id=project.id, generated_by=user.id, phases_included=payload.phases_included, format=payload.format, storage_key=f"evidence/{project.id}/{digest}.{payload.format.value}", package_hash=digest, status=EvidenceStatus.ready, generation_log="Generated synchronously for MVP; Celery worker can run the same builder.")
    db.add(package)
    audit(db, user, "evidence.ready", "EvidencePackage", str(package.id), {"format": payload.format.value, "hash": digest})
    db.commit()
    return package


@app.get("/api/v1/projects/{project_id}/evidence", response_model=list[EvidenceOut])
def list_evidence(project_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    project = get_project_or_404(project_id, db, user)
    return project.evidence_packages


@app.get("/api/v1/evidence/{package_id}/status", response_model=EvidenceOut)
def evidence_status(package_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    package = db.query(EvidencePackage).filter(EvidencePackage.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Evidence package not found")
    return package


@app.get("/api/v1/evidence/{package_id}/download")
def download_evidence(package_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    package = db.query(EvidencePackage).filter(EvidencePackage.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Evidence package not found")
    project = get_project_or_404(package.project_id, db, user)
    content, media_type = evidence_bytes(build_evidence(project, package.phases_included), package.format)
    return Response(content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename=ai-sgp-evidence-{package.id}.{package.format.value}"})


@app.get("/api/v1/frameworks")
def frameworks(db: Session = Depends(get_db)):
    from app.models import FrameworkMapping

    return db.query(FrameworkMapping).order_by(FrameworkMapping.framework, FrameworkMapping.reference_id).all()


@app.get("/api/v1/frameworks/{framework}")
def framework(framework: str, db: Session = Depends(get_db)):
    from app.models import FrameworkMapping

    return db.query(FrameworkMapping).filter(FrameworkMapping.framework.ilike(framework.replace("_", " "))).all()


@app.get("/api/v1/frameworks/phase/{phase_key}")
def phase_frameworks(phase_key: str, db: Session = Depends(get_db)):
    from app.models import FrameworkMapping

    return db.query(FrameworkMapping).filter(FrameworkMapping.phase_key == phase_key).all()


@app.get("/api/v1/admin/users")
def users(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(User).filter(User.org_id == user.org_id).all()


@app.get("/api/v1/admin/audit-log")
def audit_log(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(AuditLog).filter(AuditLog.org_id == user.org_id).order_by(AuditLog.timestamp.desc()).limit(200).all()


@app.post("/api/v1/admin/webhooks")
async def create_webhook(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    payload = await request.json()
    secret_hash = hashlib.sha256(payload.get("secret", "").encode()).hexdigest()
    hook = Webhook(org_id=user.org_id, name=payload["name"], url=payload["url"], secret_hash=secret_hash, events=payload.get("events", []), active=True)
    db.add(hook)
    db.commit()
    return hook


@app.get("/api/v1/admin/webhooks")
def webhooks(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(Webhook).filter(Webhook.org_id == user.org_id).all()
