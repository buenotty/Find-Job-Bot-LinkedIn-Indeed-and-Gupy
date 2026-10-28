import os
import subprocess
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parent.parent / "bin" / "jobs-master"


def test_launcher_exists_is_executable_and_valid_bash():
    assert LAUNCHER.exists() and os.access(LAUNCHER, os.X_OK)
    assert subprocess.run(["bash", "-n", str(LAUNCHER)]).returncode == 0


def test_launcher_prepares_venv_puts_it_on_path_and_loads_the_plugin():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'PATH="$ROOT/.venv/bin:$PATH"' in text
    assert '--plugin-dir "$ROOT"' in text
    assert "install -q -e" in text and "python3.12" in text


def test_launcher_runs_with_a_fake_claude_and_exposes_the_cli(tmp_path):
    fake = tmp_path / "claude"
    fake.write_text('#!/usr/bin/env bash\necho "ARGS: $*"\npython3 -m jobbot --help | head -1\n')
    fake.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    result = subprocess.run([str(LAUNCHER), "--model", "x"], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    assert "--plugin-dir" in result.stdout and "--model x" in result.stdout
    assert "usage: jobbot" in result.stdout
