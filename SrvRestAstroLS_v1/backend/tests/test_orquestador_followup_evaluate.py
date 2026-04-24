from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import uuid

import pytest

from backend import globalVar
from backend.modules.vertice360_orquestador_demo import db, repo, services


def _db_ready() -> bool:
    return services.demo_db_ready()


pytestmark = pytest.mark.skipif(
    not _db_ready(),
    reason="Requires DB_PG_V360_URL + psycopg connectivity to v360",
)


def _headers(monkeypatch, *, env: str = "prod", token: str = "followup-eval-token") -> dict[str, str]:
    monkeypatch.setenv("VERTICE360_ENV", env)
    monkeypatch.setenv("V360_ADMIN_TOKEN", token)
    monkeypatch.setattr(globalVar, "ENVIRONMENT", env, raising=False)
    monkeypatch.setattr(globalVar, "RUN_ENV", env, raising=False)
    monkeypatch.setattr(globalVar, "V360_ADMIN_TOKEN", token, raising=False)
    return {"x-v360-admin-token": token}


def _wire_gupshup(monkeypatch, calls: list[dict]) -> None:
    monkeypatch.setattr(services.globalVar, "GUPSHUP_APP_NAME", "test-app", raising=False)
    monkeypatch.setattr(services.globalVar, "GUPSHUP_API_KEY", "test-key", raising=False)
    monkeypatch.setattr(services.globalVar, "GUPSHUP_WA_SENDER", "+5491100000000", raising=False)
    monkeypatch.setattr(
        services.globalVar,
        "get_gupshup_wa_sender_provider_value",
        lambda: "5491100000000",
        raising=False,
    )

    async def fake_gupshup_send_text(to: str, text: str):
        calls.append({"to": to, "text": text})
        return SimpleNamespace(provider_message_id=f"gs-{len(calls)}", raw={"id": f"gs-{len(calls)}"})

    monkeypatch.setattr(services, "gupshup_send_text", fake_gupshup_send_text)


def _unique_phone() -> str:
    tail = str(uuid.uuid4().int)[-10:]
    return f"+54911{tail}"


def _unique_cliente() -> str:
    return f"followup-eval-{uuid.uuid4().hex[:10]}"


def _cleanup_phone(phone_e164: str) -> None:
    def _tx(conn):
        repo.reset_by_phone(conn, phone_e164)

    db.run_in_transaction(_tx)


def _cleanup_config(cliente: str) -> None:
    def _tx(conn):
        repo.ensure_visit_followup_config_schema(conn)
        conn.execute("delete from visit_followup_config where cliente = %s", (cliente,))

    db.run_in_transaction(_tx)


def _seed_followup_config(cliente: str, *, first_delay: int = 10, second_delay: int = 15) -> None:
    services.set_followup_config(
        cliente=cliente,
        enabled=True,
        advisor_phone="+5491111111111",
        supervisor_phone="+5491222222222",
        first_delay_seconds=first_delay,
        second_delay_seconds=second_delay,
        updated_by="tests",
        allow_manual_evaluate=True,
    )


def _ensure_pending_visit(payload: dict) -> None:
    ticket_id = str(payload["ticket_id"])

    def _tx(conn):
        detail = repo.get_ticket_detail(conn, ticket_id)
        if detail is None:
            raise AssertionError("ticket not found while ensuring pending visit")
        stage = str(detail.get("stage") or "")
        if stage != services.STAGE_PENDING_VISIT:
            repo.update_ticket_activity(conn, ticket_id, stage=services.STAGE_PENDING_VISIT)
            repo.insert_event(
                conn,
                correlation_id=ticket_id,
                domain=services.DOMAIN,
                name="orq.visit.requested",
                actor="client",
                payload={"ticket_id": ticket_id, "text": "quiero coordinar visita"},
            )

    db.run_in_transaction(_tx)


