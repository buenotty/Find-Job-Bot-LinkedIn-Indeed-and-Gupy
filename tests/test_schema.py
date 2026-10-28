from jobbot.schema import (
    Behavior, Bullet, Certification, Constraints, Experience, Language, Profile,
    Project, Screening, Skill, StretchPolicy, profile_from_dict, profile_to_dict,
    validate,
)


def full_profile():
    return Profile(
        name="Ana Souza", age=30, state="SP", city="São Paulo",
        experiences=[Experience("Acme", "Analista de Dados", "2020-01", None,
                                [Bullet("Criei dashboards", "40%")])],
        skills=[Skill("SQL", "especialista", "5 anos em produção")],
        certifications=[Certification("AWS CP", "AWS", 2023)],
        languages=[Language("Inglês", "Fluente")],
        projects=[Project("Bot", "Um bot", "https://x.dev")],
        constraints=Constraints(modality=["remoto"], cities=["São Paulo"],
                                vetoed_companies=["X"], vetoed_sectors=[],
                                current_employer="Acme"),
        screening=Screening(8000, "CLT", "imediata", "a@b.com", "11999999999", {"SQL": 5.0}),
        behavior=Behavior("autônoma", ["aprender"], "especialista"),
        stretch_policy=StretchPolicy(90, 50),
    )


def student_profile():
    return Profile(
        name="Caio Aluno", age=20, state="MG", city="Belo Horizonte",
        skills=[Skill("Python", "iniciante")],
        projects=[Project("Clone", "Clone de app")],
    )


def test_roundtrip():
    p = full_profile()
    assert profile_from_dict(profile_to_dict(p)) == p


def test_partial_profile_loads():
    assert profile_from_dict({"name": "Ana"}).experiences == []


def test_unknown_keys_ignored():
    assert profile_from_dict({"name": "Ana", "zzz": 1}).name == "Ana"


def test_validate_accepts_full_profile():
    assert validate(full_profile()) == []


def test_validate_flags_bad_level():
    p = student_profile()
    p.skills = [Skill("SQL", "guru")]
    assert any("nível" in e for e in validate(p))


def test_validate_flags_bad_contract():
    p = full_profile()
    p.screening.contract = "freela"
    assert any("contrato" in e for e in validate(p))


def test_validate_accepts_no_experience():
    assert validate(student_profile()) == []


def test_nested_unknown_key_raises():
    import pytest
    with pytest.raises(ValueError, match="nome"):
        profile_from_dict({"skills": [{"nome": "SQL", "nivel": "especialista"}]})
    with pytest.raises(ValueError, match="empresa"):
        profile_from_dict({"experiences": [{"empresa": "X"}]})


def test_wrong_shape_raises_value_error():
    import pytest
    with pytest.raises(ValueError):
        profile_from_dict({"skills": ["Python"]})
    with pytest.raises(ValueError):
        profile_from_dict({"experiences": {"company": "X"}})


def test_null_list_is_empty():
    assert profile_from_dict({"experiences": None}).experiences == []


def test_validate_flags_empty_names():
    p = student_profile()
    p.skills = [Skill("", "medio")]
    p.experiences = [Experience("", "Analista", "2020-01", None, [])]
    errors = validate(p)
    assert any("skill sem nome" in e for e in errors)
    assert any("empresa" in e for e in errors)


from jobbot.schema import Assessment, CourseDone, Target  # noqa: E402


def b1_profile():
    p = full_profile()
    p.assessments = [Assessment("2026-10-25", {"interesses.pratico": 80}, "alta", [], [{"pergunta": "q", "resposta": "r"}])]
    p.targets = [Target("Analista de Dados", "agora", "sugerida", ["SQL"], 100, "2026-10-25", "pronto")]
    p.courses_done = [CourseDone("SQL Avançado", "Plataforma X", "2026-10-20", ["SQL"], "projeto final")]
    p.cheap_course_max = 150
    return p


def test_a_profile_without_b1_fields_loads_and_validates():
    p = profile_from_dict({"name": "Ana", "age": 30})
    assert p.assessments == [] and p.targets == [] and p.courses_done == []
    assert p.cheap_course_max == 200
    assert validate(p) == []


def test_b1_roundtrip():
    p = b1_profile()
    assert profile_from_dict(profile_to_dict(p)) == p
    assert validate(p) == []


def test_validate_flags_bad_group_source_status_reliability():
    p = b1_profile()
    p.targets[0].group = "x"
    p.targets[0].source = "y"
    p.targets[0].status = "z"
    p.assessments[0].confiabilidade = "media"
    errors = " | ".join(validate(p))
    assert "grupo" in errors and "origem" in errors and "status" in errors and "confiabilidade" in errors


def test_validate_flags_negative_cheap_max():
    p = b1_profile()
    p.cheap_course_max = -1
    assert any("cheap_course_max" in e for e in validate(p))


def test_nested_unknown_key_in_target_raises():
    import pytest
    with pytest.raises(ValueError, match="cargo"):
        profile_from_dict({"targets": [{"cargo": "x"}]})


from jobbot.schema import Application, JobType, Project  # noqa: E402


