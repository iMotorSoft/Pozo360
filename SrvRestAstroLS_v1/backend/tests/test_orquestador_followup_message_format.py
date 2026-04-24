from __future__ import annotations

from backend.modules.vertice360_orquestador_demo import services


def test_followup_message_appends_panel_link() -> None:
    config = {
        "level1_template": None,
        "board_base_url": "https://demo.vertice360.imotorsoft.com/demo/vertice360-orquestador/",
    }
    context = {
        "lead_phone": "+59168912007",
        "project_code": "GDR_3760_SAAVEDRA",
    }

    message = services._followup_message_for_level(
        1,
        config=config,
        ticket_id="ticket-123",
        context=context,
    )

    assert "Podés seguir en el panel:" in message
    assert "cliente=59168912007" in message


def test_followup_message_does_not_duplicate_existing_board_url() -> None:
    board_url = "https://demo.vertice360.imotorsoft.com/demo/vertice360-orquestador/?cliente=59168912007"
    config = {
        "level1_template": f"Ticket {{ticket_id}}. Panel: {board_url}",
        "board_base_url": "https://demo.vertice360.imotorsoft.com/demo/vertice360-orquestador/",
    }
    context = {
        "lead_phone": "+59168912007",
        "project_code": "GDR_3760_SAAVEDRA",
    }

    message = services._followup_message_for_level(
        1,
        config=config,
        ticket_id="ticket-123",
        context=context,
    )

    assert message.count(board_url) == 1
