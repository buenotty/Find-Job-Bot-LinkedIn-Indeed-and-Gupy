import pytest

from jobbot.jobtypes import (
    Rules, effective_rules, find_type, releasable_targets, validate_new_type,
)
from jobbot.schema import Constraints, JobType, Profile, Screening, Skill, Target


def target(role, group, skills=()):
    return Target(role=role, group=group, source="sugerida", required_skills=list(skills))


def person(skills=("SQL", "Power BI"), targets=(), **kw):
    return Profile(
        skills=[Skill(s) for s in skills], targets=list(targets),
        constraints=Constraints(modality=["remoto"]),
        screening=Screening(salary_expectation=8000, contract="CLT"), **kw)


def test_effective_rules_fall_back_to_profile():
    r = effective_rules(JobType(role="x"), person())
    assert r == Rules(salary_floor=8000, modality=["remoto"], contract="CLT")


def test_effective_rules_override_wins():
    jt = JobType(role="x", salary_floor=3000, modality=["presencial"], contract="PJ")
    assert effective_rules(jt, person()) == Rules(3000, ["presencial"], "PJ")


def test_effective_rules_zero_floor_is_a_real_floor():
    assert effective_rules(JobType(role="x", salary_floor=0), person()).salary_floor == 0


def test_releasable_agora_and_cutoff_for_nova_formacao():
    required = [f"s{i}" for i in range(10)]
    nine = person(skills=[f"s{i}" for i in range(9)], targets=[
        target("Agora", "agora", ["s0"]), target("Quase", "nova_formacao", required), target("Sem", "sem_dado")])
    assert [t.role for t in releasable_targets(nine)] == ["Agora", "Quase"]
    eight = person(skills=[f"s{i}" for i in range(8)], targets=[target("Quase", "nova_formacao", required)])
    assert releasable_targets(eight) == []


def test_no_targets_means_no_releasable():
    assert releasable_targets(person()) == []


def test_validate_new_type_rejects_unreleasable_role():
    p = person(targets=[target("Sem", "sem_dado")])
    with pytest.raises(ValueError, match="liberada"):
        validate_new_type(p, {"role": "Sem"})
    with pytest.raises(ValueError, match="liberada"):
        validate_new_type(p, {"role": "Inexistente"})


def test_validate_new_type_accepts_releasable_role():
    p = person(targets=[target("Analista", "agora", ["SQL"])])
    assert validate_new_type(p, {"role": "analista", "salary_floor": 5000})["role"] == "analista"


def test_find_type_case_insensitive():
    p = person(job_types=[JobType(role="Analista de Dados")])
    assert find_type(p, "analista DE dados").role == "Analista de Dados"
    assert find_type(p, "outro") is None
