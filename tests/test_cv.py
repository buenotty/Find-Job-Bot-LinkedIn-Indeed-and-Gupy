from datetime import date

import pytest

from jobbot.cv import render_base_cv
from jobbot.honesty import HonestyError
from jobbot.schema import Experience, Skill
from tests.test_schema import full_profile, student_profile

TODAY = date(2027, 3, 1)


def test_cv_without_experience_renders_projects_and_skills():
    out = render_base_cv(student_profile(), "Estudante em busca do primeiro emprego.", TODAY)
    assert "## Projetos" in out and "## Competências" in out
    assert "## Experiência" not in out


def test_cv_omits_empty_sections():
    out = render_base_cv(student_profile(), "", TODAY)
    assert "## Resumo" not in out
    assert "## Certificações" not in out and "## Idiomas" not in out


def test_cv_rejects_unsupported_number():
    with pytest.raises(HonestyError, match="70%"):
        render_base_cv(full_profile(), "Reduzi 70% dos custos.", TODAY)


def test_cv_skill_order_by_level():
    p = full_profile()
    p.skills = [Skill("Excel", "iniciante"), Skill("SQL", "especialista"), Skill("Python", "medio")]
    out = render_base_cv(p, "", TODAY)
    assert out.index("SQL") < out.index("Python") < out.index("Excel")


def test_cv_uses_only_profile_employers():
    p = full_profile()
    p.experiences.append(Experience("Beta Ltda", "Analista", "2018-02", "2019-12"))
    out = render_base_cv(p, "", TODAY)
    headings = [l for l in out.splitlines() if l.startswith("### ")]
    assert {h.split(" — ")[1] for h in headings} == {"Acme", "Beta Ltda"}


def test_cv_header_has_name_and_contact():
    out = render_base_cv(full_profile(), "", TODAY)
    assert out.startswith("# Ana Souza")
    assert "a@b.com" in out and "São Paulo" in out


def test_base_cv_shows_education_section():
    from jobbot.schema import Education
    p = full_profile()
    p.education = [Education("USJT", "Sistemas", "graduacao", "2022", None, "cursando")]
    out = render_base_cv(p, "", TODAY)
    assert "## Formação" in out and "Graduação em Sistemas - USJT (2022 - cursando)" in out
    assert "## Formação" not in render_base_cv(full_profile(), "", TODAY)
