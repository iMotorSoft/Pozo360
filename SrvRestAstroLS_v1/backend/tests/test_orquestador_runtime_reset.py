from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend import globalVar
from backend.modules.vertice360_orquestador_demo import db, repo, services


def _db_ready() -> bool:
    return services.demo_db_ready()


pytestmark = pytest.mark.skipif(
    not _db_ready(),
    reason="Requires DB_PG_V360_URL + psycopg connectivity to v360",
)


def _headers(monkeypatch, *, env: str = "prod", token: str = "reset-token") -> dict[str, str]:
    monkeypatch.setenv("VERTICE360_ENV", env)
    monkeypatch.setenv("V360_ADMIN_TOKEN", token)
    monkeypatch.setattr(globalVar, "ENVIRONMENT", env, raising=False)
    monkeypatch.setattr(globalVar, "RUN_ENV", env, raising=False)
    monkeypatch.setattr(globalVar, "V360_ADMIN_TOKEN", token, raising=False)
    return {"x-v360-admin-token": token}


def _unique_phone() -> str:
    tail = str(uuid.uuid4().int)[-10:]
    return f"+54911{tail}"


def _unique_cliente() -> str:
    return f"reset-config-{uuid.uuid4().hex[:10]}"


def _cleanup_phone(phone_e164: str) -> None:
    def _tx(conn):
        repo.reset_by_phone(conn, phone_e164)

    db.run_in_transaction(_tx)


def _cleanup_config(cliente: str) -> None:
    def _tx(conn):
        repo.ensure_visit_followup_config_schema(conn)
        conn.execute("delete from visit_followup_config where cliente = %s", (cliente,))

    db.run_in_transaction(_tx)


def _seed_followup_config(cliente: str) -> None:
    services.set_followup_config(
        cliente=cliente,
        enabled=True,
        advisor_phone="+5491111111111",
        supervisor_phone="+5491222222222",
        first_delay_seconds=15,
        second_delay_seconds=20,
        updated_by="tests",
        allow_manual_evaluate=True,
    )


def _seed_runtime(client, phone: str, *, with_visit: bool = False) -> dict:
    ingest = client.post(
        "/api/demo/vertice360-orquestador/ingest_message",
        json={"phone": phone, "text": "Hola, quiero coordinar visita"},
    )
    assert ingest.status_code == 200
    payload = ingest.json()

    if with_visit:
        def _tx(conn):
            proposal = repo.create_visit_proposal(
                conn,
                ticket_id=str(payload["ticket_id"]),
                conversation_id=str(payload["conversation_id"]),
                lead_id=str(payload["lead_id"]),
                advisor_id=None,
                mode="propose",
                option1=datetime.now(timezone.utc) + timedelta(days=1),
                option2=datetime.now(timezone.utc) + timedelta(days=2),
                option3=datetime.now(timezone.utc) + timedelta(days=3),
                message_out="Te propongo horarios para la visita",
            )
            repo.insert_visit_confirmation(
                conn,
                proposal_id=str(proposal["id"]),
                ticket_id=str(payload["ticket_id"]),
                confirmed_option=1,
                confirmed_at=proposal["option1"],
                confirmed_by="advisor",
            )

        db.run_in_transaction(_tx)

    return payload


def _runtime_counts_for_phone(phone_e164: str) -> dict[str, int]:
    def _tx(conn):
        lead_row = conn.execute("select id from leads where phone_e164 = %s", (phone_e164,)).fetchone()
        if lead_row is None:
            return {table: 0 for table in repo.runtime_resettable_tables(conn)}

        lead_id = lead_row[0]
        ticket_rows = conn.execute("select id from tickets where lead_id = %s", (lead_id,)).fetchall()
        ticket_ids = [str(row[0]) for row in ticket_rows]
        placeholders = ", ".join(["%s"] * len(ticket_ids)) if ticket_ids else ""
        counts = {table: 0 for table in repo.runtime_resettable_tables(conn)}

        if ticket_ids:
            counts["events"] = int(conn.execute(f"select count(*) from events where correlation_id in ({placeholders})", tuple(ticket_ids)).fetchone()[0])
            counts["visit_confirmations"] = int(conn.execute(f"select count(*) from visit_confirmations where ticket_id in ({placeholders})", tuple(ticket_ids)).fetchone()[0])
            counts["visit_proposals"] = int(conn.execute(f"select count(*) from visit_proposals where ticket_id in ({placeholders})", tuple(ticket_ids)).fetchone()[0])
            for table_name in repo.runtime_resettable_tables(conn):
                if table_name in {"events", "visit_confirmations", "visit_proposals", "messages", "tickets", "conversations", "leads"}:
                    continue
                counts[table_name] = int(conn.execute(f"select count(*) from {table_name} where ticket_id in ({placeholders})", tuple(ticket_ids)).fetchone()[0])

        counts["messages"] = int(conn.execute("select count(*) from messages where lead_id = %s", (lead_id,)).fetchone()[0])
        counts["tickets"] = int(conn.execute("select count(*) from tickets where lead_id = %s", (lead_id,)).fetchone()[0])
        counts["conversations"] = int(conn.execute("select count(*) from conversations where lead_id = %s", (lead_id,)).fetchone()[0])
        counts["leads"] = 1
        return counts

    return db.run_in_transaction(_tx)


def _global_runtime_counts() -> dict[str, int]:
    def _tx(conn):
        counts = {}
        for table_name in repo.runtime_resettable_tables(conn):
            counts[table_name] = int(conn.execute(f"select count(*) from {table_name}").fetchone()[0])
        return counts

    return db.run_in_transaction(_tx)


