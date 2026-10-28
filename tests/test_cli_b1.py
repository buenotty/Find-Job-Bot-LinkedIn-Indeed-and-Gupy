import re

import yaml

from jobbot.assessment import load_bank
from tests.test_cli import IDENT, run, write


def varied_answers(layer=None, uniform=None):
    """Coherent answers: twins land on the same adjusted level as the item they repeat."""
    levels, out = {}, {}
    for n, item in enumerate(load_bank()):
        level = levels[item.twin] if item.twin else n % 5 + 1
        levels[item.id] = level
        if layer in (None, item.layer):
            out[item.id] = uniform if uniform else (6 - level if item.reverse else level)
    return out


def start(tmp_home, tmp_path, skills=("SQL",)):
    run(tmp_home, "put", "ana", "identidade", write(tmp_path / "i.yaml", IDENT))
    run(tmp_home, "put", "ana", "skills", write(tmp_path / "s.yaml", {"skills": [{"name": s, "level": "medio"} for s in skills]}))


def dimension_lines(out):
    return [l for l in out.splitlines() if re.match(r"(valores|interesses|personalidade|ancoras|estilo)\.", l)]


def test_assess_flow_end_to_end(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    assert run(tmp_home, "assess-status", "ana").stdout.splitlines()[0] == "proxima_camada: valores"
    for layer, nxt in (("valores", "interesses"), ("interesses", "personalidade"), ("personalidade", "ancoras"), ("ancoras", "estilo")):
        r = run(tmp_home, "assess-answer", "ana", write(tmp_path / f"{layer}.yaml", varied_answers(layer)))
        assert r.returncode == 0
        assert run(tmp_home, "assess-status", "ana").stdout.splitlines()[0] == f"proxima_camada: {nxt}"
    run(tmp_home, "assess-answer", "ana", write(tmp_path / "p.yaml", varied_answers("estilo")))
    assert run(tmp_home, "assess-status", "ana").stdout.splitlines()[0] == "completo"
    sit = write(tmp_path / "sit.yaml", [{"pergunta": "q", "resposta": "r"}])
    r = run(tmp_home, "assess-finish", "ana", "--situations", sit)
    assert r.returncode == 0 and len(dimension_lines(r.stdout)) == 36
    assert "confiabilidade: alta" in r.stdout


def test_assess_answer_rejects_out_of_range_and_saves_nothing(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    bad = {**varied_answers("valores"), "vsal01": 6}
    r = run(tmp_home, "assess-answer", "ana", write(tmp_path / "b.yaml", bad))
    assert r.returncode == 1 and "vsal01" in r.stderr and "Traceback" not in r.stderr
    assert "respondidas: 0/" in run(tmp_home, "assess-status", "ana").stdout


def test_assess_finish_before_complete_exits_1(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    run(tmp_home, "assess-answer", "ana", write(tmp_path / "v.yaml", varied_answers("valores")))
    r = run(tmp_home, "assess-finish", "ana")
    assert r.returncode == 1 and "faltam" in r.stderr


def test_straight_lining_prints_baixa(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    run(tmp_home, "assess-answer", "ana", write(tmp_path / "u.yaml", varied_answers(uniform=3)))
    r = run(tmp_home, "assess-finish", "ana")
    assert r.returncode == 0
    assert "confiabilidade: baixa" in r.stdout and "respostas_uniformes" in r.stdout


def test_target_add_with_skills_sets_group_and_status(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    run(tmp_home, "target-add", "ana", write(tmp_path / "t1.yaml", {"role": "Analista", "source": "sugerida", "required_skills": ["SQL"]}))
    run(tmp_home, "target-add", "ana", write(tmp_path / "t2.yaml", {"role": "Engenheiro", "source": "sugerida", "required_skills": ["SQL", "Kafka", "Spark"]}))
    targets = yaml.safe_load(open(tmp_home / "profiles" / "ana" / "profile.yaml"))["targets"]
    by_role = {t["role"]: t for t in targets}
    assert (by_role["Analista"]["group"], by_role["Analista"]["status"], by_role["Analista"]["match_at_acceptance"]) == ("agora", "pronto", 100)
    assert (by_role["Engenheiro"]["group"], by_role["Engenheiro"]["status"]) == ("nova_formacao", "em_formacao")


def test_target_add_without_skills_is_sem_dado(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    run(tmp_home, "target-add", "ana", write(tmp_path / "t.yaml", {"role": "Técnico de Hardware", "source": "propria"}))
    t = yaml.safe_load(open(tmp_home / "profiles" / "ana" / "profile.yaml"))["targets"][0]
    assert (t["group"], t["status"], t["match_at_acceptance"]) == ("sem_dado", "sem_dado_mercado", None)
    r = run(tmp_home, "project-match", "ana", "Técnico de Hardware")
    assert r.returncode == 1 and "skills" in r.stderr


def test_project_match_unknown_role_exits_1(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    r = run(tmp_home, "project-match", "ana", "Astronauta")
    assert r.returncode == 1 and "targets" in r.stderr


def test_course_add_then_project_match_rises(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    run(tmp_home, "target-add", "ana", write(tmp_path / "t.yaml", {"role": "Engenheiro", "source": "sugerida", "required_skills": ["SQL", "Kafka", "Spark"]}))
    before = run(tmp_home, "project-match", "ana", "Engenheiro").stdout
    assert "pct: 33" in before and "cv_liberado: nao" in before
    r = run(tmp_home, "course-add", "ana", write(tmp_path / "c.yaml", {"course": "Kafka na prática", "provider": "X", "skills_claimed": ["Kafka"], "evidence": "projeto"}))
    assert r.returncode == 0
    after = run(tmp_home, "project-match", "ana", "Engenheiro").stdout
    assert "pct: 66" in after and "missing: Spark" in after
    profile = yaml.safe_load(open(tmp_home / "profiles" / "ana" / "profile.yaml"))
    assert [s["name"] for s in profile["skills"]] == ["SQL"]


def test_band_gratis_and_price(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    assert run(tmp_home, "band", "ana", "gratis").stdout.strip() == "faixa: gratuito"
    assert run(tmp_home, "band", "ana", "150").stdout.strip() == "faixa: barato"
    assert run(tmp_home, "band", "ana", "999").stdout.strip() == "faixa: caro"
    assert run(tmp_home, "band", "ana", "abc").returncode == 1


def test_market_claims_boundary(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    run(tmp_home, "put", "ana", "triagem", write(tmp_path / "tr.yaml", {"screening": {"salary_expectation": 8000}}))
    r29 = run(tmp_home, "market-claims", "ana", "--n-jobs", "29", "--salary-median", "5000", "--applicants-median", "300")
    assert "saturado: indicio" in r29.stdout and "paga_pouco: indicio" in r29.stdout
    r30 = run(tmp_home, "market-claims", "ana", "--n-jobs", "30", "--salary-median", "5000", "--applicants-median", "300")
    assert "saturado: sim" in r30.stdout and "paga_pouco: sim" in r30.stdout


def test_corrupt_profile_is_clean_error(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    (tmp_home / "profiles" / "ana" / "profile.yaml").write_text("a: [")
    r = run(tmp_home, "target-add", "ana", write(tmp_path / "t.yaml", {"role": "x", "source": "propria"}))
    assert r.returncode == 1 and "profile.yaml" in r.stderr and "Traceback" not in r.stderr


def test_target_add_on_unknown_person_exits_1_and_creates_nothing(tmp_home, tmp_path):
    r = run(tmp_home, "target-add", "Ghost", write(tmp_path / "t.yaml", {"role": "x", "source": "propria"}))
    assert r.returncode == 1 and "nome" in r.stderr
    assert not (tmp_home / "profiles" / "ghost").exists()


def test_target_add_bad_source_exits_1_and_profile_stays_valid(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    r = run(tmp_home, "target-add", "ana", write(tmp_path / "t.yaml", {"role": "x", "source": "xyz"}))
    assert r.returncode == 1 and "origem" in r.stderr
    assert run(tmp_home, "validate", "ana").returncode == 0


def test_course_add_bad_skills_exits_1_without_internal_error(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    r = run(tmp_home, "course-add", "ana", write(tmp_path / "c.yaml", {"course": "c", "skills_claimed": [1, None]}))
    assert r.returncode == 1 and "skills_claimed" in r.stderr and "normalize" not in r.stderr


def test_assess_finish_with_bad_situations_keeps_answers(tmp_home, tmp_path):
    start(tmp_home, tmp_path)
    run(tmp_home, "assess-answer", "ana", write(tmp_path / "a.yaml", varied_answers()))
    r = run(tmp_home, "assess-finish", "ana", "--situations", write(tmp_path / "s.yaml", ["hello", 3]))
    assert r.returncode == 1
    assert run(tmp_home, "assess-status", "ana").stdout.splitlines()[0] == "completo"
    assert run(tmp_home, "assess-finish", "ana").returncode == 0
