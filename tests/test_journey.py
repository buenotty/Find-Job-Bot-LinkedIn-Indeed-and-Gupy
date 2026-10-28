from datetime import date

from jobbot.journey import STAGES, journey
from jobbot.schema import Application, Assessment, JobType, Target
from jobbot.store import STEPS, profile_dir, put_step, update_profile

IDENT = {"name": "Ana", "age": 30, "state": "SP", "city": "São Paulo"}


def finish_interview(name="Ana"):
    put_step(name, "identidade", IDENT)
    for step in STEPS[1:]:
        put_step(name, step, {})


def touch(name, filename):
    folder = profile_dir(name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / filename).write_text("x", encoding="utf-8")


def test_stage_order_and_skills():
    assert [s.skill for s in STAGES] == [
        "jobbot-interview", "jobbot-assessment", "jobbot-market", "jobbot-profiles",
        "jobbot-types", "jobbot-round"]


def test_new_person_starts_with_the_interview(tmp_home):
    j = journey("Ana")
    assert j.next_skill == "jobbot-interview" and not any(s.done for s in j.stages)


def test_incomplete_interview_keeps_the_interview_next(tmp_home):
    put_step("Ana", "identidade", IDENT)
    assert journey("Ana").next_skill == "jobbot-interview"


def test_each_stage_unlocks_the_next(tmp_home):
    finish_interview()
    assert journey("Ana").next_skill == "jobbot-assessment"
    update_profile("Ana", lambda p: p.assessments.append(Assessment("2026-10-25", {}, "alta")))
    assert journey("Ana").next_skill == "jobbot-market"
    touch("Ana", "focus-report.md")
    assert journey("Ana").next_skill == "jobbot-market"  # approved roles (targets) are part of this stage
    update_profile("Ana", lambda p: p.targets.append(Target(role="Analista", group="agora", source="sugerida")))
    assert journey("Ana").next_skill == "jobbot-profiles"
    touch("Ana", "perfis-revisados.md")
    assert journey("Ana").next_skill == "jobbot-types"


def test_types_stage_needs_a_pdf_for_every_type(tmp_home):
    finish_interview()
    for f in ("focus-report.md", "perfis-revisados.md"):
        touch("Ana", f)
    update_profile("Ana", lambda p: (
        p.assessments.append(Assessment("2026-10-25", {}, "alta")),
        p.targets.append(Target(role="Analista", group="agora", source="sugerida")),
        p.job_types.extend([JobType(role="Analista de Dados"), JobType(role="Técnico de Hardware")])))
    assert journey("Ana").next_skill == "jobbot-types"
    (profile_dir("Ana") / "types").mkdir()
    (profile_dir("Ana") / "types" / "analista-de-dados.pdf").write_bytes(b"%PDF")
    assert journey("Ana").next_skill == "jobbot-types"
    (profile_dir("Ana") / "types" / "tecnico-de-hardware.pdf").write_bytes(b"%PDF")
    assert journey("Ana").next_skill == "jobbot-round"


def test_after_the_first_round_the_round_stage_is_done_and_round_stays_next(tmp_home):
    finish_interview()
    for f in ("focus-report.md", "perfis-revisados.md"):
        touch("Ana", f)
    (profile_dir("Ana") / "types").mkdir()
    (profile_dir("Ana") / "types" / "analista.pdf").write_bytes(b"%PDF")
    update_profile("Ana", lambda p: (
        p.assessments.append(Assessment("2026-10-25", {}, "alta")),
        p.targets.append(Target(role="Analista", group="agora", source="sugerida")),
        p.job_types.append(JobType(role="Analista")),
        p.applications.append(Application(date="2026-10-25", platform="linkedin", status="preparado"))))
    j = journey("Ana")
    assert all(s.done for s in j.stages) and j.next_skill == "jobbot-round"
