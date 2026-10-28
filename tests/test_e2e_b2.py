from pathlib import Path

import yaml

from jobbot.pdf import extract_text
from tests.test_cli import run
from tests.test_e2e import FIX, STEPS

HERE = Path(__file__).parent / "fixtures" / "maria"
NAME = "Maria Exemplo"


def prepare(tmp_home):
    for i, step in enumerate(STEPS, 1):
        assert run(tmp_home, "put", NAME, step, str(FIX / f"{i}-{step}.yaml")).returncode == 0
    assert run(tmp_home, "put", NAME, "skills", str(HERE / "skills-hardware.yaml")).returncode == 0
    assert run(tmp_home, "put", NAME, "experiencias", str(HERE / "experiencias-hardware.yaml")).returncode == 0
    for target in ("target-analista", "target-hardware-skills"):
        assert run(tmp_home, "target-add", NAME, str(HERE / f"{target}.yaml")).returncode == 0


def pdfs(folder):
    return sorted(folder.glob("*.pdf"))


def test_resume_flow(tmp_home):
    prepare(tmp_home)
    base = tmp_home / "profiles" / "maria-exemplo"

    for t in ("analista", "hardware"):
        assert run(tmp_home, "type-define", NAME, str(HERE / f"type-{t}.yaml")).returncode == 0
    listing = run(tmp_home, "type-list", NAME).stdout
    assert listing.count("liberado: sim") == 2
    assert run(tmp_home, "type-resume", NAME, "Analista de Dados", str(HERE / "content-analista.yaml")).returncode == 0
    assert run(tmp_home, "type-resume", NAME, "Técnico de Hardware", str(HERE / "content-hardware.yaml")).returncode == 0
    analyst_model = extract_text(base / "types" / "analista-de-dados.pdf")
    hardware_model = extract_text(base / "types" / "tecnico-de-hardware.pdf")
    assert "Autodidata desde 2022" in hardware_model and "Autodidata" not in analyst_model

    typed = run(tmp_home, "vaga-resume", NAME, str(HERE / "posting-analista.yaml"))
    assert typed.returncode == 0 and "modo: tipo" in typed.stdout and "arriscada: nao" in typed.stdout
    risky = run(tmp_home, "vaga-resume", NAME, str(HERE / "posting-hardware-risky.yaml"))
    assert risky.returncode == 0 and "arriscada: sim" in risky.stdout
    scratch = run(tmp_home, "vaga-resume", NAME, str(HERE / "posting-sem-tipo.yaml"),
                  "--content-file", str(HERE / "content-sem-tipo.yaml"))
    assert scratch.returncode == 0 and "modo: do_zero" in scratch.stdout

    resumes = base / "resumes"
    import yaml
    records = yaml.safe_load((base / "profile.yaml").read_text(encoding="utf-8"))["applications"]
    file_of = {r["company"].lower(): base / r["file"] for r in records}
    analyst_pdf = next(v for k, v in file_of.items() if k.startswith("acme"))
    analyst_text = extract_text(analyst_pdf)
    assert "Kafka" in analyst_text.split("Competências")[1] and "Kafka" not in analyst_text.split("Competências")[0]
    risky_text = extract_text(next(v for k, v in file_of.items() if k.startswith("oficina")))
    for missing in ("Redes", "Cabeamento", "Linux", "Docker"):
        assert missing not in risky_text
    sheet = analyst_pdf.with_suffix(".review.txt").read_text(encoding="utf-8")
    assert "Kafka" in sheet and "entrevista" in sheet
    assert len(file_of) == 3

    log = yaml.safe_load((base / "profile.yaml").read_text())["applications"]
    assert [r["mode"] for r in log] == ["tipo", "tipo", "do_zero"]
    assert log[1]["risky"] is True
    for f in [*resumes.iterdir(), *(base / "types").iterdir(), base / "profile.yaml"]:
        assert f.stat().st_mode & 0o777 == 0o600, f
    assert run(tmp_home, "validate", NAME).returncode == 0
    assert len(run(tmp_home, "applications", NAME).stdout.strip().splitlines()) == 3
