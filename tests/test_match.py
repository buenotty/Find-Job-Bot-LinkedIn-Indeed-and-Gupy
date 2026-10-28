import pytest

from jobbot.match import coverage, label, normalize, stretch_action
from jobbot.schema import Skill, StretchPolicy


@pytest.mark.parametrize("pct,expected", [
    (0, "Arriscado"), (49, "Arriscado"), (50, "Chance média"), (69, "Chance média"),
    (70, "Bom match"), (79, "Bom match"), (80, "Ótimo match"), (99, "Ótimo match"),
    (100, "Vaga perfeita"),
])
def test_label_boundaries(pct, expected):
    assert label(pct) == expected


def test_normalize_strips_accents_case_spaces():
    assert normalize("  Análise   de DADOS ") == "analise de dados"


def test_coverage_normalizes():
    assert coverage(["power bi", "SQL "], [Skill("Power  BI"), Skill("sql")]) == (100, [])


def test_coverage_accents():
    assert coverage(["analise de dados"], [Skill("Análise de Dados")]) == (100, [])


def test_coverage_floor_never_rounds_up_to_100():
    required = [f"s{i}" for i in range(200)]
    skills = [Skill(f"s{i}") for i in range(199)]
    pct, missing = coverage(required, skills)
    assert pct == 99 and missing == ["s199"]


def test_coverage_reports_missing_in_original_spelling():
    assert coverage(["SQL", "Kafka"], [Skill("sql")]) == (50, ["Kafka"])


def test_coverage_empty_required_raises():
    with pytest.raises(ValueError):
        coverage([], [Skill("SQL")])


@pytest.mark.parametrize("pct,expected", [
    (100, "esticar"), (90, "esticar"), (89, "esticar_marcado"),
    (50, "esticar_marcado"), (49, "arriscada"),
])
def test_stretch_action_default_policy(pct, expected):
    assert stretch_action(pct, StretchPolicy()) == expected


def test_stretch_action_custom_policy():
    policy = StretchPolicy(stretch_from=80, risky_below=40)
    assert stretch_action(80, policy) == "esticar"
    assert stretch_action(40, policy) == "esticar_marcado"
    assert stretch_action(39, policy) == "arriscada"


from jobbot.match import coverage_detail  # noqa: E402


def test_adjacent_skill_counts_as_covered_and_is_reported():
    pct, missing, adjacent = coverage_detail(["SQL Server", "Kafka"], [Skill("SQL")])
    assert (pct, missing, adjacent) == (50, ["Kafka"], {"SQL Server": "SQL"})
    assert coverage(["SQL Server"], [Skill("sql")]) == (100, [])


def test_ssms_and_excel_adjacencies():
    assert coverage_detail(["T-SQL"], [Skill("SSMS")])[2] == {"T-SQL": "SSMS"}
    assert coverage_detail(["Excel Avançado"], [Skill("Excel")])[2] == {"Excel Avançado": "Excel"}


def test_unrelated_names_sharing_a_word_are_not_adjacent():
    assert coverage_detail(["Data Science"], [Skill("Data")]) == (0, ["Data Science"], {})
    assert coverage_detail(["Python"], [Skill("SQL")]) == (0, ["Python"], {})


def test_literal_ownership_wins_over_adjacency():
    assert coverage_detail(["SQL Server"], [Skill("SQL Server"), Skill("SQL")]) == (100, [], {})
