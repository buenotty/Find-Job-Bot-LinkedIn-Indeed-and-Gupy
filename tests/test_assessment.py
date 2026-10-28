from datetime import date

import pytest

from jobbot.assessment import (
    Item, consistency, dimension_key, finish, load_bank, progress, score, submit_answers,
)
from jobbot.store import load_profile, profile_dir, put_step

IDENT = {"name": "Ana", "age": 30, "state": "SP", "city": "SP"}


def bank():
    return [
        Item("v1", "valores", "salario", "t1"),
        Item("v2", "valores", "salario", "t2"),
        Item("i1", "interesses", "pratico", "a"),
        Item("i2", "interesses", "pratico", "b", reverse=True),
        Item("i3", "interesses", "pratico", "c", reverse=True, twin="i1"),
    ]


def adjusted(level):
    """Raw answers that all land on `level` after reverse-adjustment."""
    return {i.id: (6 - level if i.reverse else level) for i in bank()}


def test_dimension_key():
    assert dimension_key(bank()[0]) == "valores.salario"


@pytest.mark.parametrize("level,expected", [(5, 100), (1, 0), (3, 50)])
def test_score_is_percent_of_max(level, expected):
    assert set(score(adjusted(level), bank()).values()) == {expected}


def test_reverse_item_flips():
    high = adjusted(5)
    flipped = {**high, "i2": 5}  # reverse item answered 5 counts as 1
    assert score(flipped, bank())["interesses.pratico"] < score(high, bank())["interesses.pratico"]


def test_submit_rejects_out_of_range_all_or_nothing(tmp_home):
    with pytest.raises(ValueError, match="v2"):
        submit_answers("Ana", {"v1": 3, "v2": 6}, bank())
    assert progress("Ana", bank()) == ("valores", 0, 5)


@pytest.mark.parametrize("bad", [{"zz": 3}, {"v1": "abc"}, {"v1": True}, {"v1": 3.5}, {"v1": 0}])
def test_submit_rejects_bad_values(tmp_home, bad):
    with pytest.raises(ValueError):
        submit_answers("Ana", bad, bank())
    assert progress("Ana", bank())[1] == 0


def test_resume_progress_by_layer(tmp_home):
    assert progress("Ana", bank())[0] == "valores"
    submit_answers("Ana", {"v1": 3, "v2": 4}, bank())
    assert progress("Ana", bank()) == ("interesses", 2, 5)
    submit_answers("Ana", {"i1": 1, "i2": 2, "i3": 3}, bank())
    assert progress("Ana", bank()) == (None, 5, 5)


def test_later_answers_overwrite(tmp_home):
    submit_answers("Ana", {"v1": 3}, bank())
    submit_answers("Ana", {"v1": 5}, bank())
    assert progress("Ana", bank())[1] == 1


def test_straight_lining_flagged():
    assert consistency({i.id: 3 for i in bank()}, bank()) == ("baixa", ["respostas_uniformes"])


def test_incoherent_twins_flagged():
    answers = {"v1": 1, "v2": 2, "i1": 5, "i2": 4, "i3": 5}  # i3 reverse: adjusted 1 vs i1 5
    assert consistency(answers, bank()) == ("baixa", ["pares_incoerentes"])


def test_coherent_answers_are_alta():
    answers = {"v1": 4, "v2": 5, "i1": 4, "i2": 1, "i3": 2}
    assert consistency(answers, bank()) == ("alta", [])


def test_finish_requires_all_answers(tmp_home):
    submit_answers("Ana", {"v1": 3}, bank())
    with pytest.raises(ValueError, match="faltam 4"):
        finish("Ana", bank(), [], date(2026, 10, 25))


def test_finish_appends_and_clears_state(tmp_home):
    put_step("Ana", "identidade", IDENT)
    submit_answers("Ana", {"v1": 4, "v2": 5, "i1": 4, "i2": 1, "i3": 2}, bank())
    a = finish("Ana", bank(), [{"pergunta": "q", "resposta": "r"}], date(2026, 10, 25))
    assert a.confiabilidade == "alta" and a.scores["valores.salario"] == 88
    got = load_profile("Ana").assessments
    assert len(got) == 1 and got[0].situations[0]["resposta"] == "r"
    assert not (profile_dir("Ana") / "test_state.yaml").exists()


def test_retake_keeps_history_latest_wins(tmp_home):
    put_step("Ana", "identidade", IDENT)
    for day in (date(2026, 10, 1), date(2026, 10, 25)):
        submit_answers("Ana", {"v1": 4, "v2": 5, "i1": 4, "i2": 1, "i3": 2}, bank())
        finish("Ana", bank(), [], day)
    got = load_profile("Ana").assessments
    assert [a.date for a in got] == ["2026-10-01", "2026-10-25"]


def test_bank_loader_rejects_bad_twin_duplicate_and_layer(tmp_path):
    def bank_file(rows):
        f = tmp_path / "b.yaml"
        f.write_text(rows)
        return f
    with pytest.raises(ValueError, match="twin"):
        load_bank(bank_file("- {id: a, layer: valores, dimension: d, text: t, twin: nope}\n"))
    with pytest.raises(ValueError, match="duplic"):
        load_bank(bank_file("- {id: a, layer: valores, dimension: d, text: t}\n- {id: a, layer: valores, dimension: d, text: u}\n"))
    with pytest.raises(ValueError, match="camada"):
        load_bank(bank_file("- {id: a, layer: xyz, dimension: d, text: t}\n"))


def test_track_and_holland_code_from_scores():
    from jobbot.assessment import holland_code, track_from_scores
    assert track_from_scores({"ancoras.tecnica": 83, "ancoras.gestao": 50}) == "especialista"
    assert track_from_scores({"ancoras.tecnica": 40, "ancoras.gestao": 75}) == "gestao"
    assert track_from_scores({"ancoras.tecnica": 60, "ancoras.gestao": 58}) == "indefinido"
    assert track_from_scores({}) == "indefinido"
    assert track_from_scores({"ancoras.tecnica": 83, "ancoras.gestao": 75}) == "hibrido"
    tie = {"ancoras.tecnica": 55, "ancoras.gestao": 50}
    assert track_from_scores({**tie, "estilo.lideranca": 80}) == "gestao"
    assert track_from_scores({**tie, "estilo.lideranca": 20}) == "especialista"
    assert track_from_scores({**tie, "estilo.lideranca": 50}) == "indefinido"
    scores = {"interesses.investigativo": 90, "interesses.pratico": 80, "interesses.convencional": 70,
              "interesses.social": 40, "interesses.artistico": 40, "interesses.empreendedor": 10}
    assert holland_code(scores) == "IRC"