def _seed_pending_visit_ticket(client, phone: str, *, lead_name: str | None = None) -> dict:
    first = client.post(
        "/api/demo/vertice360-orquestador/ingest_message",
        json={"phone": phone, "text": "Hola"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/demo/vertice360-orquestador/ingest_message",
        json={"phone": phone, "text": "Quiero coordinar visita"},
    )
    assert second.status_code == 200
    payload = second.json()
    _ensure_pending_visit(payload)
    if lead_name:
        _set_lead_name(str(payload["lead_id"]), lead_name)
    return payload


def _set_lead_name(lead_id: str, lead_name: str) -> None:
    def _tx(conn):
        conn.execute("update leads set name = %s, updated_at = now() where id = %s", (lead_name, lead_id))

    db.run_in_transaction(_tx)


def _latest_cycle(ticket_id: str) -> dict | None:
    def _tx(conn):
        repo.ensure_visit_followup_cycle_schema(conn)
        return repo.fetch_one(
            conn,
            """
            select cycle_id, ticket_id, cliente, status, started_at, last_human_action_at,
                   level1_sent_at, level2_sent_at, cancel_reason, closed_at,
                   project_code, lead_phone, advisor_phone, supervisor_phone,
                   last_evaluated_at, last_stage_seen, created_at, updated_at
            from visit_followup_cycle
            where ticket_id = %s
            order by created_at desc
            limit 1
            """,
            (ticket_id,),
        )

    return db.run_in_transaction(_tx)


def _set_cycle_fields(cycle_id: str, **changes) -> None:
    def _tx(conn):
        repo.update_followup_cycle(conn, cycle_id, **changes)

    db.run_in_transaction(_tx)


def _lead_message_count(lead_id: str) -> int:
    def _tx(conn):
        row = conn.execute("select count(*) from messages where lead_id = %s", (lead_id,)).fetchone()
        return int(row[0])

    return db.run_in_transaction(_tx)


def _insert_human_outbound_message(*, conversation_id: str, lead_id: str, text: str, created_at: datetime) -> None:
    def _tx(conn):
        message = repo.insert_message(
            conn,
            conversation_id=conversation_id,
            lead_id=lead_id,
            direction="out",
            actor="advisor",
            text=text,
            provider_meta={"manual": True},
        )
        conn.execute("update messages set created_at = %s where id = %s", (created_at, str(message["id"])))

    db.run_in_transaction(_tx)


def _set_ticket_stage(ticket_id: str, stage: str) -> None:
    def _tx(conn):
        repo.update_ticket_activity(conn, ticket_id, stage=stage)

    db.run_in_transaction(_tx)


def test_followup_evaluate_creates_cycle_for_pending_ticket(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        messages_before = _lead_message_count(str(payload["lead_id"]))

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"]), "force_now": True},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["evaluated_count"] == 1
        assert data["actions"][0]["action"] == "created_cycle"
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        assert cycle["status"] == "active"
        assert cycle["level1_sent_at"] is None
        assert _lead_message_count(str(payload["lead_id"])) == messages_before
        assert calls == []
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_sends_level1_when_delay_elapsed(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        _set_cycle_fields(str(cycle["cycle_id"]), started_at=now - timedelta(seconds=11), last_evaluated_at=now - timedelta(seconds=11))
        messages_before = _lead_message_count(str(payload["lead_id"]))

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions"][0]["action"] == "sent_level1"
        assert data["actions"][0]["send_ok"] is True
        assert data["actions"][0]["provider_status"] == "submitted"
        assert data["actions"][0]["status_after"] == "level1_sent"
        assert data["actions"][0]["target_phone"] == "+5491111111111"
        assert data["actions"][0]["target_matches_lead"] is False
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle["status"] == "level1_sent"
        assert cycle["level1_sent_at"] is not None
        assert _lead_message_count(str(payload["lead_id"])) == messages_before
        assert len(calls) == 1
        assert calls[0]["to"] == "+5491111111111"
        assert "Podés seguir en el panel:" in calls[0]["text"]
        assert f"cliente={phone.lstrip('+')}" in calls[0]["text"]
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_sends_level2_after_level1_elapsed(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        _set_cycle_fields(
            str(cycle["cycle_id"]),
            status="level1_sent",
            started_at=now - timedelta(seconds=30),
            level1_sent_at=now - timedelta(seconds=16),
            last_evaluated_at=now - timedelta(seconds=16),
        )

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions"][0]["action"] == "sent_level2"
        assert data["actions"][0]["send_ok"] is True
        assert data["actions"][0]["provider_status"] == "submitted"
        assert data["actions"][0]["status_after"] == "level2_sent"
        assert data["actions"][0]["target_phone"] == "+5491222222222"
        assert data["actions"][0]["target_matches_lead"] is False
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle["status"] == "level2_sent"
        assert cycle["level2_sent_at"] is not None
        assert len(calls) == 1
        assert calls[0]["to"] == "+5491222222222"
        assert "Podés seguir en el panel:" in calls[0]["text"]
        assert f"cliente={phone.lstrip('+')}" in calls[0]["text"]
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_flags_target_when_supervisor_matches_lead(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        services.set_followup_config(
            cliente=cliente,
            enabled=True,
            advisor_phone="+5491111111111",
            supervisor_phone=phone,
            first_delay_seconds=10,
            second_delay_seconds=15,
            updated_by="tests",
            allow_manual_evaluate=True,
        )
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        _set_cycle_fields(
            str(cycle["cycle_id"]),
            status="level1_sent",
            started_at=now - timedelta(seconds=30),
            level1_sent_at=now - timedelta(seconds=16),
            last_evaluated_at=now - timedelta(seconds=16),
        )

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions"][0]["action"] == "sent_level2"
        assert data["actions"][0]["provider_status"] == "submitted"
        assert data["actions"][0]["target_phone"] == phone
        assert data["actions"][0]["target_matches_lead"] is True
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_does_not_send_duplicate_level1(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        _set_cycle_fields(
            str(cycle["cycle_id"]),
            status="level1_sent",
            started_at=now - timedelta(seconds=30),
            level1_sent_at=now - timedelta(seconds=2),
            last_evaluated_at=now - timedelta(seconds=2),
        )

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions"][0]["action"] == "no_action"
        assert calls == []
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_does_not_send_duplicate_level2(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        _set_cycle_fields(
            str(cycle["cycle_id"]),
            status="level2_sent",
            started_at=now - timedelta(seconds=40),
            level1_sent_at=now - timedelta(seconds=20),
            level2_sent_at=now - timedelta(seconds=2),
            last_evaluated_at=now - timedelta(seconds=2),
        )

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions"][0]["action"] == "no_action"
        assert calls == []
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_closes_cycle_when_human_action_detected(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        _set_cycle_fields(
            str(cycle["cycle_id"]),
            status="level1_sent",
            started_at=now - timedelta(seconds=30),
            level1_sent_at=now - timedelta(seconds=20),
        )
        human_at = now - timedelta(seconds=1)
        _insert_human_outbound_message(
            conversation_id=str(payload["conversation_id"]),
            lead_id=str(payload["lead_id"]),
            text="Te escribo manualmente desde asesor",
            created_at=human_at,
        )

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions"][0]["action"] == "closed_human_action"
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        assert cycle["status"] == "completed"
        assert cycle["last_human_action_at"] is not None
        assert calls == []
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_closes_cycle_when_stage_changes(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload = _seed_pending_visit_ticket(client, phone)
        monkeypatch.setattr(services, "_utcnow", lambda: now)
        client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        _set_ticket_stage(str(payload["ticket_id"]), services.STAGE_WAITING_CONFIRMATION)

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["actions"][0]["action"] == "closed_stage_changed"
        cycle = _latest_cycle(str(payload["ticket_id"]))
        assert cycle is not None
        assert cycle["status"] == "cancelled"
        assert cycle["cancel_reason"] == "stage_changed"
        assert calls == []
    finally:
        _cleanup_phone(phone)
        _cleanup_config(cliente)


def test_followup_evaluate_one_ticket_only(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone_a = _unique_phone()
    phone_b = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload_a = _seed_pending_visit_ticket(client, phone_a)
        payload_b = _seed_pending_visit_ticket(client, phone_b)
        monkeypatch.setattr(services, "_utcnow", lambda: now)

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente, "ticket_id": str(payload_a["ticket_id"])},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["evaluated_count"] == 1
        assert data["actions"][0]["ticket_id"] == str(payload_a["ticket_id"])
        assert _latest_cycle(str(payload_a["ticket_id"])) is not None
        assert _latest_cycle(str(payload_b["ticket_id"])) is None
    finally:
        _cleanup_phone(phone_a)
        _cleanup_phone(phone_b)
        _cleanup_config(cliente)


def test_followup_evaluate_all_by_cliente(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    calls: list[dict] = []
    _wire_gupshup(monkeypatch, calls)
    cliente = _unique_cliente()
    phone_a = _unique_phone()
    phone_b = _unique_phone()
    now = datetime.now(timezone.utc)

    try:
        _seed_followup_config(cliente)
        payload_a = _seed_pending_visit_ticket(client, phone_a)
        payload_b = _seed_pending_visit_ticket(client, phone_b)
        _set_lead_name(str(payload_a["lead_id"]), "Mario Rojas")
        _set_lead_name(str(payload_b["lead_id"]), "Ana Demo")
        monkeypatch.setattr(services, "_utcnow", lambda: now)

        response = client.post(
            "/api/demo/vertice360-orquestador/followup/evaluate",
            json={"cliente": cliente},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["evaluated_count"] == 2
        action_ticket_ids = {item["ticket_id"] for item in data["actions"]}
        assert action_ticket_ids == {str(payload_a["ticket_id"]), str(payload_b["ticket_id"])}
        assert _latest_cycle(str(payload_a["ticket_id"])) is not None
        assert _latest_cycle(str(payload_b["ticket_id"])) is not None
    finally:
        _cleanup_phone(phone_a)
        _cleanup_phone(phone_b)
        _cleanup_config(cliente)


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        ({}, 401),
        ({"x-v360-admin-token": "wrong-token"}, 401),
    ],
)
def test_followup_evaluate_requires_admin_token(client, monkeypatch, headers: dict[str, str], expected_status: int) -> None:
    _headers(monkeypatch, env="prod", token="expected-token")
    response = client.post(
        "/api/demo/vertice360-orquestador/followup/evaluate",
        json={"cliente": _unique_cliente()},
        headers=headers,
    )
    assert response.status_code == expected_status
    assert response.json()["detail"] == "invalid admin token"
