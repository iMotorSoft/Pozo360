from __future__ import annotations

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


def _unique_cliente() -> str:
    return f"followup-demo-{uuid.uuid4().hex[:12]}"


def _followup_headers(
    monkeypatch,
    *,
    env: str = "dev",
    token: str = "test-followup-token",
) -> dict[str, str]:
    monkeypatch.setenv("VERTICE360_ENV", env)
    monkeypatch.setenv("V360_ADMIN_TOKEN", token)
    monkeypatch.setattr(globalVar, "ENVIRONMENT", env, raising=False)
    monkeypatch.setattr(globalVar, "RUN_ENV", env, raising=False)
    monkeypatch.setattr(globalVar, "V360_ADMIN_TOKEN", token, raising=False)
    return {"x-v360-admin-token": token}


def _cleanup_config(cliente: str) -> None:
    def _tx(conn):
        repo.ensure_visit_followup_config_schema(conn)
        conn.execute("delete from visit_followup_config where cliente = %s", (cliente,))

    db.run_in_transaction(_tx)


def _base_payload(cliente: str, **overrides) -> dict:
    payload = {
        "cliente": cliente,
        "enabled": True,
        "advisor_phone": "+5491111111111",
        "supervisor_phone": "+5491222222222",
        "first_delay_seconds": 15,
        "second_delay_seconds": 20,
        "level1_template": (
            "Tenés una cita pendiente sin responder para {lead_name_or_phone} "
            "en {project}. Ticket {ticket_id}."
        ),
        "level2_template": (
            "Escalamiento: la cita pendiente de {lead_name_or_phone} "
            "en {project} superó el tiempo de respuesta. Ticket {ticket_id}."
        ),
        "updated_by": "mario",
        "board_base_url": "http://localhost:3062/demo/vertice360-orquestador/",
        "allow_manual_evaluate": True,
    }
    payload.update(overrides)
    return payload


