from datetime import date

import pytest

from jobbot.answers import (
    add_pending, builtin_answer, classify_field, match_bank, resolve, upsert_answer,
)
from jobbot.schema import AnswerEntry, PendingQuestion, Profile, Screening

TODAY = date(2026, 10, 25)


def person(**kw):
    base = dict(screening=Screening(salary_expectation=8000, contract="CLT", availability="30 dias",
                                    email="m@example.com", phone="21999990000",
                                    years_by_skill={"SQL": 4, "Python": 2.5}))
    base.update(kw)
    return Profile(**base)


@pytest.mark.parametrize("question,expected", [
    ("Você é pessoa com deficiência (PCD)?", "sensivel"),
    ("Qual é o seu gênero?", "sensivel"),
    ("Qual a sua cor ou raça?", "sensivel"),
    ("Orientação sexual", "sensivel"),
    ("Estado civil", "sensivel"),
    ("Autorizo o tratamento dos meus dados conforme a LGPD", "legal"),
    ("Li e aceito os termos de uso", "legal"),
    ("Pretensão salarial", "geral"),
    ("Você tem experiência com corretoras?", "geral"),
])
def test_classify_field_sensitive_legal_general(question, expected):
    assert classify_field(question) == expected


def entry(q, a="x", cat="geral"):
    return AnswerEntry(q, a, cat)


def test_match_bank_exact_normalized():
    bank = [entry("Você possui CNH?", "Sim")]
    assert match_bank("voce possui cnh", bank).answer == "Sim"


def test_match_bank_similar_wording_matches():
    bank = [entry("Pretensão salarial", "8000")]
    assert match_bank("Qual sua pretensão salarial?", bank).answer == "8000"
    assert match_bank("Você tem CNH?", [entry("Você possui CNH?", "Sim")]).answer == "Sim"


def test_match_bank_different_skill_does_not_match():
    bank = [entry("Anos de experiência com Python", "2")]
    assert match_bank("Anos de experiência com SQL", bank) is None


def test_match_bank_different_numbers_do_not_match():
    bank = [entry("Você tem mais de 5 anos de experiência?", "Não")]
    assert match_bank("Você tem mais de 10 anos de experiência?", bank) is None


def test_match_bank_empty_or_nothing_in_common():
    assert match_bank("Pergunta qualquer", []) is None
    assert match_bank("???", [entry("Pretensão salarial")]) is None


def test_builtin_salary_availability_email_phone():
    p = person()
    assert builtin_answer("Qual sua pretensão salarial?", p) == "8000"
    assert builtin_answer("Quando você pode começar?", p) == "30 dias"
    assert builtin_answer("Informe seu e-mail", p) == "m@example.com"
    assert builtin_answer("Telefone / WhatsApp", p) == "21999990000"


def test_builtin_years_by_skill_normalized():
    p = person()
    assert builtin_answer("Quantos anos de experiência você tem com SQL?", p) == "4"
    assert builtin_answer("Anos de experiência em python", p) == "2.5"
    assert builtin_answer("Anos de experiência com Kafka", p) is None


def test_builtin_none_when_profile_lacks_value():
    assert builtin_answer("Pretensão salarial", Profile()) is None
    assert builtin_answer("Seu e-mail", Profile()) is None


def test_resolve_order_bank_then_builtin():
    p = person(answers=[entry("Pretensão salarial", "9000")])
    r = resolve(["Pretensão salarial", "Telefone"], p)
    assert (r[0].answer, r[0].source, r[0].status) == ("9000", "banco", "respondida")
    assert (r[1].answer, r[1].source) == ("21999990000", "perfil")


def test_resolve_sensitive_and_legal_only_from_bank():
    p = person()
    r = resolve(["Você é PCD?", "Autorizo o uso dos meus dados (LGPD)"], p)
    assert [x.status for x in r] == ["em_branco", "em_branco"] and [x.answer for x in r] == [None, None]
    p.answers = [entry("Você é PCD?", "Não", "sensivel")]
    assert resolve(["Você é PCD?"], p)[0].answer == "Não"


def test_resolve_unknown_is_blank_never_invented():
    r = resolve(["Qual seu animal favorito?"], person())[0]
    assert (r.status, r.answer, r.source, r.category) == ("em_branco", None, "", "geral")


def test_add_pending_dedupes_and_skips_answered():
    p = person(answers=[entry("Pretensão salarial", "8000")])
    add_pending(p, ["Qual seu animal favorito?", "Pretensão salarial", "Seu animal favorito"], "Analista@Acme", TODAY)
    assert [q.question for q in p.pending] == ["Qual seu animal favorito?"]
    assert p.pending[0].vaga == "Analista@Acme" and p.pending[0].date == "2026-10-25"
    add_pending(p, ["Qual seu animal favorito?"], "Outra@Vaga", TODAY)
    assert len(p.pending) == 1


def test_upsert_answer_replaces_and_clears_pending():
    p = person(answers=[entry("Você possui CNH?", "Não")],
               pending=[PendingQuestion("Voce tem CNH", "geral", "v", "d"), PendingQuestion("Outra", "geral", "v", "d")])
    upsert_answer(p, entry("Você tem CNH?", "Sim"))
    assert [a.answer for a in p.answers] == ["Sim"]
    assert [q.question for q in p.pending] == ["Outra"]


@pytest.mark.parametrize("question", [
    "Você tem disponibilidade para mudar de cidade?",
    "Tem disponibilidade para trabalhar aos sábados?",
    "Descreva uma situação em que você usou o e-mail para resolver um conflito",
    "Se quisermos contato por e-mail ou telefone, você autoriza?",
    "Você autoriza contato por telefone e aceita os termos?",
])
def test_builtin_does_not_hit_the_wrong_field(question):
    assert builtin_answer(question, person()) is None
    assert resolve([question], person())[0].status == "em_branco"


def test_builtin_short_field_labels_still_work():
    p = person()
    assert builtin_answer("Disponibilidade", p) == "30 dias"
    assert builtin_answer("Qual a sua disponibilidade?", p) == "30 dias"
    assert builtin_answer("Seu melhor e-mail para contato", p) == "m@example.com"


@pytest.mark.parametrize("question,expected", [
    ("Você autoriza o uso dos seus dados?", "legal"),
    ("Você concorda com o uso e tratamento dos seus dados?", "legal"),
    ("Aceita os termos e a política de privacidade?", "legal"),
    ("Declaro que as informações são verdadeiras", "legal"),
    ("Possui autorização de trabalho no Brasil?", "sensivel"),
    ("Precisa de visto de trabalho?", "sensivel"),
    ("Qual a sua nacionalidade?", "sensivel"),
    ("Data de nascimento", "sensivel"),
    ("Informe seu CPF", "sensivel"),
    ("Aceita trabalhar em regime híbrido?", "geral"),
])
def test_classify_field_more_forms(question, expected):
    assert classify_field(question) == expected
