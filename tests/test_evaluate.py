import pytest

from jobbot.evaluate import evaluate
from jobbot.posting import Posting
from jobbot.schema import Constraints, CourseDone, JobType, Profile, Screening, Skill, StretchPolicy


def skills(n_total, n_owned):
    names = [f"s{i}" for i in range(n_total)]
    return names, [Skill(s) for s in names[:n_owned]]


def run(n_total, n_owned, **post_kw):
    names, owned = skills(n_total, n_owned)
    p = Profile(skills=owned, screening=Screening(salary_expectation=5000, contract="CLT"),
                job_types=[JobType(role="T", salary_floor=5000)])
    return evaluate(Posting(title="T", skills=names, **post_kw), p, "T"), p


def test_evaluate_empty_skills_raises_clear_error():
    with pytest.raises(ValueError, match="sem lista de skills"):
        evaluate(Posting(title="T"), Profile(), None)


@pytest.mark.parametrize("total,owned,action,stretched", [
    (20, 19, "esticar", 1), (10, 6, "esticar_marcado", 4), (5, 2, "arriscada", 0)])
def test_evaluate_stretch_actions(total, owned, action, stretched):
    ev, _ = run(total, owned)
    assert ev.action == action and len(ev.stretched) == stretched
    assert ev.risky == (action == "arriscada")


def test_evaluate_below_floor_flagged_not_dropped():
    ev, _ = run(10, 10, salary=4000)
    assert ev.below_floor is True and ev.match == 100
    assert run(10, 10, salary=5000)[0].below_floor is False


def test_evaluate_missing_salary_passes_with_note():
    ev, _ = run(10, 10)
    assert ev.below_floor is False and "salário não informado" in ev.notes
    assert ev.good_without_type is True


def test_evaluate_no_floor_means_no_check():
    names, owned = skills(5, 5)
    p = Profile(skills=owned, job_types=[JobType(role="T")])
    ev = evaluate(Posting(title="T", skills=names, salary=1000), p, "T")
    assert ev.below_floor is False and ev.good_without_type is True


def test_evaluate_unknown_type_role_raises():
    with pytest.raises(ValueError, match="tipo"):
        evaluate(Posting(title="T", skills=["a"]), Profile(), "Astronauta")


def test_evaluate_constraints():
    p = Profile(skills=[Skill("a")], screening=Screening(contract="CLT"))
    assert evaluate(Posting(title="T", skills=["a"], modality="presencial"), p, None).constraints_ok  # empty = any
    p.constraints = Constraints(modality=["remoto"])
    assert not evaluate(Posting(title="T", skills=["a"], modality="presencial"), p, None).constraints_ok
    assert evaluate(Posting(title="T", skills=["a"], modality="remoto", contract="CLT"), p, None).constraints_ok
    assert not evaluate(Posting(title="T", skills=["a"], contract="PJ"), p, None).constraints_ok
    p.screening.contract = "ambos"
    assert evaluate(Posting(title="T", skills=["a"], contract="PJ"), p, None).constraints_ok


def test_good_without_type_threshold_69_70():
    assert run(13, 9)[0].match == 69 and run(13, 9)[0].good_without_type is False
    assert run(10, 7)[0].match == 70 and run(10, 7)[0].good_without_type is True


def test_good_without_type_needs_salary_at_or_above_lowest_floor():
    assert run(10, 10, salary=4999)[0].good_without_type is False
    assert run(10, 10, salary=5000)[0].good_without_type is True


def test_good_without_type_needs_constraints():
    names, owned = skills(5, 5)
    p = Profile(skills=owned, constraints=Constraints(modality=["remoto"]))
    assert evaluate(Posting(title="T", skills=names, modality="presencial"), p, None).good_without_type is False


def test_evaluate_counts_confirmed_course_skills():
    names, owned = skills(4, 2)
    p = Profile(skills=owned, courses_done=[CourseDone(course="c", skills_claimed=["s2"])])
    assert evaluate(Posting(title="T", skills=names), p, None).match == 75


