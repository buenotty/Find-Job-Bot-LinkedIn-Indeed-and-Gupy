import json
import os
import subprocess
import sys

import yaml

IDENT = {"name": "Ana", "age": 30, "state": "SP", "city": "São Paulo"}


def run(home, *args):
    env = {**os.environ, "JOBBOT_HOME": str(home)}
    return subprocess.run([sys.executable, "-m", "jobbot", *args],
                          capture_output=True, text=True, env=env)


def write(path, content):
    path.write_text(content if isinstance(content, str) else yaml.safe_dump(content, allow_unicode=True),
                    encoding="utf-8")
    return str(path)


def test_status_new_profile(tmp_home):
    r = run(tmp_home, "status", "ana")
    assert r.returncode == 0 and r.stdout.strip() == "identidade"


def test_put_advances_status(tmp_home, tmp_path):
    f = write(tmp_path / "id.yaml", IDENT)
    assert run(tmp_home, "put", "ana", "identidade", f).returncode == 0
    assert run(tmp_home, "status", "ana").stdout.strip() == "experiencias"


def test_put_unknown_step_exits_1(tmp_home, tmp_path):
    f = write(tmp_path / "x.yaml", {})
    r = run(tmp_home, "put", "ana", "nope", f)
    assert r.returncode == 1 and "nope" in r.stderr and "Traceback" not in r.stderr


def test_match_output_keys(tmp_home, tmp_path):
    f = write(tmp_path / "s.yaml", {"skills": [{"name": "SQL", "level": "medio"}]})
    run(tmp_home, "put", "ana", "skills", f)
    r = run(tmp_home, "match", "ana", "--required", "SQL,Kafka")
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert "pct: 50" in lines
    assert "label: Chance média" in lines
    assert "stretch_action: esticar_marcado" in lines
    assert "missing: Kafka" in lines


def test_validate_reports_errors(tmp_home, tmp_path):
    run(tmp_home, "put", "ana", "identidade", write(tmp_path / "i.yaml", IDENT))
    run(tmp_home, "put", "ana", "skills", write(tmp_path / "s.yaml", {"skills": [{"name": "SQL", "level": "guru"}]}))
    r = run(tmp_home, "validate", "ana")
    assert r.returncode == 1 and "nível" in r.stdout


def test_corrupt_profile_is_clean_error(tmp_home, tmp_path):
    run(tmp_home, "put", "ana", "identidade", write(tmp_path / "i.yaml", IDENT))
    (tmp_home / "profiles" / "ana" / "profile.yaml").write_text("a: [")
    r = run(tmp_home, "validate", "ana")
    assert r.returncode == 1 and "profile.yaml" in r.stderr and "Traceback" not in r.stderr


def test_cv_writes_file(tmp_home, tmp_path):
    run(tmp_home, "put", "ana", "identidade", write(tmp_path / "i.yaml", IDENT))
    s = write(tmp_path / "sum.md", "Analista de dados.")
    r = run(tmp_home, "cv", "ana", "--summary-file", s)
    assert r.returncode == 0
    assert (tmp_home / "profiles" / "ana" / "cv-base.md").read_text().startswith("# Ana")


def test_cv_blocks_invented_number(tmp_home, tmp_path):
    run(tmp_home, "put", "ana", "identidade", write(tmp_path / "i.yaml", IDENT))
    s = write(tmp_path / "sum.md", "Reduzi 70% dos custos.")
    r = run(tmp_home, "cv", "ana", "--summary-file", s)
    assert r.returncode == 1 and "70%" in r.stderr
    assert not (tmp_home / "profiles" / "ana" / "cv-base.md").exists()


def test_check_clean_and_dirty(tmp_home, tmp_path):
    run(tmp_home, "put", "ana", "identidade", write(tmp_path / "i.yaml", IDENT))
    assert run(tmp_home, "check", "ana", write(tmp_path / "ok.md", "Sem números.")).returncode == 0
    r = run(tmp_home, "check", "ana", write(tmp_path / "bad.md", "Cresci 90%."))
    assert r.returncode == 1 and "90%" in r.stdout


def test_market_table(tmp_home, tmp_path):
    run(tmp_home, "put", "ana", "skills", write(tmp_path / "s.yaml", {"skills": [{"name": "SQL", "level": "medio"}]}))
    jobs = {"role": "Analista de Dados", "jobs": [
        {"title": "A", "company": "X", "skills": ["SQL"], "salary_min": 5000, "salary_max": 7000}]}
    r = run(tmp_home, "market", "ana", write(tmp_path / "j.json", json.dumps(jobs)))
    assert r.returncode == 0
    assert "| Analista de Dados |" in r.stdout and "Vaga perfeita" in r.stdout and "6000" in r.stdout


def test_path_prints_profile_dir(tmp_home):
    r = run(tmp_home, "path", "José da Silva")
    assert r.returncode == 0 and r.stdout.strip() == str(tmp_home / "profiles" / "jose-da-silva")


def test_put_misspelled_key_exits_1_with_message(tmp_home, tmp_path):
    f = write(tmp_path / "s.yaml", {"skills": [{"nome": "SQL", "nivel": "medio"}]})
    r = run(tmp_home, "put", "ana", "skills", f)
    assert r.returncode == 1 and "nome" in r.stderr and "Traceback" not in r.stderr
