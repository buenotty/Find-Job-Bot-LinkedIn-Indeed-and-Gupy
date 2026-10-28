from datetime import date
from pathlib import Path

import yaml

from jobbot.schema import Application
from jobbot.store import update_profile
from tests.test_cli import run, write
from tests.test_e2e_b2 import HERE, NAME, prepare

BASE_NAME = "Maria Exemplo"


def load_yaml(name):
    return yaml.safe_load((HERE / name).read_text(encoding="utf-8"))


def setup_types(tmp_home):
    prepare(tmp_home)
    for t in ("analista", "hardware"):
        assert run(tmp_home, "type-define", NAME, str(HERE / f"type-{t}.yaml")).returncode == 0
    assert run(tmp_home, "type-resume", NAME, "Analista de Dados", str(HERE / "content-analista.yaml")).returncode == 0
    assert run(tmp_home, "type-resume", NAME, "Técnico de Hardware", str(HERE / "content-hardware.yaml")).returncode == 0


def test_round_flow(tmp_home, tmp_path):
    setup_types(tmp_home)
    base = tmp_home / "profiles" / "maria-exemplo"

    first = run(tmp_home, "round-check", NAME, "linkedin").stdout
    assert "permitido: 10" in first and "hoje: 0/30" in first

    mine = run(tmp_home, "vaga-check", NAME, str(HERE / "posting-employer.yaml"), "--platform", "linkedin")
    assert "filtro: empregador_atual" in mine.stdout

    hardware = load_yaml("posting-hardware-risky.yaml")
    hardware["modality"] = "hibrido"
    hardware_file = write(tmp_path / "hardware.yaml", hardware)
    for posting, extra in ((str(HERE / "posting-linkedin.yaml"), []), (hardware_file, []),
                           (str(HERE / "posting-sem-tipo.yaml"), ["--content-file", str(HERE / "content-sem-tipo.yaml")])):
        assert "filtro: nao" in run(tmp_home, "vaga-check", NAME, posting, "--platform", "linkedin").stdout
        r = run(tmp_home, "vaga-resume", NAME, posting, "--platform", "linkedin", *extra)
        assert r.returncode == 0, r.stderr
    counters = run(tmp_home, "round-check", NAME, "linkedin").stdout
    assert "hoje: 3/30" in counters and "pendentes: 3" in counters
    assert "hoje: 0/30" in run(tmp_home, "round-check", NAME, "indeed").stdout

    repeat = write(tmp_path / "repeat.yaml", {"title": "Analista de Dados Pleno", "company": "Acme Dados", "skills": ["SQL"],
                                              "url": "https://linkedin.com/jobs/view/1001?refId=zzz"})
    assert "repetida: repetida" in run(tmp_home, "vaga-check", NAME, repeat, "--platform", "linkedin").stdout
    cross = run(tmp_home, "vaga-check", NAME, write(tmp_path / "cross.yaml", {
        "title": "analista de dados pleno", "company": "ACME dados", "skills": ["SQL"], "url": "https://gupy.io/vaga/77"}),
        "--platform", "gupy")
    assert "repetida: repetida" in cross.stdout

    questions = str(HERE / "questions-form.yaml")
    answered = run(tmp_home, "answers-resolve", NAME, questions, "--vaga", "Analista@Acme").stdout.splitlines()
    assert "geral | respondida | perfil | Qual sua pretensão salarial? | 7000" in answered
    assert any("Quando você pode começar?" in l and "30 dias" in l for l in answered)
    assert any(l.startswith("geral | em_branco") and "animal" in l for l in answered)
    assert any(l.startswith("sensivel | em_branco") for l in answered)
    assert len(run(tmp_home, "pending-list", NAME).stdout.strip().splitlines()) == 2
    assert run(tmp_home, "answers-add", NAME, str(HERE / "answers-new.yaml")).returncode == 0
    assert run(tmp_home, "pending-list", NAME).stdout.strip() == ""
    again = run(tmp_home, "answers-resolve", NAME, questions).stdout
    assert "em_branco" not in again and "banco | Qual seu animal favorito? | Gato" in again

    risky = str(HERE / "fit-text-risky.txt")
    out = run(tmp_home, "fit-risks", NAME, risky).stdout.splitlines()
    assert "flags: proibe_ia, cronometrado, tentativa_unica, vigiado" in out and "acao: deixar_para_pessoa" in out
    assert run(tmp_home, "run-settings", NAME, "--fit-mode", "pular").returncode == 0
    assert "acao: deixar_para_pessoa" in run(tmp_home, "fit-risks", NAME, risky).stdout  # vigiado wins in any mode

    assert run(tmp_home, "platform-pause", NAME, "linkedin", "--reason", "captcha").returncode == 0
    assert "permitido: 0" in run(tmp_home, "round-check", NAME, "linkedin").stdout
    assert run(tmp_home, "platform-release", NAME, "linkedin").returncode == 0
    assert "permitido: 7" not in run(tmp_home, "round-check", NAME, "linkedin").stdout  # 3 pending, cap still 10
    assert "permitido: 10" in run(tmp_home, "round-check", NAME, "linkedin").stdout

    assert run(tmp_home, "app-status", NAME, "https://linkedin.com/jobs/view/1001", "enviada").returncode == 0
    apps = yaml.safe_load((base / "profile.yaml").read_text())["applications"]
    assert [a["status"] for a in apps if a["company"] == "Acme Dados"] == ["enviada"]
    assert "pendentes: 2" in run(tmp_home, "round-check", NAME, "linkedin").stdout

    today = date.today().isoformat()
    update_profile(BASE_NAME, lambda p: p.applications.extend(
        Application(date=today, platform="linkedin", status="enviada", url=f"https://x/{i}") for i in range(30)))
    capped = run(tmp_home, "round-check", NAME, "linkedin").stdout
    assert "permitido: 0" in capped and "limite diário" in capped

    assert run(tmp_home, "validate", NAME).returncode == 0
    for f in base.rglob("*"):
        assert f.stat().st_mode & 0o777 == (0o700 if f.is_dir() else 0o600), f
