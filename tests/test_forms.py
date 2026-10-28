from pathlib import Path

import pytest

from jobbot.forms import interview_form, parse_interview

FIXTURE = Path(__file__).parent / "fixtures" / "maria" / "questionario.txt"


def parsed():
    data, errors = parse_interview(FIXTURE.read_text(encoding="utf-8"))
    assert errors == [], errors
    return data


def test_blank_form_lists_every_section_and_parses_to_nothing():
    text = interview_form()
    assert text.startswith("# JOBBOT:interview")
    for n in range(1, 8):
        assert f"## {n}." in text
    data, errors = parse_interview(text)
    assert data == {} and errors == []


def test_identity():
    assert parsed()["identidade"] == {"name": "Maria Exemplo", "age": 28, "state": "RJ", "city": "Rio de Janeiro"}


def test_experiences_and_projects():
    step = parsed()["experiencias"]
    exp = step["experiences"][0]
    assert (exp["company"], exp["role"], exp["start"], exp["end"]) == ("Loja Modelo", "Analista de Dados", "2021-02", None)
    assert exp["bullets"] == [{"text": "Automatizei relatórios semanais de vendas", "metric": "30%"},
                              {"text": "Criei painéis de acompanhamento", "metric": None}]
    proj = step["projects"][0]
    assert (proj["name"], proj["kind"], proj["start"], proj["end"]) == ("Montagem de PCs", "autodidata", "2022", None)
    assert proj["description"] == "Montagem e upgrade de computadores para amigos" and proj["url"] is None


def test_skills_levels_accept_accents_and_blank_evidence():
    skills = parsed()["skills"]["skills"]
    assert skills == [{"name": "SQL", "level": "especialista", "evidence": "uso diário há 4 anos"},
                      {"name": "Python", "level": "medio", "evidence": "scripts de limpeza de dados"},
                      {"name": "Excel", "level": "iniciante", "evidence": ""}]


def test_certifications_languages_education():
    step = parsed()["certificacoes_idiomas"]
    assert step["certifications"] == [{"name": "Fundamentos de Dados", "issuer": "Plataforma Exemplo", "year": 2022}]
    assert step["languages"] == [{"name": "Inglês", "level": "Profissional"}]
    assert step["education"] == [{"institution": "USJT", "course": "Análise e Desenvolvimento de Sistemas",
                                  "level": "graduacao", "start": "2022", "end": None, "status": "cursando"}]


def test_constraints_normalize_modality_and_lists():
    c = parsed()["restricoes"]["constraints"]
    assert c["modality"] == ["remoto", "hibrido"] and c["cities"] == ["Rio de Janeiro"]
    assert c["vetoed_companies"] == ["Empresa Vetada"] and c["vetoed_sectors"] == []
    assert c["current_employer"] == "Loja Modelo"


def test_screening_with_decimal_comma():
    s = parsed()["triagem"]["screening"]
    assert s["salary_expectation"] == 7000 and s["contract"] == "CLT" and s["availability"] == "30 dias"
    assert s["email"] == "maria@example.com" and s["phone"] == "21999990000"
    assert s["years_by_skill"] == {"SQL": 4.0, "Python": 2.5}


def test_behavior_track_from_choices():
    b = parsed()["comportamento"]["behavior"]
    assert b["track"] == "especialista" and b["work_style"].startswith("Autonomia")
    assert b["motivators"] == ["aprender", "impacto", "estabilidade"]


def edit(old, new):
    return FIXTURE.read_text(encoding="utf-8").replace(old, new, 1)


@pytest.mark.parametrize("old,new,needle", [
    ("Idade: 28", "Idade: vinte", "idade"),
    ("- Python | médio |", "- Python | guru |", "nível"),
    ("graduacao | 2022", "licenciatura | 2022", "nível"),
    ("| cursando", "| quase", "situação"),
    ("Contrato: CLT", "Contrato: freela", "contrato"),
    ("Pretensão salarial: 7000", "Pretensão salarial: muito", "pretensão"),
    ("Escolha 3: B", "Escolha 3: C", "escolha"),
    ("- SQL | 4", "- SQL | muitos", "anos"),
    ("Tipo: autodidata", "Tipo: hobby", "tipo"),
])
def test_errors_name_the_line_and_the_problem(old, new, needle):
    data, errors = parse_interview(edit(old, new))
    assert errors and all(e.startswith("linha ") for e in errors)
    assert any(needle in e.lower() for e in errors), errors


