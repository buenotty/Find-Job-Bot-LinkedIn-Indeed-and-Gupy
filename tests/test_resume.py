from datetime import date

import pytest

from jobbot.evaluate import Evaluation
from jobbot.honesty import HonestyError
from jobbot.posting import Posting
from jobbot.resume import (
    SECTION_TITLES, SUMMARY_MAX, ResumeContent, build_resume, content_from_dict, doc_text,
    merge_content, review_sheet,
)
from jobbot.schema import (
    Bullet, Certification, Education, Experience, Language, Profile, Project, Screening, Skill,
)

TODAY = date(2026, 10, 25)


def person(**kw):
    base = dict(
        name="Maria Exemplo", city="Rio de Janeiro", state="RJ",
        experiences=[Experience("Loja Modelo", "Analista de Dados", "2021-02", None,
                                [Bullet("Automatizei relatórios semanais", "30%")])],
        skills=[Skill("SQL", "especialista"), Skill("Python", "medio"), Skill("Excel", "iniciante")],
        projects=[Project("Montagem de PCs", "Monto computadores", None, "autodidata", "2022-03", None),
                  Project("Painel de vendas", "Painel com dados públicos")],
        education=[Education("USJT", "Análise e Desenvolvimento de Sistemas", "graduacao", "2022", None, "cursando")],
        certifications=[Certification("Fundamentos de Dados", "Plataforma Exemplo", 2022)],
        languages=[Language("Inglês", "Profissional")],
        screening=Screening(email="m@example.com", phone="21999990000"),
    )
    base.update(kw)
    return Profile(**base)


def build(content=None, stretched=(), **kw):
    return build_resume(person(**kw), content or ResumeContent(), list(stretched), TODAY)


def test_experience_and_certification_come_only_from_profile():
    doc = build(ResumeContent(experience_bullets={"Loja Modelo": ["Reduzi retrabalho em 30%"]}))
    text = doc_text(doc)
    assert "Analista de Dados - Loja Modelo (2021-02 - Atual)" in text
    assert "- Fundamentos de Dados - Plataforma Exemplo (2022)" in text
    assert "Reduzi retrabalho em 30%" in text


def test_bullet_key_for_unknown_company_or_project_is_rejected():
    with pytest.raises(HonestyError, match="Empresa Inventada"):
        build(ResumeContent(experience_bullets={"Empresa Inventada": ["x"]}))
    with pytest.raises(HonestyError, match="Projeto Fantasma"):
        build(ResumeContent(project_bullets={"Projeto Fantasma": ["x"]}))


def test_unsupported_number_in_bullet_or_summary_rejected():
    with pytest.raises(HonestyError, match="70%"):
        build(ResumeContent(experience_bullets={"Loja Modelo": ["Cortei custos em 70%"]}))
    with pytest.raises(HonestyError, match="9"):
        build(ResumeContent(summary="Analista com 9 anos de experiência."))


def test_summary_over_limit_rejected():
    with pytest.raises(ValueError, match="resumo"):
        build(ResumeContent(summary="x" * (SUMMARY_MAX + 1)))
    build(ResumeContent(summary="x" * SUMMARY_MAX))


def test_stretched_skill_in_summary_or_bullet_rejected():
    with pytest.raises(HonestyError, match="Kafka"):
        build(ResumeContent(summary="Experiência com kafka e SQL."), stretched=["Kafka"])
    with pytest.raises(HonestyError, match="Kafka"):
        build(ResumeContent(project_bullets={"Painel de vendas": ["Integrei Kafka"]}), stretched=["Kafka"])


def test_stretched_skill_listed_last_without_level():
    doc = build(ResumeContent(skill_order=["Python"]), stretched=["Kafka"])
    assert doc.skills == ["Python", "SQL", "Excel", "Kafka"]
    assert "especialista" not in doc_text(doc).lower() and "Kafka" in doc_text(doc).split("Competências")[1]


def test_skill_order_ignores_unowned_and_never_duplicates():
    doc = build(ResumeContent(skill_order=["Rust", "python", "Python"]), stretched=["SQL"])
    assert doc.skills == ["Python", "SQL", "Excel"]


def test_no_experience_renders_projects_section_only():
    text = doc_text(build(experiences=[]))
    assert "Projetos e voluntariado" in text and "Experiência" not in text