def b2_profile():
    p = b1_profile()
    p.projects = [Project("Montagem de PCs", "Monto computadores", None, "autodidata", "2022-03", None)]
    p.job_types = [JobType("Analista de Dados", 5000, ["hibrido"], "CLT", ["SQL"])]
    p.applications = [Application("2026-10-25", "https://x", "Acme", "Analista", "Analista de Dados",
                                  "tipo", 80, "Ótimo match", False, False, "resumes/a.pdf")]
    return p


def test_a_and_b1_profiles_load_without_b2_fields():
    p = profile_from_dict({"name": "Ana", "projects": [{"name": "x", "description": "y"}]})
    assert p.job_types == [] and p.applications == [] and p.projects[0].kind == "projeto"
    assert validate(p) == []


def test_b2_roundtrip():
    p = b2_profile()
    assert profile_from_dict(profile_to_dict(p)) == p
    assert validate(p) == []


def test_validate_flags_bad_kind_mode_contract_floor():
    p = b2_profile()
    p.projects[0].kind = "hobby"
    p.applications[0].mode = "x"
    p.job_types[0].contract = "freela"
    p.job_types[0].salary_floor = -1
    p.job_types[0].keywords = [1]
    errors = " | ".join(validate(p))
    for word in ("kind", "modo", "contrato", "piso", "keywords"):
        assert word in errors, word


def test_nested_unknown_key_in_job_type_raises():
    import pytest
    with pytest.raises(ValueError, match="cargo"):
        profile_from_dict({"job_types": [{"cargo": "x"}]})


from jobbot.schema import Education  # noqa: E402


def test_education_roundtrip_and_old_profiles_load():
    p = full_profile()
    p.education = [Education("USJT", "Análise e Desenvolvimento de Sistemas", "graduacao", "2022", None, "cursando")]
    assert profile_from_dict(profile_to_dict(p)) == p and validate(p) == []
    assert profile_from_dict({"name": "Ana"}).education == []


def test_validate_flags_bad_education_level_status_and_missing_course():
    p = full_profile()
    p.education = [Education("X", "", "doutorzinho", "2020", None, "quase")]
    errors = " | ".join(validate(p))
    assert "nível" in errors and "situação" in errors and "curso" in errors


from jobbot.schema import AnswerEntry, PendingQuestion, PlatformState, RunSettings, SeenPosting  # noqa: E402


def c_profile():
    p = b2_profile()
    p.applications[0].platform = "linkedin"
    p.seen = [SeenPosting("k", "a|b", "linkedin", "Acme", "Analista", "https://x", "preparada", "2026-10-25")]
    p.answers = [AnswerEntry("Pretensão salarial", "8000", "geral", False)]
    p.pending = [PendingQuestion("Qual a sua cor?", "sensivel", "Analista@Acme", "2026-10-25")]
    p.platforms = [PlatformState("linkedin", True, "captcha", "2026-10-25")]
    return p


def test_b2_profiles_load_without_c_fields():
    p = profile_from_dict({"name": "Ana", "applications": [{"company": "X", "status": "preparado"}]})
    assert p.run == RunSettings() and p.seen == [] and p.answers == [] and p.pending == [] and p.platforms == []
    assert p.applications[0].platform == "" and validate(p) == []


def test_c_roundtrip():
    p = c_profile()
    assert profile_from_dict(profile_to_dict(p)) == p
    assert validate(p) == []


def test_run_defaults():
    r = RunSettings()
    assert (r.per_round, r.per_day, r.max_examined, r.fit_mode) == (10, 30, 50, "auto")


import pytest  # noqa: E402


@pytest.mark.parametrize("mutate,word", [
    (lambda p: setattr(p.applications[0], "status", "x"), "status"),
    (lambda p: setattr(p.applications[0], "platform", "orkut"), "plataforma"),
    (lambda p: setattr(p.seen[0], "reason", "x"), "motivo"),
    (lambda p: setattr(p.seen[0], "platform", "orkut"), "plataforma"),
    (lambda p: setattr(p.answers[0], "category", "x"), "categoria"),
    (lambda p: setattr(p.platforms[0], "platform", "orkut"), "plataforma"),
    (lambda p: setattr(p.run, "per_round", 0), "per_round"),
    (lambda p: setattr(p.run, "per_day", -1), "per_day"),
    (lambda p: setattr(p.run, "max_examined", 0), "max_examined"),
    (lambda p: setattr(p.run, "fit_mode", "sempre"), "fit_mode"),
])
def test_validate_flags_bad_c_values(mutate, word):
    p = c_profile()
    mutate(p)
    assert any(word in e for e in validate(p)), validate(p)


def test_nested_unknown_key_in_answer_raises():
    with pytest.raises(ValueError, match="pergunta"):
        profile_from_dict({"answers": [{"pergunta": "x"}]})


def test_education_line_without_a_start_shows_only_the_end_year():
    from jobbot.schema import Education, education_line

    assert education_line(Education("Colégio X", "", "medio", "", "2022", "concluido")) == "Ensino médio - Colégio X (2022)"
