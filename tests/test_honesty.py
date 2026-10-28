from datetime import date

from jobbot.honesty import total_years, unsupported_numbers
from tests.test_schema import full_profile

TODAY = date(2027, 3, 1)  # full_profile starts 2020-01 -> 7 whole years


def test_reported_metric_allowed():
    assert unsupported_numbers("Reduzi 40% do tempo de carga", full_profile(), TODAY) == []


def test_invented_metric_flagged():
    assert unsupported_numbers("Reduzi 70% do tempo", full_profile(), TODAY) == ["70%"]


def test_age_is_not_a_metric():
    p = full_profile()
    p.age = 40
    p.experiences[0].bullets[0].metric = None
    assert unsupported_numbers("Ganho de 40%", p, TODAY) == ["40%"]


def test_decimal_comma_matches_years_by_skill():
    p = full_profile()
    p.screening.years_by_skill = {"SQL": 2.5}
    assert unsupported_numbers("2,5 anos de SQL", p, TODAY) == []


def test_total_years_allowed_and_next_flagged():
    p = full_profile()
    assert total_years(p, TODAY) == 7
    assert unsupported_numbers("7 anos de experiência", p, TODAY) == []
    assert unsupported_numbers("8 anos de experiência", p, TODAY) == ["8"]


def test_total_years_without_experience_is_zero():
    p = full_profile()
    p.experiences = []
    assert total_years(p, TODAY) == 0


def test_numbers_inside_words_ignored():
    assert unsupported_numbers("AWS S3 e Web3", full_profile(), TODAY) == []


def test_repeated_token_reported_once():
    assert unsupported_numbers("70% e depois 70%", full_profile(), TODAY) == ["70%"]


def test_project_start_year_allowed():
    from jobbot.schema import Project
    p = full_profile()
    p.projects = [Project("Montagem", "x", None, "autodidata", "2022-03", None)]
    assert unsupported_numbers("Autodidata desde 2022", p, TODAY) == []


def test_practice_years_still_need_years_by_skill():
    assert unsupported_numbers("4 anos de montagem", full_profile(), TODAY) == ["4"]


def test_education_years_are_allowed():
    from jobbot.schema import Education
    p = full_profile()
    p.education = [Education("USJT", "Sistemas", "graduacao", "2019", "2023", "concluido")]
    assert unsupported_numbers("Formado em 2023, curso iniciado em 2019", p, TODAY) == []
    assert unsupported_numbers("Formado em 2018", p, TODAY) == ["2018"]