@pytest.mark.parametrize("kind,start,label", [
    ("autodidata", "2022-03", "Autodidata desde 2022"), ("autodidata", "", "Autodidata"),
    ("voluntariado", "", "Voluntariado"), ("voluntariado", "2020", "Voluntariado desde 2020"),
    ("freela", "", "Freela"), ("projeto", "2021", None),
])
def test_project_kind_labels(kind, start, label):
    doc = build(projects=[Project("P", "desc", None, kind, start, None)])
    got = doc.projects[0]["label"]
    assert got == label if label else not got


def test_empty_sections_omitted_and_headings_exact():
    text = doc_text(build(certifications=[], languages=[], projects=[], experiences=[]))
    for gone in ("Certificações", "Idiomas", "Projetos e voluntariado", "Experiência", "Resumo"):
        assert gone not in text
    full = doc_text(build(ResumeContent(summary="Resumo curto.")))
    headings = [l for l in full.splitlines() if l in SECTION_TITLES]
    assert headings == list(SECTION_TITLES)


def test_content_from_dict_rejects_unknown_key_and_bad_shape():
    with pytest.raises(ValueError, match="resumo"):
        content_from_dict({"resumo": "x"})
    with pytest.raises(ValueError):
        content_from_dict({"experience_bullets": {"A": "not a list"}})
    with pytest.raises(ValueError):
        content_from_dict({"skill_order": "SQL"})
    assert content_from_dict({"summary": "x"}).summary == "x"


def test_merge_content_override_wins_only_when_set():
    base = ResumeContent(summary="base", skill_order=["A"], experience_bullets={"X": ["1"]})
    merged = merge_content(base, ResumeContent(summary="novo"))
    assert (merged.summary, merged.skill_order, merged.experience_bullets) == ("novo", ["A"], {"X": ["1"]})
    assert merge_content(base, ResumeContent(skill_order=["B"])).skill_order == ["B"]


def ev(**kw):
    base = dict(match=60, label="Chance média", action="esticar_marcado", missing=["Kafka"], stretched=["Kafka"],
                risky=False, below_floor=True, constraints_ok=True, good_without_type=False, notes=["salário não informado"])
    base.update(kw)
    return Evaluation(**base)


def test_review_sheet_lists_stretched_missing_and_floor():
    posting = Posting(title="Analista", company="Acme", salary=4000, url="https://x/1")
    text = review_sheet(posting, ev(), "Analista de Dados", "tipo", 5000)
    assert "Kafka" in text and "podem ser perguntadas na entrevista" in text
    assert "abaixo do piso" in text.lower() and "4000" in text and "5000" in text
    assert "https://x/1" in text and "Chance média" in text
    risky = review_sheet(posting, ev(risky=True, stretched=[], missing=["Kafka", "Spark"], match=30, label="Arriscado"),
                         None, "do_zero", None)
    assert "sem tipo" in risky.lower() and "Spark" in risky and "arriscada" in risky.lower()


def test_risky_vacancy_has_no_stretched_in_doc():
    assert "Kafka" not in doc_text(build(stretched=[]))


def test_project_bullets_select_and_order_projects():
    doc = build(ResumeContent(project_bullets={"Painel de vendas": ["Montei o painel com dados públicos"]}))
    assert [x["name"] for x in doc.projects] == ["Painel de vendas"]
    both = build(ResumeContent(project_bullets={"Painel de vendas": ["a"], "Montagem de PCs": ["b"]}))
    assert [x["name"] for x in both.projects] == ["Painel de vendas", "Montagem de PCs"]


def test_no_project_bullets_means_all_projects():
    assert [x["name"] for x in build().projects] == ["Montagem de PCs", "Painel de vendas"]


def test_risky_missing_skill_in_text_is_rejected_even_without_stretch():
    content = ResumeContent(summary="Analista com experiência em Kafka e SQL.")
    with pytest.raises(HonestyError, match="Kafka"):
        build_resume(person(), content, [], TODAY, missing=["Kafka", "Spark"])
    assert build_resume(person(), content, [], TODAY).summary  # no missing list given: nothing to check


