from __future__ import annotations

from typing import Any

from litestar import Request, Router, get, post
from litestar.exceptions import HTTPException

from backend import globalVar
from backend.modules.vertice360_orquestador_demo import services
from backend.modules.vertice360_orquestador_demo.schemas import (
    AdminResetPhoneRequest,
    ResetRuntimeAllRequest,
    ResetRuntimePhoneRequest,
    FollowupConfigSetRequest,
    FollowupEvaluateRequest,
    IngestMessageRequest,
    SupervisorSendRequest,
    VisitConfirmRequest,
    VisitProposeRequest,
    VisitRescheduleRequest,
)


def _map_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        detail = exc.args[0] if exc.args else "Not found"
        return HTTPException(status_code=404, detail=str(detail))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


def _validate_admin_token(request: Request, *, disabled_detail: str) -> None:
    expected = str(globalVar.V360_ADMIN_TOKEN or "").strip()
    provided = str(request.headers.get("x-v360-admin-token") or "").strip()
    if not expected:
        raise HTTPException(status_code=401, detail=disabled_detail)
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="invalid admin token")


def _validate_admin_reset_access(request: Request) -> None:
    if str(globalVar.RUN_ENV).lower() != "dev":
        raise HTTPException(
            status_code=403,
            detail="admin reset is only available in dev",
        )
    _validate_admin_token(request, disabled_detail="admin reset disabled")


def _validate_followup_config_access(request: Request) -> None:
    _validate_admin_token(request, disabled_detail="followup config access disabled")


def _validate_runtime_reset_access(request: Request) -> None:
    _validate_admin_token(request, disabled_detail="runtime reset disabled")


@get("/bootstrap")
async def bootstrap() -> dict[str, Any]:
    try:
        return services.bootstrap()
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@get("/dashboard")
async def dashboard(cliente: str | None = None) -> dict[str, Any]:
    try:
        return services.dashboard(cliente)
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@get("/knowledge/capabilities")
async def knowledge_capabilities(request: Request, force_refresh: bool = False) -> dict[str, Any]:
    try:
        _validate_admin_reset_access(request)
        return services.project_knowledge_capabilities(force_refresh=force_refresh)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@get("/knowledge/debug/project")
async def knowledge_debug_project(request: Request, code: str) -> dict[str, Any]:
    try:
        _validate_admin_reset_access(request)
        return services.project_knowledge_debug_project(code=code)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@get("/ticket/{ticket_id:str}")
async def ticket_detail(ticket_id: str) -> dict[str, Any]:
    try:
        return services.ticket_detail(ticket_id=ticket_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/ingest_message", status_code=200)
async def ingest_message(data: IngestMessageRequest) -> dict[str, Any]:
    try:
        return services.ingest_message(
            phone=data.phone,
            text=data.text,
            project_code=data.project_code,
            source=data.source,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/admin/reset_phone", status_code=200)
async def admin_reset_phone(request: Request, data: AdminResetPhoneRequest) -> dict[str, Any]:
    try:
        _validate_admin_reset_access(request)
        return services.admin_reset_phone(phone=data.phone)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/admin/reset_runtime_phone", status_code=200)
async def admin_reset_runtime_phone(request: Request, data: ResetRuntimePhoneRequest) -> dict[str, Any]:
    try:
        _validate_runtime_reset_access(request)
        return services.admin_reset_runtime_phone(phone=data.phone)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/admin/reset_runtime_all", status_code=200)
async def admin_reset_runtime_all(request: Request, data: ResetRuntimeAllRequest) -> dict[str, Any]:
    try:
        _validate_runtime_reset_access(request)
        return services.admin_reset_runtime_all(confirm=data.confirm)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/followup/config/set", status_code=200)
async def followup_config_set(request: Request, data: FollowupConfigSetRequest) -> dict[str, Any]:
    try:
        _validate_followup_config_access(request)
        return services.set_followup_config(
            cliente=data.cliente,
            enabled=data.enabled,
            advisor_phone=data.advisor_phone,
            supervisor_phone=data.supervisor_phone,
            first_delay_seconds=data.first_delay_seconds,
            second_delay_seconds=data.second_delay_seconds,
            level1_template=data.level1_template,
            level2_template=data.level2_template,
            updated_by=data.updated_by,
            board_base_url=data.board_base_url,
            allow_manual_evaluate=data.allow_manual_evaluate,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@get("/followup/config/get")
async def followup_config_get(request: Request, cliente: str) -> dict[str, Any]:
    try:
        _validate_followup_config_access(request)
        return services.get_followup_config(cliente=cliente)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/followup/evaluate", status_code=200)
async def followup_evaluate(request: Request, data: FollowupEvaluateRequest) -> dict[str, Any]:
    try:
        _validate_followup_config_access(request)
        return await services.evaluate_followup(
            cliente=data.cliente,
            ticket_id=data.ticket_id,
            force_now=data.force_now,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/visit/propose", status_code=200)
async def visit_propose(data: VisitProposeRequest) -> dict[str, Any]:
    try:
        return await services.propose_visit(
            ticket_id=data.ticket_id,
            advisor_name=data.advisor_name,
            option1=data.option1,
            option2=data.option2,
            option3=data.option3,
            message_out=data.message_out,
            mode=data.mode,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/visit/confirm", status_code=200)
async def visit_confirm(data: VisitConfirmRequest) -> dict[str, Any]:
    try:
        return services.confirm_visit(
            proposal_id=data.proposal_id,
            confirmed_option=data.confirmed_option,
            confirmed_by=data.confirmed_by,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/visit/reschedule", status_code=200)
async def visit_reschedule(data: VisitRescheduleRequest) -> dict[str, Any]:
    try:
        return services.reschedule_visit(
            ticket_id=data.ticket_id,
            advisor_name=data.advisor_name,
            option1=data.option1,
            option2=data.option2,
            option3=data.option3,
            message_out=data.message_out,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@post("/supervisor/send", status_code=200)
async def supervisor_send(data: SupervisorSendRequest) -> dict[str, Any]:
    try:
        return await services.supervisor_send(
            ticket_id=data.ticket_id,
            lead_phone=data.lead_phone,
            target=data.target,
            text=data.text,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


router = Router(
    path="/api/demo/vertice360-orquestador",
    route_handlers=[
        bootstrap,
        dashboard,
        knowledge_capabilities,
        knowledge_debug_project,
        ticket_detail,
        ingest_message,
        admin_reset_phone,
        admin_reset_runtime_phone,
        admin_reset_runtime_all,
        followup_config_set,
        followup_config_get,
        followup_evaluate,
        visit_propose,
        visit_confirm,
        visit_reschedule,
        supervisor_send,
    ],
)