def test_missing_name_is_an_error_when_identity_is_partly_filled():
    data, errors = parse_interview(edit("Nome completo: Maria Exemplo", "Nome completo:"))
    assert any("nome" in e.lower() for e in errors)


def test_unknown_label_is_reported_not_ignored():
    data, errors = parse_interview(edit("Cidade: Rio de Janeiro", "Cidadee: Rio de Janeiro"))
    assert any("cidadee" in e.lower() for e in errors)


def test_a_wrong_marker_is_rejected():
    data, errors = parse_interview("# JOBBOT:teste\n")
    assert errors and "interview" in errors[0]


from jobbot.assessment import load_bank  # noqa: E402
from jobbot.forms import (  # noqa: E402
    SITUATION_QUESTIONS, apply_followup, assessment_form, followup_form, parse_assessment, parse_followup,
)
from jobbot.schema import Bullet, Experience, Profile, Skill  # noqa: E402


def test_assessment_form_has_every_item_and_the_open_questions():
    bank = load_bank()
    text = assessment_form(bank)
    assert text.startswith("# JOBBOT:teste")
    assert sum(1 for l in text.splitlines() if l.rstrip().endswith("| =")) == len(bank)
    for layer in ("VALORES", "INTERESSES", "PERSONALIDADE", "PERGUNTAS ABERTAS"):
        assert f"## {layer}" in text
    assert len(SITUATION_QUESTIONS) == 3 and all(f"Pergunta {i}:" in text for i in range(1, 4))


def fill(text, ids_to_value):
    out = []
    for line in text.splitlines():
        first = line.split("|")[0].strip()
        if first in ids_to_value and line.rstrip().endswith("| ="):
            line = line.rstrip() + f" {ids_to_value[first]}"
        out.append(line)
    return "\n".join(out)


def test_parse_assessment_blank_partial_and_errors():
    bank = load_bank()
    blank = assessment_form(bank)
    assert parse_assessment(blank, bank) == ({}, [], [])
    ids = [i.id for i in bank]
    answers, situations, errors = parse_assessment(fill(blank, {ids[0]: 4, ids[1]: 5}), bank)
    assert answers == {ids[0]: 4, ids[1]: 5} and errors == []
    _, _, errors = parse_assessment(fill(blank, {ids[0]: 7}), bank)
    assert errors and errors[0].startswith("linha ") and ids[0] in errors[0]
    _, _, errors = parse_assessment(blank.replace("# TESTE", "# TESTE\nzzz99 | item inventado | = 3", 1), bank)
    assert any("zzz99" in e for e in errors)


def test_parse_assessment_open_questions_with_multiline_answers():
    bank = load_bank()
    text = assessment_form(bank).replace("Resposta:", "Resposta: Automatizei os relatórios da loja.\nFoi um trabalho de dois meses.", 1)
    _, situations, errors = parse_assessment(text, bank)
    assert errors == [] and len(situations) == 1
    assert situations[0]["pergunta"] == SITUATION_QUESTIONS[0]
    assert situations[0]["resposta"] == "Automatizei os relatórios da loja. Foi um trabalho de dois meses."


def gap_profile():
    return Profile(
        name="Ana", skills=[Skill("SQL", "especialista"), Skill("Python", "medio", "scripts"), Skill("Excel", "iniciante")],
        experiences=[Experience("Acme", "Analista", "2021-01", None, [Bullet("Criei painéis"), Bullet("Reduzi custos", "10%")])])


def test_followup_lists_only_real_gaps():
    text = followup_form(gap_profile())
    assert text.startswith("# JOBBOT:followup")
    assert "@evidence:SQL" in text and "@evidence:Python" not in text and "@evidence:Excel" not in text
    assert "@metric:0:0" in text and "@metric:0:1" not in text
    for field in ("age", "state", "city", "salary_expectation", "email", "phone"):
        assert f"@field:{field}" in text


