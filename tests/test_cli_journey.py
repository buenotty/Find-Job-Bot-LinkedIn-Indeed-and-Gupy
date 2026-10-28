from tests.test_cli import run, write
from tests.test_cli_b2 import NAME, make_profile


def test_next_for_a_new_person_points_to_the_interview(tmp_home):
    r = run(tmp_home, "next", "Novo")
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert "1. Entrevista e perfil | jobbot-interview | pendente" in lines
    assert "6. Rodada de vagas | jobbot-round | pendente" in lines
    assert lines[-1] == "proximo: jobbot-interview"


def test_next_marks_done_stages(tmp_home, tmp_path):
    make_profile(tmp_home)
    (tmp_home / "profiles" / "maria" / "focus-report.md").write_text("x", encoding="utf-8")
    out = run(tmp_home, "next", NAME).stdout
    assert "jobbot-market | feito" in out and "proximo:" in out
    assert "tipos" not in out.splitlines()[-1]


def test_next_on_corrupt_profile_is_a_clean_error(tmp_home):
    make_profile(tmp_home)
    (tmp_home / "profiles" / "maria" / "profile.yaml").write_text("a: [")
    r = run(tmp_home, "next", NAME)
    assert r.returncode == 1 and "profile.yaml" in r.stderr and "Traceback" not in r.stderr