def test_leak_check_catches_skill_inside_longer_word_but_not_short_skill_in_other_word():
    with pytest.raises(HonestyError, match="Kafka"):
        build(ResumeContent(summary="Kafkaizou pipelines inteiros."), stretched=["Kafka"])
    with pytest.raises(HonestyError, match="Docker"):
        build(ResumeContent(summary="Fiz a dockerização do ambiente."), stretched=["Docker"])
    build(ResumeContent(summary="Cuidei do gopher interno."), stretched=["Go"])  # short skill: whole word only
    with pytest.raises(HonestyError, match="Go"):
        build(ResumeContent(summary="Experiência com Go e SQL."), stretched=["Go"])


def test_education_rendered_from_profile_after_competencias():
    text = doc_text(build())
    assert "Formação" in text
    assert text.index("Competências") < text.index("Formação") < text.index("Certificações")
    assert "- Graduação em Análise e Desenvolvimento de Sistemas - USJT (2022 - cursando)" in text


def test_education_levels_render_labels_and_omit_when_empty():
    levels = [Education("Colégio X", "", "medio", "2015", "2017", "concluido"),
              Education("Y", "Redes", "tecnico", "2018", "2019", "concluido"),
              Education("Z", "Dados", "pos", "2024", None, "cursando")]
    text = doc_text(build(education=levels))
    assert "- Ensino médio - Colégio X (2015 - 2017)" in text
    assert "- Técnico em Redes - Y (2018 - 2019)" in text
    assert "- Pós-graduação em Dados - Z (2024 - cursando)" in text
    assert "Formação" not in doc_text(build(education=[]))


def test_adjacent_skill_named_in_text_is_rejected_via_the_forbidden_list():
    with pytest.raises(HonestyError, match="SQL Server"):
        build_resume(person(), ResumeContent(summary="Experiência com SQL Server."), [], TODAY, missing=["SQL Server"])


def test_review_sheet_lists_adjacent_skills():
    posting = Posting(title="Analista", company="Acme")
    sheet = review_sheet(posting, ev(adjacent={"SQL Server": "SQL"}), "Analista de Dados", "tipo", 5000)
    assert "SQL Server" in sheet and "você tem SQL" in sheet


def test_experience_bullets_select_which_jobs_appear():
    from datetime import date

    from jobbot.resume import ResumeContent, build_resume
    from jobbot.schema import Bullet, Experience, Profile

    p = Profile(name="A", experiences=[Experience("Velha SA", "Técnico", "2020-01", "2021-01", [Bullet("x", None)]),
                                       Experience("Nova SA", "Analista", "2021-02", None, [Bullet("y", None)])])
    assert [e["company"] for e in build_resume(p, ResumeContent(), [], date(2026, 1, 1)).experiences] == ["Velha SA", "Nova SA"]
    only_new = ResumeContent(experience_bullets={"Nova SA": ["Fiz y"]})
    assert [e["company"] for e in build_resume(p, only_new, [], date(2026, 1, 1)).experiences] == ["Nova SA"]


def test_show_projects_false_drops_the_section():
    from datetime import date

    from jobbot.resume import ResumeContent, build_resume, content_from_dict
    from jobbot.schema import Profile, Project

    p = Profile(name="A", projects=[Project("P", "d", None, "autodidata", "2022", None)])
    assert len(build_resume(p, ResumeContent(), [], date(2026, 1, 1)).projects) == 1
    assert build_resume(p, ResumeContent(show_projects=False), [], date(2026, 1, 1)).projects == []
    assert content_from_dict({"show_projects": False}).show_projects is False
    import pytest
    with pytest.raises(ValueError):
        content_from_dict({"show_projects": "nao"})


def test_skill_groups_only_accept_owned_skills_and_stretched_go_in_their_own_group():
    from datetime import date

    import pytest

    from jobbot.honesty import HonestyError
    from jobbot.resume import ResumeContent, build_resume
    from jobbot.schema import Profile, Skill

    p = Profile(name="A", linkedin="https://www.linkedin.com/in/a/", skills=[Skill("SQL", "medio"), Skill("Python", "iniciante")])
    ok = ResumeContent(skill_groups={"Dados": ["sql"], "Código": ["Python"]})
    doc = build_resume(p, ok, ["Kafka"], date(2026, 1, 1))
    assert doc.skill_groups == [("Dados", ["SQL"]), ("Código", ["Python"]), ("Também", ["Kafka"])]
    assert "linkedin.com/in/a" in doc.contact and "https" not in doc.contact
    with pytest.raises(HonestyError):
        build_resume(p, ResumeContent(skill_groups={"Dados": ["Spark"]}), [], date(2026, 1, 1))
