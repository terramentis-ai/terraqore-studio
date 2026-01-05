"""Governance and compliance reporting endpoints."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Dict, Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from metaqore.api.dependencies import get_psmp_engine, get_secure_gateway, get_state_manager
from metaqore.api.routes.utils import build_response_metadata, paginate_items
from metaqore.api.schemas import (
    AuditEventRecord,
    AuditTrailData,
    AuditTrailResponse,
    BlockingReportResponse,
    ConflictListData,
    ConflictListResponse,
    ConflictResolutionRequest,
    ConflictResponse,
    ComplianceReportData,
    ComplianceReportResponse,
)
from metaqore.core.psmp import PSMPEngine
from metaqore.core.models import ConflictSeverity, ResolutionStrategy
from metaqore.core.security import SecureGateway
from metaqore.core.state_manager import StateManager

router = APIRouter(prefix="/governance", tags=["Governance"])


@router.get(
    "/conflicts",
    response_model=ConflictListResponse,
    summary="List conflicts for a project",
)
async def list_conflicts(
    request: Request,
    project_id: str = Query(..., description="Project identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=200, description="Items per page"),
    severity: ConflictSeverity | None = Query(None, description="Filter by severity level"),
    resolved: bool | None = Query(None, description="Filter by resolution state"),
    conflict_type: str | None = Query(None, description="Filter by conflict type"),
    state_manager: StateManager = Depends(get_state_manager),
) -> ConflictListResponse:
    project = state_manager.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    conflicts = state_manager.list_conflicts(project_id)
    if severity is not None:
        conflicts = [conflict for conflict in conflicts if conflict.severity == severity]
    if resolved is not None:
        conflicts = [conflict for conflict in conflicts if conflict.resolved is resolved]
    if conflict_type:
        conflicts = [conflict for conflict in conflicts if conflict.conflict_type == conflict_type]

    paged_conflicts, total = paginate_items(conflicts, page, page_size)
    filters: Dict[str, Any] = {}
    if severity is not None:
        filters["severity"] = severity.value
    if resolved is not None:
        filters["resolved"] = resolved
    if conflict_type:
        filters["conflict_type"] = conflict_type

    data = ConflictListData(
        project_id=project_id,
        conflicts=paged_conflicts,
        total=total,
        page=page,
        page_size=page_size,
        filters=filters,
    )
    return ConflictListResponse(data=data, metadata=build_response_metadata(request))


@router.post(
    "/conflicts/{conflict_id}/resolve",
    response_model=ConflictResponse,
    summary="Resolve a conflict using a chosen strategy",
)
async def resolve_conflict(
    conflict_id: str,
    payload: ConflictResolutionRequest,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
    psmp_engine: PSMPEngine = Depends(get_psmp_engine),
) -> ConflictResponse:
    conflict = state_manager.get_conflict(conflict_id)
    if conflict is None:
        raise HTTPException(status_code=404, detail="Conflict not found")

    resolved = psmp_engine.resolve_conflict(conflict, payload.strategy or conflict.resolution_strategy)
    return ConflictResponse(data=resolved, metadata=build_response_metadata(request))


@router.get(
    "/blocking-report",
    response_model=BlockingReportResponse,
    summary="Retrieve PSMP blocking report for a project",
)
async def get_blocking_report(
    request: Request,
    project_id: str = Query(..., description="Project identifier"),
    state_manager: StateManager = Depends(get_state_manager),
    psmp_engine: PSMPEngine = Depends(get_psmp_engine),
) -> BlockingReportResponse:
    project = state_manager.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    report = psmp_engine.get_blocking_report(project_id)
    return BlockingReportResponse(data=report, metadata=build_response_metadata(request))


@router.get(
    "/compliance/export",
    response_model=ComplianceReportResponse,
    summary="Export compliance audit snapshot (JSON or CSV)",
    responses={
        200: {
            "content": {
                "application/json": {},
                "text/csv": {
                    "example": "timestamp,event_type,organization,payload\n2026-01-04T00:00:00Z,routing_decision,default,{'provider':'ollama'}",
                },
            }
        }
    },
)
async def export_compliance_report(
    request: Request,
    export_format: str = Query(
        "json",
        alias="format",
        pattern="^(json|csv)$",
        description="Export format",
    ),
    organization: str | None = Query(None, description="Organization to report"),
    secure_gateway: SecureGateway = Depends(get_secure_gateway),
) -> ComplianceReportResponse | PlainTextResponse:
    auditor = secure_gateway.auditor
    resolved_org = organization or auditor.organization
    events = auditor.get_audit_trail({"organization": resolved_org})
    report = auditor.get_compliance_report(resolved_org)
    metadata = build_response_metadata(request)

    if export_format.lower() == "csv":
        csv_payload = _serialize_events_to_csv(events)
        filename = f"compliance_{resolved_org}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
        response = PlainTextResponse(csv_payload, media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        response.headers["X-Request-ID"] = metadata.request_id
        return response

    data = ComplianceReportData(
        organization=resolved_org,
        format="json",
        report=report,
        events=[AuditEventRecord(**event) for event in events],
    )
    return ComplianceReportResponse(data=data, metadata=metadata)


@router.get(
    "/compliance/audit",
    response_model=AuditTrailResponse,
    summary="Retrieve compliance audit events",
)
async def get_compliance_audit_trail(
    request: Request,
    organization: str | None = Query(None, description="Organization to filter"),
    event_type: str | None = Query(None, description="Filter by event type"),
    provider: str | None = Query(None, description="Filter by provider"),
    agent_name: str | None = Query(None, description="Filter by agent name"),
    task_type: str | None = Query(None, description="Filter by task type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    secure_gateway: SecureGateway = Depends(get_secure_gateway),
) -> AuditTrailResponse:
    auditor = secure_gateway.auditor
    resolved_org = organization or auditor.organization

    filters: Dict[str, Any] = {"organization": resolved_org}
    filter_summary: Dict[str, Any] = {}

    if event_type:
        filters["event_type"] = event_type
        filter_summary["event_type"] = event_type
    if provider:
        filters["provider"] = provider
        filter_summary["provider"] = provider
    if agent_name:
        filters["agent_name"] = agent_name
        filter_summary["agent_name"] = agent_name
    if task_type:
        filters["task_type"] = task_type
        filter_summary["task_type"] = task_type

    events = auditor.get_audit_trail(filters)
    paged_events, total = paginate_items(events, page, page_size)
    records = [AuditEventRecord(**event) for event in paged_events]

    data = AuditTrailData(
        organization=resolved_org,
        events=records,
        total=total,
        page=page,
        page_size=page_size,
        filters=filter_summary,
    )
    return AuditTrailResponse(data=data, metadata=build_response_metadata(request))


def _serialize_events_to_csv(events: Iterable[Dict[str, object]]) -> str:
    """Convert audit events into a CSV payload."""

    output = StringIO()
    fieldnames = ["timestamp", "event_type", "organization", "payload"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for event in events:
        payload = event.get("payload")
        writer.writerow(
            {
                "timestamp": event.get("timestamp", ""),
                "event_type": event.get("event_type", ""),
                "organization": event.get("organization", ""),
                "payload": payload if isinstance(payload, str) else str(payload or {}),
            }
        )
    return output.getvalue()


__all__ = ["router"]
