"""Testes de fumaça e de integração da interface com Streamlit AppTest."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from core import InsertStatus, SearchLocation

APP_PATH = Path(__file__).resolve().parent / "app.py"


def _new_app() -> AppTest:
    """Cria e executa a aplicação em um ambiente de teste isolado."""

    return AppTest.from_file(str(APP_PATH), default_timeout=20).run()


def _button(at: AppTest, label: str):
    for button in at.button:
        if button.label == label:
            return button
    raise AssertionError(f"Botão não encontrado: {label!r}")


def _number_input(at: AppTest, label: str):
    for number_input in at.number_input:
        if number_input.label == label:
            return number_input
    raise AssertionError(f"Number input não encontrado: {label!r}")


def _metric(at: AppTest, label: str):
    for metric in at.metric:
        if metric.label == label:
            return metric
    raise AssertionError(f"Métrica não encontrada: {label!r}")


def test_app_smoke_initial_state() -> None:
    at = _new_app()

    assert not at.exception
    assert at.title[0].value == "🔎 Lista ordenada com cauda de inserções"
    assert len(at.session_state["ordered"]) == 1024
    assert at.session_state["tail"] == []
    assert at.session_state["last_search"] is None
    assert at.session_state["last_insert"] is None

    # Os controles principais existem e a aplicação não exige configuração
    # manual de estado para iniciar.
    assert _button(at, "🔍 Buscar")
    assert _button(at, "➕ Inserir")
    assert _button(at, "🔄 Reiniciar estrutura")
    assert _number_input(at, "Chave inteira")


def test_app_search_found_in_ordered_region_shows_metrics() -> None:
    at = _new_app()
    target = at.session_state["ordered"][500]

    _number_input(at, "Chave inteira").set_value(target)
    _button(at, "🔍 Buscar").click()
    at.run()

    assert not at.exception
    report = at.session_state["last_search"]
    assert report is not None
    assert report.found is True
    assert report.location is SearchLocation.ORDERED
    assert report.sequential_iterations == 0
    assert report.total_iterations == report.binary_iterations

    assert str(_metric(at, "Iterações da busca binária").value) == str(
        report.binary_iterations
    )
    assert str(_metric(at, "Iterações da busca sequencial").value) == "0"
    assert str(_metric(at, "Total de iterações").value) == str(report.total_iterations)
    assert _metric(at, "Local do resultado").value == SearchLocation.ORDERED.value
    assert len(at.success) >= 1


def test_app_search_missing_key_uses_binary_then_empty_tail() -> None:
    at = _new_app()

    _number_input(at, "Chave inteira").set_value(-999_999)
    _button(at, "🔍 Buscar").click()
    at.run()

    assert not at.exception
    report = at.session_state["last_search"]
    assert report is not None
    assert report.found is False
    assert report.location is SearchLocation.NOT_FOUND
    assert report.sequential_iterations == 0
    assert report.total_iterations == report.binary_iterations
    assert _metric(at, "Local do resultado").value == SearchLocation.NOT_FOUND.value
    assert len(at.warning) >= 1


def test_app_search_found_in_tail_after_insert() -> None:
    at = _new_app()
    new_key = max(at.session_state["ordered"]) + 1

    _number_input(at, "Chave inteira").set_value(new_key)
    _button(at, "➕ Inserir").click()
    at.run()
    assert not at.exception

    _number_input(at, "Chave inteira").set_value(new_key)
    _button(at, "🔍 Buscar").click()
    at.run()

    assert not at.exception
    report = at.session_state["last_search"]
    assert report is not None
    assert report.found is True
    assert report.location is SearchLocation.TAIL
    assert report.sequential_iterations == 1
    assert report.total_iterations == report.binary_iterations + 1
    assert _metric(at, "Local do resultado").value == SearchLocation.TAIL.value


def test_app_insert_then_reject_duplicate() -> None:
    at = _new_app()
    ordered = list(at.session_state["ordered"])
    new_key = max(ordered) + 1

    _number_input(at, "Chave inteira").set_value(new_key)
    _button(at, "➕ Inserir").click()
    at.run()

    assert not at.exception
    assert at.session_state["tail"] == [new_key]
    inserted = at.session_state["last_insert"]
    assert inserted is not None
    assert inserted.status is InsertStatus.INSERTED
    assert len(at.success) >= 1

    # Tentativa de inserir uma chave que já está na região ordenada.
    _number_input(at, "Chave inteira").set_value(ordered[0])
    _button(at, "➕ Inserir").click()
    at.run()

    assert not at.exception
    assert at.session_state["tail"] == [new_key]
    duplicate = at.session_state["last_insert"]
    assert duplicate is not None
    assert duplicate.status is InsertStatus.DUPLICATE
    assert len(at.error) >= 1


def test_app_tenth_insert_merges_and_empties_tail() -> None:
    at = _new_app()
    original = list(at.session_state["ordered"])
    start = max(original) + 1
    new_keys = list(range(start, start + 10))

    for new_key in new_keys:
        _number_input(at, "Chave inteira").set_value(new_key)
        _button(at, "➕ Inserir").click()
        at.run()
        assert not at.exception

    assert at.session_state["tail"] == []
    assert len(at.session_state["ordered"]) == len(original) + 10
    assert at.session_state["ordered"] == sorted(original + new_keys)

    outcome = at.session_state["last_insert"]
    assert outcome is not None
    assert outcome.status is InsertStatus.MERGED
    assert outcome.merged is True
    assert len(at.success) >= 1
