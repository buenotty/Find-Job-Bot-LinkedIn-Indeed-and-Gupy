import pytest

from jobbot.orientation import (
    MIN_SAMPLE, SATURATED_APPLICANTS, classify_group, cv_released, market_claims,
    price_band, projected_match,
)
from jobbot.schema import CourseDone, Profile, Screening, Skill, StretchPolicy, Target


def person(skills=("SQL",), courses=(), expectation=8000):
    return Profile(
        skills=[Skill(s) for s in skills],
        courses_done=list(courses),
        screening=Screening(salary_expectation=expectation),
    )


def test_constants():
    assert (MIN_SAMPLE, SATURATED_APPLICANTS) == (30, 200)


def test_group_boundary_49_50():
    pol = StretchPolicy()
    assert classify_group(49, pol) == "nova_formacao"
    assert classify_group(50, pol) == "agora"
    assert classify_group(59, StretchPolicy(90, 60)) == "nova_formacao"


def test_cv_released_rules():
    pol = StretchPolicy()
    assert cv_released(Target(group="agora"), 55, pol) is True
    assert cv_released(Target(group="nova_formacao"), 89, pol) is False
    assert cv_released(Target(group="nova_formacao"), 90, pol) is True
    assert cv_released(Target(group="nova_formacao"), None, pol) is False
    assert cv_released(Target(group="sem_dado"), 100, pol) is False


@pytest.mark.parametrize("price,expected", [(0, "gratuito"), (1, "barato"), (200, "barato"), (201, "caro"), (None, "sem_preco")])
def test_price_band(price, expected):
    assert price_band(price, 200) == expected


def test_price_band_custom_limit():
    assert price_band(150, 100) == "caro"


def course(*claimed, name="c"):
    return CourseDone(course=name, skills_claimed=list(claimed))


def test_projection_counts_only_claimed_required():
    p = person(courses=[course("Kafka", "Culinária")])
    assert projected_match(p, ["SQL", "Kafka", "Spark"]) == (66, ["Spark"])


def test_projection_matches_names_loosely():
    p = person(courses=[course("  power  BI ")])
    assert projected_match(p, ["Power BI"]) == (100, [])


def test_projection_not_inflated_by_duplicate_courses():
    once = projected_match(person(courses=[course("Kafka")]), ["SQL", "Kafka", "Spark"])
    twice = projected_match(person(courses=[course("Kafka", name="a"), course("Kafka", name="b")]), ["SQL", "Kafka", "Spark"])
    assert once == twice


def test_projection_duplicate_required_counts_once():
    assert projected_match(person(), ["SQL", "sql", "Kafka"]) == (50, ["Kafka"])


def test_projection_empty_required_returns_zero_without_error():
    assert projected_match(person(), []) == (0, [])


def test_projection_never_exceeds_100():
    p = person(skills=("SQL", "Kafka"), courses=[course("Kafka")])
    assert projected_match(p, ["SQL", "Kafka"]) == (100, [])


def test_projection_does_not_mutate_profile_skills():
    p = person(courses=[course("Kafka")])
    projected_match(p, ["SQL", "Kafka"])
    assert [s.name for s in p.skills] == ["SQL"]


def test_claims_29_vs_30_jobs():
    p = person()
    assert market_claims(29, 5000, 300, p) == {"saturado": "indicio", "paga_pouco": "indicio"}
    assert market_claims(30, 5000, 300, p) == {"saturado": "sim", "paga_pouco": "sim"}


def test_claims_without_salary_expectation_never_say_paga_pouco():
    got = market_claims(50, 1000, 10, person(expectation=None))
    assert got["paga_pouco"] == "sem_dado"


def test_claims_saturated_threshold():
    p = person()
    assert market_claims(30, 9000, 199, p)["saturado"] == "nao"
    assert market_claims(30, 9000, 200, p)["saturado"] == "sim"


def test_claims_missing_data():
    assert market_claims(50, None, None, person()) == {"saturado": "sem_dado", "paga_pouco": "sem_dado"}