def test_followup_config_create_ok(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    try:
        response = client.post(
            "/api/demo/vertice360-orquestador/followup/config/set",
            json=_base_payload(cliente),
            headers=headers,
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["cliente"] == cliente
        assert payload["enabled"] is True
        assert payload["advisor_phone"] == "+5491111111111"
        assert payload["supervisor_phone"] == "+5491222222222"
        assert payload["first_delay_seconds"] == 15
        assert payload["second_delay_seconds"] == 20
        assert payload["allow_manual_evaluate"] is True
        assert payload["updated_by"] == "mario"
        assert payload["updated_at"]
    finally:
        _cleanup_config(cliente)


def test_followup_config_update_ok(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    try:
        create = client.post(
            "/api/demo/vertice360-orquestador/followup/config/set",
            json=_base_payload(cliente),
            headers=headers,
        )
        assert create.status_code == 200

        update = client.post(
            "/api/demo/vertice360-orquestador/followup/config/set",
            json=_base_payload(
                cliente,
                enabled=False,
                advisor_phone=None,
                supervisor_phone=None,
                first_delay_seconds=30,
                second_delay_seconds=45,
                updated_by="lucia",
                allow_manual_evaluate=False,
            ),
            headers=headers,
        )
        assert update.status_code == 200

        payload = update.json()
        assert payload["cliente"] == cliente
        assert payload["enabled"] is False
        assert payload["advisor_phone"] is None
        assert payload["supervisor_phone"] is None
        assert payload["first_delay_seconds"] == 30
        assert payload["second_delay_seconds"] == 45
        assert payload["allow_manual_evaluate"] is False
        assert payload["updated_by"] == "lucia"
    finally:
        _cleanup_config(cliente)


def test_followup_config_get_ok(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    try:
        create = client.post(
            "/api/demo/vertice360-orquestador/followup/config/set",
            json=_base_payload(cliente),
            headers=headers,
        )
        assert create.status_code == 200

        response = client.get(
            "/api/demo/vertice360-orquestador/followup/config/get",
            params={"cliente": cliente},
            headers=headers,
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["cliente"] == cliente
        assert payload["advisor_phone"] == "+5491111111111"
        assert payload["supervisor_phone"] == "+5491222222222"
    finally:
        _cleanup_config(cliente)


def test_followup_config_set_allowed_with_valid_token_in_prod(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch, env="prod")
    cliente = _unique_cliente()

    try:
        response = client.post(
            "/api/demo/vertice360-orquestador/followup/config/set",
            json=_base_payload(cliente),
            headers=headers,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["cliente"] == cliente
        assert payload["advisor_phone"] == "+5491111111111"
    finally:
        _cleanup_config(cliente)


def test_followup_config_get_allowed_with_valid_token_in_prod(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch, env="prod")
    cliente = _unique_cliente()

    try:
        create = client.post(
            "/api/demo/vertice360-orquestador/followup/config/set",
            json=_base_payload(cliente),
            headers=headers,
        )
        assert create.status_code == 200

        response = client.get(
            "/api/demo/vertice360-orquestador/followup/config/get",
            params={"cliente": cliente},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["cliente"] == cliente
    finally:
        _cleanup_config(cliente)


def test_followup_config_set_rejects_without_token(client, monkeypatch) -> None:
    _followup_headers(monkeypatch, env="prod")
    cliente = _unique_cliente()

    response = client.post(
        "/api/demo/vertice360-orquestador/followup/config/set",
        json=_base_payload(cliente),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"


def test_followup_config_get_rejects_without_token(client, monkeypatch) -> None:
    _followup_headers(monkeypatch, env="prod")

    response = client.get(
        "/api/demo/vertice360-orquestador/followup/config/get",
        params={"cliente": _unique_cliente()},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"


def test_followup_config_set_rejects_invalid_token(client, monkeypatch) -> None:
    _followup_headers(monkeypatch, env="prod", token="expected-token")
    cliente = _unique_cliente()

    response = client.post(
        "/api/demo/vertice360-orquestador/followup/config/set",
        json=_base_payload(cliente),
        headers={"x-v360-admin-token": "wrong-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"


def test_followup_config_get_rejects_invalid_token(client, monkeypatch) -> None:
    _followup_headers(monkeypatch, env="prod", token="expected-token")

    response = client.get(
        "/api/demo/vertice360-orquestador/followup/config/get",
        params={"cliente": _unique_cliente()},
        headers={"x-v360-admin-token": "wrong-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"


def test_followup_config_get_missing_returns_404(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()
    _cleanup_config(cliente)

    response = client.get(
        "/api/demo/vertice360-orquestador/followup/config/get",
        params={"cliente": cliente},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "followup config not found"


def test_followup_config_enabled_true_without_advisor_phone_returns_error(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    response = client.post(
        "/api/demo/vertice360-orquestador/followup/config/set",
        json=_base_payload(cliente, advisor_phone=None),
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "advisor_phone is required when enabled=true"


def test_followup_config_enabled_true_without_supervisor_phone_returns_error(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    response = client.post(
        "/api/demo/vertice360-orquestador/followup/config/set",
        json=_base_payload(cliente, supervisor_phone=None),
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "supervisor_phone is required when enabled=true"


@pytest.mark.parametrize(
    ("field_name", "field_value", "detail"),
    [
        ("first_delay_seconds", 0, "first_delay_seconds must be > 0"),
        ("second_delay_seconds", -1, "second_delay_seconds must be > 0"),
    ],
)
def test_followup_config_invalid_delays_return_error(
    client,
    monkeypatch,
    field_name: str,
    field_value: int,
    detail: str,
) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    response = client.post(
        "/api/demo/vertice360-orquestador/followup/config/set",
        json=_base_payload(cliente, **{field_name: field_value}),
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == detail


def test_followup_config_normalizes_phones(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    try:
        response = client.post(
            "/api/demo/vertice360-orquestador/followup/config/set",
            json=_base_payload(
                cliente,
                advisor_phone="54911 1111-1111",
                supervisor_phone="(549) 1222-222222",
            ),
            headers=headers,
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["advisor_phone"] == "+5491111111111"
        assert payload["supervisor_phone"] == "+5491222222222"
    finally:
        _cleanup_config(cliente)


def test_followup_config_invalid_template_placeholder_returns_error(client, monkeypatch) -> None:
    headers = _followup_headers(monkeypatch)
    cliente = _unique_cliente()

    response = client.post(
        "/api/demo/vertice360-orquestador/followup/config/set",
        json=_base_payload(
            cliente,
            level1_template="Hola {lead_name_or_phone}. Placeholder inválido: {foo}.",
        ),
        headers=headers,
    )

    assert response.status_code == 400
    assert "{foo}" in response.json()["detail"]


def test_followup_config_schema_apply_is_idempotent() -> None:
    def _tx(conn):
        repo.ensure_visit_followup_config_schema(conn)
        repo.ensure_visit_followup_config_schema(conn)
        row = conn.execute("select to_regclass('visit_followup_config')::text").fetchone()
        return row[0]

    table_name = db.run_in_transaction(_tx)
    assert table_name == "visit_followup_config"