def test_adjacent_skills_raise_match_and_are_stretched_but_reported():
    p = Profile(skills=[Skill("SQL"), Skill("Power BI")], screening=Screening(salary_expectation=5000))
    ev = evaluate(Posting(title="T", skills=["SQL Server", "SSIS", "ETL", "Power BI"]), p, None)
    assert ev.match == 50 and ev.action == "esticar_marcado"
    assert ev.adjacent == {"SQL Server": "SQL"}
    assert set(ev.stretched) == {"SQL Server", "SSIS", "ETL"} and ev.missing == ["SSIS", "ETL"]


def test_adjacent_skills_in_a_risky_vacancy_are_reported_but_never_stretched():
    p = Profile(skills=[Skill("SQL")])
    ev = evaluate(Posting(title="T", skills=["SQL Server", "A", "B", "C", "D"]), p, None)
    assert ev.risky and ev.stretched == [] and ev.adjacent == {"SQL Server": "SQL"}


def test_onsite_allowed_only_from_min_salary():
    p = Profile(skills=[Skill("a")], constraints=Constraints(modality=["remoto", "hibrido"], onsite_min_salary=6000),
                screening=Screening(contract="CLT"))
    def ok(**kw):
        return evaluate(Posting(title="T", skills=["a"], **kw), p, None).constraints_ok
    assert ok(modality="presencial", salary=6500) and ok(modality="presencial")
    assert not ok(modality="presencial", salary=5000)
    assert ok(modality="remoto", salary=3000)


def test_estimate_used_when_posting_has_no_salary_and_flagged():
    ev, _ = run(10, 10, salary_estimate=4000, salary_source="Glassdoor, 2026-10-26")
    assert ev.below_floor is True and ev.salary_is_estimate is True
    assert "salário estimado (Glassdoor, 2026-10-26)" in ev.notes
    # the posting's own salary wins over an estimate
    ev, _ = run(10, 10, salary=6000, salary_estimate=1000, salary_source="x")
    assert ev.below_floor is False and ev.salary_is_estimate is False


def test_seniority_and_city_constraints():
    p = Profile(skills=[Skill("a")], constraints=Constraints(seniority=["junior", "pleno"],
                cities=["São Paulo", "Osasco"]), screening=Screening(contract="CLT"))
    def ok(**kw):
        return evaluate(Posting(title="T", skills=["a"], **kw), p, None).constraints_ok
    assert ok(level="junior") and ok(level="pleno") and ok()  # unknown level is not filtered out
    assert not ok(level="senior")
    assert ok(city="Osasco") and ok(city="são paulo") and not ok(city="São Bernardo do Campo")
    assert ok(city="São Bernardo do Campo", modality="remoto")


def test_measured_commute_replaces_the_city_list():
    p = Profile(skills=[Skill("a")], constraints=Constraints(cities=["São Paulo"], max_commute_minutes=120),
                screening=Screening(contract="CLT"))
    def ok(**kw):
        return evaluate(Posting(title="T", skills=["a"], **kw), p, None).constraints_ok
    assert ok(modality="hibrido", city="Barueri", commute_minutes=110)
    assert not ok(modality="hibrido", city="São Paulo", commute_minutes=130)
    assert not ok(modality="hibrido", city="Barueri")  # no measured trip yet: the city list applies
    assert ok(modality="remoto", city="Curitiba", commute_minutes=500)


def test_stretch_off_never_lists_missing_skills():
    names = ["a", "b", "c", "d", "e"]
    def ev(stretch):
        p = Profile(skills=[Skill(s) for s in names[:4]], stretch_policy=StretchPolicy(stretch=stretch),
                    screening=Screening(contract="CLT"))
        return evaluate(Posting(title="T", skills=names), p, None)
    assert ev(True).stretched == ["e"] and ev(False).stretched == [] and ev(False).missing == ["e"]
