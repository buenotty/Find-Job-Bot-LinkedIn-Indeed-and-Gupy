import os

import pytest

from jobbot import store
from jobbot.store import (
    STEPS, ProfileError, load_profile, next_step, profile_dir, put_step, save_profile, slugify,
)
from jobbot.schema import Profile

IDENT = {"name": "Ana", "age": 30, "state": "SP", "city": "São Paulo"}


def test_slugify_strips_accents():
    assert slugify("José da Silva") == "jose-da-silva"


def test_slugify_blocks_traversal(tmp_home):
    assert slugify("../../etc") == "etc"
    assert profile_dir("../../etc").parent == tmp_home / "profiles"


def test_slugify_empty_raises():
    with pytest.raises(ValueError):
        slugify("///")


def test_home_defaults_to_dot_jobbot(monkeypatch, tmp_path):
    monkeypatch.delenv("JOBBOT_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert store.home() == tmp_path / ".jobbot"


def test_two_profiles_isolated(tmp_home):
    put_step("Ana", "identidade", IDENT)
    put_step("Bia", "identidade", {**IDENT, "name": "Bia"})
    bia_file = profile_dir("Bia") / "profile.yaml"
    before = bia_file.read_text()
    put_step("Ana", "skills", {"skills": [{"name": "SQL", "level": "medio"}]})
    assert load_profile("Ana").name == "Ana"
    assert load_profile("Bia").skills == []
    assert bia_file.read_text() == before


def test_corrupt_yaml_raises_with_path_and_keeps_file(tmp_home):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    f.write_text("a: [")
    with pytest.raises(ProfileError, match="profile.yaml"):
        load_profile("Ana")
    with pytest.raises(ProfileError, match="profile.yaml"):
        put_step("Ana", "skills", {"skills": []})
    assert f.read_text() == "a: ["


def test_put_step_rejects_foreign_fields(tmp_home):
    with pytest.raises(ValueError):
        put_step("ana", "skills", {"age": 5})


def test_put_step_rejects_unknown_step(tmp_home):
    with pytest.raises(ValueError):
        put_step("ana", "inexistente", {})


def test_resume_walks_steps_in_order(tmp_home):
    assert next_step("Ana") == "identidade"
    put_step("Ana", "identidade", IDENT)
    put_step("Ana", "experiencias", {"experiences": [], "projects": []})
    assert next_step("Ana") == "skills"
    for step in STEPS[2:]:
        put_step("Ana", step, {})
    assert next_step("Ana") is None


def test_save_is_atomic(tmp_home, monkeypatch):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    before = f.read_text()

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        save_profile("Ana", Profile(name="Outra"))
    assert f.read_text() == before
    assert [p.name for p in f.parent.iterdir() if p.name.endswith(".tmp")] == []


def test_wrong_shaped_profile_raises_profile_error_with_path(tmp_home):
    put_step("Ana", "identidade", IDENT)
    (profile_dir("Ana") / "profile.yaml").write_text("skills: [Python]\n")
    with pytest.raises(ProfileError, match="profile.yaml"):
        load_profile("Ana")


def test_profile_files_are_private(tmp_home):
    put_step("Ana", "identidade", IDENT)
    d = profile_dir("Ana")
    assert d.stat().st_mode & 0o777 == 0o700
    assert (d / "profile.yaml").stat().st_mode & 0o777 == 0o600
    assert (d / "state.yaml").stat().st_mode & 0o777 == 0o600


def test_identity_collision_between_similar_names_is_refused(tmp_home):
    put_step("José", "identidade", {**IDENT, "name": "José"})
    with pytest.raises(ValueError, match="já existe"):
        put_step("Jose", "identidade", {**IDENT, "name": "Jose"})
    assert load_profile("José").name == "José"
    put_step("josé", "identidade", {**IDENT, "name": "josé"})  # same person, case only


from jobbot.store import append_record  # noqa: E402


def test_append_record_keeps_history(tmp_home):
    put_step("Ana", "identidade", IDENT)
    append_record("Ana", "assessments", {"date": "2026-10-01", "scores": {"a.b": 10}})
    append_record("Ana", "assessments", {"date": "2026-10-25", "scores": {"a.b": 20}})
    got = load_profile("Ana").assessments
    assert [a.date for a in got] == ["2026-10-01", "2026-10-25"]


def test_append_record_unknown_field_raises(tmp_home):
    put_step("Ana", "identidade", IDENT)
    with pytest.raises(ValueError):
        append_record("Ana", "skills", {"name": "SQL"})


def test_append_record_bad_record_raises_and_saves_nothing(tmp_home):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    before = f.read_text()
    with pytest.raises(ValueError, match="cargo"):
        append_record("Ana", "targets", {"cargo": "x"})
    assert f.read_text() == before


def test_append_record_on_corrupt_file_writes_nothing(tmp_home):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    f.write_text("a: [")
    with pytest.raises(ProfileError):
        append_record("Ana", "targets", {"role": "x"})
    assert f.read_text() == "a: ["


def test_append_record_does_not_touch_interview_state(tmp_home):
    put_step("Ana", "identidade", IDENT)
    before = next_step("Ana")
    append_record("Ana", "courses_done", {"course": "c"})
    assert next_step("Ana") == before


@pytest.mark.parametrize("field,record,match", [
    ("targets", {"role": "x", "source": "xyz"}, "origem"),
    ("targets", {"role": "x", "required_skills": "SQL"}, "required_skills"),
    ("courses_done", {"course": "c", "skills_claimed": [1, None]}, "skills_claimed"),
    ("assessments", {"date": "d", "situations": ["hello", 3]}, "situations"),
])
def test_append_record_rejects_invalid_records_and_saves_nothing(tmp_home, field, record, match):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    before = f.read_text()
    with pytest.raises(ValueError, match=match):
        append_record("Ana", field, record)
    assert f.read_text() == before


def test_append_record_refuses_nameless_profile(tmp_home):
    with pytest.raises(ValueError, match="nome"):
        append_record("Ghost", "targets", {"role": "x"})
    assert not (tmp_home / "profiles" / "ghost").exists()


from jobbot.store import upsert_job_type  # noqa: E402


def test_upsert_job_type_replaces_same_role_case_insensitive(tmp_home):
    put_step("Ana", "identidade", IDENT)
    upsert_job_type("Ana", {"role": "Analista de Dados", "salary_floor": 5000})
    upsert_job_type("Ana", {"role": "analista de dados", "salary_floor": 6000})
    types = load_profile("Ana").job_types
    assert len(types) == 1 and types[0].salary_floor == 6000


def test_upsert_job_type_rejects_invalid_and_saves_nothing(tmp_home):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    before = f.read_text()
    with pytest.raises(ValueError, match="contrato"):
        upsert_job_type("Ana", {"role": "x", "contract": "freela"})
    assert f.read_text() == before


def test_append_application_record(tmp_home):
    put_step("Ana", "identidade", IDENT)
    append_record("Ana", "applications", {"date": "2026-10-25", "company": "Acme", "mode": "tipo"})
    assert load_profile("Ana").applications[0].company == "Acme"


def test_atomic_write_accepts_bytes_and_str_with_private_mode(tmp_path):
    from jobbot.store import atomic_write
    atomic_write(tmp_path / "d" / "a.bin", b"\x00\x01")
    atomic_write(tmp_path / "d" / "b.txt", "olá")
    assert (tmp_path / "d" / "a.bin").read_bytes() == b"\x00\x01"
    assert (tmp_path / "d" / "b.txt").read_text(encoding="utf-8") == "olá"
    assert (tmp_path / "d" / "a.bin").stat().st_mode & 0o777 == 0o600


def test_education_is_saved_in_the_certifications_and_languages_step(tmp_home):
    put_step("Ana", "identidade", IDENT)
    put_step("Ana", "certificacoes_idiomas", {"education": [
        {"institution": "USJT", "course": "Sistemas", "level": "graduacao", "start": "2022", "status": "cursando"}]})
    assert load_profile("Ana").education[0].institution == "USJT"


from jobbot.store import update_profile  # noqa: E402


def test_update_profile_applies_and_saves(tmp_home):
    put_step("Ana", "identidade", IDENT)
    update_profile("Ana", lambda p: setattr(p.run, "per_round", 5))
    assert load_profile("Ana").run.per_round == 5


def test_update_profile_invalid_change_leaves_file_untouched(tmp_home):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    before = f.read_bytes()
    with pytest.raises(ValueError, match="per_round"):
        update_profile("Ana", lambda p: setattr(p.run, "per_round", 0))
    assert f.read_bytes() == before


def test_update_profile_on_corrupt_file_raises_profile_error(tmp_home):
    put_step("Ana", "identidade", IDENT)
    f = profile_dir("Ana") / "profile.yaml"
    f.write_text("a: [")
    with pytest.raises(ProfileError):
        update_profile("Ana", lambda p: None)
    assert f.read_text() == "a: ["


def test_update_profile_keeps_private_mode(tmp_home):
    put_step("Ana", "identidade", IDENT)
    update_profile("Ana", lambda p: setattr(p.run, "per_day", 20))
    assert (profile_dir("Ana") / "profile.yaml").stat().st_mode & 0o777 == 0o600