def _protected_counts() -> dict[str, int]:
    def _tx(conn):
        counts = {}
        for table_name in repo.protected_reset_tables():
            counts[table_name] = int(conn.execute(f"select count(*) from {table_name}").fetchone()[0])
        return counts

    return db.run_in_transaction(_tx)


def test_reset_runtime_phone_deletes_only_target_runtime_and_keeps_protected_data(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    phone_target = _unique_phone()
    phone_other = _unique_phone()
    cliente = _unique_cliente()

    try:
        _seed_followup_config(cliente)
        protected_before = _protected_counts()
        _seed_runtime(client, phone_target, with_visit=True)
        _seed_runtime(client, phone_other, with_visit=False)

        before_target = _runtime_counts_for_phone(phone_target)
        before_other = _runtime_counts_for_phone(phone_other)
        assert before_target["leads"] == 1
        assert before_target["visit_proposals"] == 1
        assert before_target["visit_confirmations"] == 1
        assert before_other["leads"] == 1

        response = client.post(
            "/api/demo/vertice360-orquestador/admin/reset_runtime_phone",
            json={"phone": phone_target},
            headers=headers,
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["ok"] is True
        assert payload["mode"] == "phone"
        assert payload["phone"] == phone_target
        assert payload["deleted"]["leads"] == 1
        assert payload["deleted"]["visit_proposals"] == 1
        assert payload["deleted"]["visit_confirmations"] == 1
        assert "visit_followup_config" in payload["protected_not_touched"]

        after_target = _runtime_counts_for_phone(phone_target)
        after_other = _runtime_counts_for_phone(phone_other)
        assert all(value == 0 for value in after_target.values())
        assert after_other == before_other
        assert _protected_counts() == protected_before
        assert services.get_followup_config(cliente=cliente)["cliente"] == cliente
    finally:
        _cleanup_phone(phone_target)
        _cleanup_phone(phone_other)
        _cleanup_config(cliente)


def test_reset_runtime_all_deletes_runtime_and_keeps_protected_data(client, monkeypatch) -> None:
    baseline_runtime = _global_runtime_counts()
    if any(value != 0 for value in baseline_runtime.values()):
        pytest.skip("reset_runtime_all integration test requires an empty runtime baseline")

    headers = _headers(monkeypatch, env="prod")
    phone_a = _unique_phone()
    phone_b = _unique_phone()
    cliente = _unique_cliente()

    try:
        _seed_followup_config(cliente)
        protected_before = _protected_counts()
        _seed_runtime(client, phone_a, with_visit=True)
        _seed_runtime(client, phone_b, with_visit=False)

        runtime_before = _global_runtime_counts()
        assert runtime_before["leads"] == 2
        assert runtime_before["visit_proposals"] == 1
        assert runtime_before["visit_confirmations"] == 1

        response = client.post(
            "/api/demo/vertice360-orquestador/admin/reset_runtime_all",
            json={"confirm": "RESET_RUNTIME_ONLY"},
            headers=headers,
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["ok"] is True
        assert payload["mode"] == "all"
        assert payload["deleted"]["leads"] == 2
        assert payload["deleted"]["visit_proposals"] == 1
        assert payload["deleted"]["visit_confirmations"] == 1
        assert "demo_units" in payload["protected_not_touched"]
        assert "visit_followup_config" in payload["protected_not_touched"]

        runtime_after = _global_runtime_counts()
        assert all(value == 0 for value in runtime_after.values())
        assert _protected_counts() == protected_before
        assert services.get_followup_config(cliente=cliente)["cliente"] == cliente
    finally:
        _cleanup_phone(phone_a)
        _cleanup_phone(phone_b)
        _cleanup_config(cliente)


def test_reset_runtime_all_requires_exact_confirm_string(client, monkeypatch) -> None:
    headers = _headers(monkeypatch, env="prod")
    phone = _unique_phone()

    try:
        _seed_runtime(client, phone, with_visit=False)
        before = _global_runtime_counts()

        response = client.post(
            "/api/demo/vertice360-orquestador/admin/reset_runtime_all",
            json={"confirm": "RESET_ALL"},
            headers=headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "confirm must be RESET_RUNTIME_ONLY"
        assert _global_runtime_counts() == before
    finally:
        _cleanup_phone(phone)


@pytest.mark.parametrize(
    ("method", "url", "json_payload"),
    [
        ("post", "/api/demo/vertice360-orquestador/admin/reset_runtime_phone", {"phone": "+5491111111111"}),
        ("post", "/api/demo/vertice360-orquestador/admin/reset_runtime_all", {"confirm": "RESET_RUNTIME_ONLY"}),
    ],
)
def test_runtime_reset_rejects_without_token(client, monkeypatch, method: str, url: str, json_payload: dict) -> None:
    _headers(monkeypatch, env="prod")
    response = getattr(client, method)(url, json=json_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"


@pytest.mark.parametrize(
    ("method", "url", "json_payload"),
    [
        ("post", "/api/demo/vertice360-orquestador/admin/reset_runtime_phone", {"phone": "+5491111111111"}),
        ("post", "/api/demo/vertice360-orquestador/admin/reset_runtime_all", {"confirm": "RESET_RUNTIME_ONLY"}),
    ],
)
def test_runtime_reset_rejects_invalid_token(client, monkeypatch, method: str, url: str, json_payload: dict) -> None:
    _headers(monkeypatch, env="prod", token="expected-token")
    response = getattr(client, method)(url, json=json_payload, headers={"x-v360-admin-token": "wrong-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"
