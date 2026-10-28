from pathlib import Path

import yaml

from tests.test_cli import run
from tests.test_e2e import FIX, STEPS

HERE = Path(__file__).parent / "fixtures" / "maria"
NAME = "Maria Exemplo"


def put_interview(tmp_home):
    for i, step in enumerate(STEPS, 1):
        assert run(tmp_home, "put", NAME, step, str(FIX / f"{i}-{step}.yaml")).returncode == 0


def test_orientation_flow(tmp_home):
    put_interview(tmp_home)
    for layer in ("valores", "interesses", "personalidade", "ancoras", "estilo"):
        assert run(tmp_home, "assess-answer", NAME, str(HERE / f"answers-{layer}.yaml")).returncode == 0
    assert run(tmp_home, "assess-status", NAME).stdout.splitlines()[0] == "completo"

    done = run(tmp_home, "assess-finish", NAME, "--situations", str(HERE / "situations.yaml"))
    assert done.returncode == 0 and "confiabilidade: alta" in done.stdout
    assert sum(1 for l in done.stdout.splitlines() if l.split(".")[0] in ("valores", "interesses", "personalidade", "ancoras", "estilo")) == 36
    assert "trilha: especialista" in done.stdout and "codigo_holland:" in done.stdout

    out = {}
    for f in ("analista", "hardware", "engenheiro"):
        out[f] = run(tmp_home, "target-add", NAME, str(HERE / f"target-{f}.yaml")).stdout
    assert "group: agora" in out["analista"] and "status: pronto" in out["analista"]
    assert "group: sem_dado" in out["hardware"]
    assert "group: nova_formacao" in out["engenheiro"] and "status: em_formacao" in out["engenheiro"]

    before = run(tmp_home, "project-match", NAME, "Engenheiro de Dados").stdout
    assert "pct: 40" in before and "cv_liberado: nao" in before
    assert run(tmp_home, "course-add", NAME, str(HERE / "course-spark.yaml")).returncode == 0
    after = run(tmp_home, "project-match", NAME, "Engenheiro de Dados").stdout
    assert "pct: 60" in after and "cv_liberado: nao" in after

    assert run(tmp_home, "validate", NAME).returncode == 0
    profile_file = tmp_home / "profiles" / "maria-exemplo" / "profile.yaml"
    assert profile_file.stat().st_mode & 0o777 == 0o600
    skills = [s["name"] for s in yaml.safe_load(profile_file.read_text())["skills"]]
    assert "Spark" not in skills  # a finished course never edits skills by itself
