from pathlib import Path

from tests.test_cli import run, write

FIX = Path(__file__).parent / "fixtures" / "maria"
STEPS = ["identidade", "experiencias", "skills", "certificacoes_idiomas",
         "restricoes", "triagem", "comportamento"]


def test_full_flow(tmp_home, tmp_path):
    for i, step in enumerate(STEPS, 1):
        assert run(tmp_home, "put", "Maria Exemplo", step, str(FIX / f"{i}-{step}.yaml")).returncode == 0

    assert run(tmp_home, "status", "Maria Exemplo").stdout.strip() == "completo"
    assert run(tmp_home, "validate", "Maria Exemplo").returncode == 0

    m = run(tmp_home, "match", "Maria Exemplo", "--required", "SQL,Python,Kafka,Spark")
    assert "label: Chance média" in m.stdout and "missing: Kafka, Spark" in m.stdout

    market = run(tmp_home, "market", "Maria Exemplo",
                 str(FIX / "jobs-engenheiro.json"), str(FIX / "jobs-analista.json"))
    rows = [l for l in market.stdout.splitlines() if l.startswith("| ") and "Cargo" not in l]
    assert rows[0].startswith("| Analista de Dados |") and rows[1].startswith("| Engenheiro de Dados |")

    summary = write(tmp_path / "summary.md", "Analista de dados que reduziu 30% do tempo de relatórios.")
    cv = run(tmp_home, "cv", "Maria Exemplo", "--summary-file", summary)
    assert cv.returncode == 0
    assert "Maria Exemplo" in (tmp_home / "profiles" / "maria-exemplo" / "cv-base.md").read_text()

    dirty = run(tmp_home, "check", "Maria Exemplo", write(tmp_path / "bad.md", "Cresci 90% ao ano."))
    assert dirty.returncode == 1 and "90%" in dirty.stdout
