import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# CPF with mask, personal-looking absolute paths and e-mail addresses must not be committed.
PATTERNS = {
    "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "home path": re.compile(r"/Users/[a-z0-9_.-]+/"),
    "email": re.compile(r"(?!a@b\.com)[\w.+-]+@(?!example\.)(?!b\.com)[\w-]+\.(com|com\.br|org|net)\b"),
}


def test_tracked_files_have_no_personal_data():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        return  # not a git checkout (e.g. sdist): nothing to scan
    hits = []
    for rel in out.stdout.split():
        path = ROOT / rel
        if rel == "tests/test_no_personal_data.py" or path.suffix in {".pdf", ".png"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        hits += [f"{rel}: {n}" for n, rx in PATTERNS.items() if rx.search(text)]
    assert not hits, hits