def test_followup_is_none_when_nothing_is_missing():
    p = gap_profile()
    p.age, p.state, p.city = 30, "SP", "São Paulo"
    p.screening.salary_expectation, p.screening.email, p.screening.phone = 5000, "a@b.com", "11999999999"
    p.skills[0].evidence = "4 anos"
    p.experiences[0].bullets[0].metric = "20%"
    assert followup_form(p) is None


def test_apply_followup_fills_fields_and_reports_bad_numbers():
    text = followup_form(gap_profile())
    text = text.replace("@evidence:SQL |", "@evidence:SQL |", 1)
    lines = []
    for line in text.splitlines():
        if line.startswith("@evidence:SQL"):
            line = line.rstrip() + " uso diário há 4 anos"
        elif line.startswith("@metric:0:0"):
            line = line.rstrip() + " 20%"
        elif line.startswith("@field:age"):
            line = line.rstrip() + " 33"
        lines.append(line)
    items, errors = parse_followup("\n".join(lines))
    assert errors == []
    p = gap_profile()
    assert apply_followup(p, items) == []
    assert p.skills[0].evidence == "uso diário há 4 anos" and p.experiences[0].bullets[0].metric == "20%" and p.age == 33
    bad_items, _ = parse_followup(text.replace("@field:age |", "@field:age |", 1).rstrip() + "\n@field:age | x | = muitos\n")
    errors = apply_followup(gap_profile(), bad_items)
    assert errors and "idade" in errors[0].lower()


def test_friendly_dates_placeholders_and_state_check():
    text = interview_form().replace("Nome completo:", "Nome completo: Ana").replace("Estado:", "Estado: São Paulo")
    text = text
    _, errors = parse_interview(text)
    assert any("sigla de duas letras" in e for e in errors)
    filled = interview_form().replace("Nome completo:", "Nome completo: Ana").replace("Empresa:", "Empresa: X")
    filled = filled.replace("Cargo:", "Cargo: Y").replace("Início:\nFim:\nEntregas:", "Início: out 2022\nFim: Atual\nEntregas:", 1)
    filled = filled.replace("Empresas vetadas:", "Empresas vetadas: -").replace("Motivadores:", "Motivadores: ?")
    data, errors = parse_interview(filled)
    assert errors == []
    exp = data["experiencias"]["experiences"][0]
    assert (exp["start"], exp["end"]) == ("2022-10", None)
    assert "restricoes" not in data
    assert "comportamento" not in data


def test_onsite_min_salary_field():
    text = interview_form().replace("Presencial só a partir de:", "Presencial só a partir de: R$ 6.000")
    data, errors = parse_interview(text)
    assert errors == [] and data["restricoes"]["constraints"]["onsite_min_salary"] == 6000


def test_identity_links():
    text = (interview_form().replace("Nome completo:", "Nome completo: Ana")
            .replace("LinkedIn:", "LinkedIn: linkedin.com/in/ana").replace("GitHub:", "GitHub: ana")
            .replace("Outros links:", "Outros links: ana.dev, youtube.com/@ana"))
    data, errors = parse_interview(text)
    assert errors == []
    assert data["identidade"] == {"name": "Ana", "linkedin": "linkedin.com/in/ana", "github": "ana",
                                  "links": ["ana.dev", "youtube.com/@ana"]}


def test_seniority_field():
    text = interview_form().replace("Senioridade:", "Senioridade: júnior, pleno")
    data, errors = parse_interview(text)
    assert errors == [] and data["restricoes"]["constraints"]["seniority"] == ["junior", "pleno"]
    bad, errors = parse_interview(interview_form().replace("Senioridade:", "Senioridade: master"))
    assert any("senioridade" in e for e in errors)


def test_commute_fields():
    text = (interview_form().replace("Tempo máximo de deslocamento:", "Tempo máximo de deslocamento: 120 minutos")
            .replace("Perto de casa:", "Perto de casa: Metrô Tatuapé"))
    data, errors = parse_interview(text)
    c = data["restricoes"]["constraints"]
    assert errors == [] and c["max_commute_minutes"] == 120
    assert c["home_area"] == "Metrô Tatuapé"
