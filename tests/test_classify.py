import pytest

from jobbot.classify import classify
from jobbot.posting import Posting
from jobbot.schema import JobType, Profile, Skill, Target

OWNED = ["SQL", "Power BI", "Excel", "Python", "Montagem de computadores", "Diagnóstico de hardware"]


def person(**kw):
    base = dict(
        skills=[Skill(s) for s in OWNED],
        targets=[
            Target(role="Analista de Dados", group="agora", required_skills=["SQL", "Power BI", "Excel"]),
            Target(role="Técnico de Hardware", group="agora",
                   required_skills=["Montagem de computadores", "Diagnóstico de hardware"]),
        ],
        job_types=[JobType(role="Analista de Dados", keywords=["Tableau"]), JobType(role="Técnico de Hardware")],
    )
    base.update(kw)
    return Profile(**base)


def post(title, skills=()):
    return Posting(title=title, skills=list(skills))


def test_classify_unique_best():
    c = classify(post("Analista de Dados Pleno", ["SQL", "Power BI"]), person())
    assert (c.kind, c.role) == ("tipo", "Analista de Dados")
    assert c.scores["Analista de Dados"] > c.scores["Técnico de Hardware"]


def test_classify_tie_is_ambiguo():
    c = classify(post("Analista Hardware"), person())
    assert c.kind == "ambiguo" and sorted(c.candidates) == ["Analista de Dados", "Técnico de Hardware"]


def test_classify_no_types_is_sem_tipo():
    assert classify(post("Analista de Dados", ["SQL"]), person(job_types=[])).kind == "sem_tipo"


def test_classify_low_score_is_sem_tipo():
    assert classify(post("Contador", ["Cobol"]), person()).kind == "sem_tipo"


def test_classify_ignores_type_that_is_no_longer_releasable():
    p = person(targets=[Target(role="Analista de Dados", group="sem_dado")])
    assert classify(post("Analista de Dados", ["SQL", "Power BI"]), p).kind == "sem_tipo"


def test_classify_forced_must_be_defined_type():
    with pytest.raises(ValueError, match="tipo"):
        classify(post("x"), person(), forced="Astronauta")
    c = classify(post("Contador"), person(), forced="técnico de hardware")
    assert (c.kind, c.role) == ("tipo", "Técnico de Hardware")


def test_title_word_bonus_is_accent_insensitive():
    c = classify(post("TECNICO Hardware"), person())
    assert (c.kind, c.role) == ("tipo", "Técnico de Hardware")
