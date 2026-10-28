import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from jobbot.assessment import load_bank
from jobbot.forms import assessment_form
from tests.test_cli import run
from tests.test_forms import FIXTURE, fill

NAME = "Maria Exemplo"


def pdir(tmp_home):
    return tmp_home / "profiles" / "maria-exemplo"


def test_form_new_interview_creates_numbered_files(tmp_home):
    first = run(tmp_home, "form-new", NAME, "interview")
    assert first.returncode == 0
    path = Path(first.stdout.strip().splitlines()[-1].split(": ", 1)[1])
    assert path.name == "questionario-maria-exemplo.txt" and path.parent == tmp_home / "forms"
    assert path.read_text(encoding="utf-8").startswith("# JOBBOT:interview")
    assert path.stat().st_mode & 0o777 == 0o600
    second = run(tmp_home, "form-new", NAME, "interview").stdout
    assert "questionario-maria-exemplo-2.txt" in second
    assert path.exists()  # never overwrites a form the person may be filling


def test_form_new_rejects_unknown_kind(tmp_home):
    r = run(tmp_home, "form-new", NAME, "outro")
    assert r.returncode == 1 and "interview" in r.stderr and "Traceback" not in r.stderr


def test_form_load_saves_every_step_and_the_profile_validates(tmp_home, tmp_path):
    f = tmp_path / "q.txt"
    shutil.copy(FIXTURE, f)
    r = run(tmp_home, "form-load", NAME, str(f))
    assert r.returncode == 0, r.stderr
    for step in ("identidade", "experiencias", "skills", "certificacoes_idiomas", "restricoes", "triagem", "comportamento"):
        assert f"salvo: {step}" in r.stdout
    assert run(tmp_home, "status", NAME).stdout.strip() == "completo"
    assert run(tmp_home, "validate", NAME).returncode == 0
    data = yaml.safe_load((pdir(tmp_home) / "profile.yaml").read_text())
    assert data["name"] == "Maria Exemplo" and data["screening"]["years_by_skill"]["Python"] == 2.5
    assert data["education"][0]["institution"] == "USJT" and data["projects"][0]["kind"] == "autodidata"


def test_form_load_with_errors_saves_nothing_and_lists_every_line(tmp_home, tmp_path):
    f = tmp_path / "q.txt"
    f.write_text(FIXTURE.read_text(encoding="utf-8").replace("Idade: 28", "Idade: vinte").replace("Contrato: CLT", "Contrato: freela"),
                 encoding="utf-8")
    r = run(tmp_home, "form-load", NAME, str(f))
    assert r.returncode == 1 and r.stderr.count("linha ") >= 2 and "Traceback" not in r.stderr
    assert not (pdir(tmp_home) / "profile.yaml").exists()


def test_form_load_rejects_files_without_a_known_marker(tmp_home, tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("qualquer coisa\n", encoding="utf-8")
    r = run(tmp_home, "form-load", NAME, str(f))
    assert r.returncode == 1 and "JOBBOT" in r.stderr


def test_assessment_form_round_trip_partial_then_complete(tmp_home, tmp_path):
    bank = load_bank()
    blank = tmp_path / "t.txt"
    blank.write_text(assessment_form(bank), encoding="utf-8")
    ids = [i.id for i in bank]
    half = tmp_path / "half.txt"
    half.write_text(fill(blank.read_text(encoding="utf-8"), {i: (n % 5) + 1 for n, i in enumerate(ids[:60])}), encoding="utf-8")
    r = run(tmp_home, "form-load", NAME, str(half))
    assert r.returncode == 0 and "respondidas: 60/" in r.stdout and "assess-finish" not in r.stdout
    full = tmp_path / "full.txt"
    full.write_text(fill(blank.read_text(encoding="utf-8"), {i: (n % 5) + 1 for n, i in enumerate(ids)}), encoding="utf-8")
    r = run(tmp_home, "form-load", NAME, str(full))
    assert f"respondidas: {len(ids)}/{len(ids)}" in r.stdout and "proximo: assess-finish" in r.stdout


def test_assessment_form_bad_value_saves_nothing(tmp_home, tmp_path):
    bank = load_bank()
    bad = tmp_path / "bad.txt"
    bad.write_text(fill(assessment_form(bank), {bank[0].id: 9, bank[1].id: 3}), encoding="utf-8")
    r = run(tmp_home, "form-load", NAME, str(bad))
    assert r.returncode == 1 and bank[0].id in r.stderr
    assert "respondidas: 0/" in run(tmp_home, "assess-status", NAME).stdout


def test_followup_flow_generates_only_gaps_and_applies_answers(tmp_home, tmp_path):
    f = tmp_path / "q.txt"
    shutil.copy(FIXTURE, f)
    run(tmp_home, "form-load", NAME, str(f))
    r = run(tmp_home, "form-gaps", NAME)
    assert r.returncode == 0
    path = Path(r.stdout.strip().splitlines()[-1].split(": ", 1)[1])
    text = path.read_text(encoding="utf-8")
    assert "@metric:0:1" in text and "@field:age" not in text  # Maria already gave her age
    filled = tmp_path / "s.txt"
    filled.write_text(text.replace("@metric:0:1 |", "@metric:0:1 |", 1).rstrip().replace(
        "| =", "| = 15%") if False else "\n".join(
            (l.rstrip() + " 15%") if l.startswith("@metric:0:1") else l for l in text.splitlines()), encoding="utf-8")
    assert run(tmp_home, "form-load", NAME, str(filled)).returncode == 0
    data = yaml.safe_load((pdir(tmp_home) / "profile.yaml").read_text())
    assert data["experiences"][0]["bullets"][1]["metric"] == "15%"


def test_form_gaps_without_gaps_says_so(tmp_home, tmp_path):
    f = tmp_path / "q.txt"
    f.write_text(FIXTURE.read_text(encoding="utf-8").replace("- Criei painéis de acompanhamento", "- Criei painéis | 12%")
                 .replace("- Python | médio | scripts de limpeza de dados", "- Python | médio | scripts")
                 .replace("- SQL | especialista | uso diário há 4 anos", "- SQL | especialista | 4 anos"), encoding="utf-8")
    run(tmp_home, "form-load", NAME, str(f))
    r = run(tmp_home, "form-gaps", NAME)
    assert r.returncode == 0 and "sem lacunas" in r.stdout


def test_forms_go_to_the_visible_folder_and_its_permissions_are_untouched(tmp_home):
    forms = tmp_home / "forms"
    forms.mkdir()
    forms.chmod(0o755)
    run(tmp_home, "form-new", NAME, "interview")
    run(tmp_home, "form-new", NAME, "teste")
    assert forms.stat().st_mode & 0o777 == 0o755
    assert sorted(p.name for p in forms.iterdir()) == ["questionario-maria-exemplo.txt", "teste-maria-exemplo.txt"]
    assert not any(pdir(tmp_home).glob("*.txt")) if pdir(tmp_home).exists() else True


def fill_name(path, name="Maria Exemplo"):
    text = FIXTURE.read_text(encoding="utf-8").replace("Maria Exemplo", name)
    Path(path).write_text(text, encoding="utf-8")


def test_form_load_without_a_path_finds_the_newest_file_of_that_person(tmp_home):
    forms = tmp_home / "forms"
    forms.mkdir()
    old, new = forms / "questionario-maria-exemplo.txt", forms / "questionario-maria-exemplo-2.txt"
    other = forms / "questionario-joao.txt"
    fill_name(old, "Nome Antigo")
    fill_name(new, "Maria Exemplo")
    fill_name(other, "Joao")
    import os
    os.utime(old, (1_000_000, 1_000_000))
    os.utime(other, (9_000_000_000, 9_000_000_000))  # newest overall, but another person's
    r = run(tmp_home, "form-load", NAME)
    assert r.returncode == 0 and "lendo:" in r.stdout and "-2.txt" in r.stdout
    assert yaml.safe_load((pdir(tmp_home) / "profile.yaml").read_text())["name"] == "Maria Exemplo"


def test_form_load_without_a_path_falls_back_to_the_old_hidden_location(tmp_home):
    pdir(tmp_home).mkdir(parents=True)
    fill_name(pdir(tmp_home) / "questionario.txt")
    r = run(tmp_home, "form-load", NAME)
    assert r.returncode == 0 and "salvo: identidade" in r.stdout


def test_form_load_without_a_path_and_nothing_found_is_a_clean_error(tmp_home):
    r = run(tmp_home, "form-load", NAME)
    assert r.returncode == 1 and "nenhum formulário" in r.stderr and "Traceback" not in r.stderr


def test_form_load_without_a_path_ignores_files_without_a_marker(tmp_home):
    forms = tmp_home / "forms"
    forms.mkdir()
    (forms / "questionario-maria-exemplo.txt").write_text("rascunho qualquer\n", encoding="utf-8")
    assert run(tmp_home, "form-load", NAME).returncode == 1


def archived(tmp_home):
    return sorted((pdir(tmp_home) / "forms").glob("*.txt")) if (pdir(tmp_home) / "forms").exists() else []


def test_a_loaded_interview_is_collected_out_of_downloads(tmp_home):
    forms = tmp_home / "forms"
    forms.mkdir()
    fill_name(forms / "questionario-maria-exemplo.txt")
    r = run(tmp_home, "form-load", NAME)
    assert r.returncode == 0 and "recolhido:" in r.stdout
    assert list(forms.iterdir()) == []
    [kept] = archived(tmp_home)
    assert kept.name == "questionario-maria-exemplo.txt" and kept.stat().st_mode & 0o777 == 0o600
    assert (pdir(tmp_home) / "forms").stat().st_mode & 0o777 == 0o700
    assert run(tmp_home, "form-load", NAME).returncode == 1  # nothing left to read


def test_a_form_with_errors_stays_in_downloads_for_correction(tmp_home):
    forms = tmp_home / "forms"
    forms.mkdir()
    (forms / "questionario-maria-exemplo.txt").write_text(
        FIXTURE.read_text(encoding="utf-8").replace("Idade: 28", "Idade: vinte"), encoding="utf-8")
    assert run(tmp_home, "form-load", NAME).returncode == 1
    assert [p.name for p in forms.iterdir()] == ["questionario-maria-exemplo.txt"] and archived(tmp_home) == []


def test_a_partial_test_stays_and_a_complete_one_is_collected(tmp_home):
    bank = load_bank()
    ids = [i.id for i in bank]
    forms = tmp_home / "forms"
    run(tmp_home, "form-new", NAME, "teste")
    path = forms / "teste-maria-exemplo.txt"
    blank = path.read_text(encoding="utf-8")
    path.write_text(fill(blank, {i: 3 for i in ids[:40]}), encoding="utf-8")
    r = run(tmp_home, "form-load", NAME)
    assert "recolhido" not in r.stdout and path.exists()
    path.write_text(fill(blank, {i: (n % 5) + 1 for n, i in enumerate(ids)}), encoding="utf-8")
    r = run(tmp_home, "form-load", NAME)
    assert "recolhido:" in r.stdout and not path.exists() and [p.name for p in archived(tmp_home)] == ["teste-maria-exemplo.txt"]


def test_a_followup_is_collected_after_it_is_applied(tmp_home, tmp_path):
    forms = tmp_home / "forms"
    forms.mkdir()
    fill_name(forms / "questionario-maria-exemplo.txt")
    run(tmp_home, "form-load", NAME)
    gaps = run(tmp_home, "form-gaps", NAME)
    path = Path(gaps.stdout.strip().splitlines()[-1].split(": ", 1)[1])
    path.write_text("\n".join((l.rstrip() + " 15%") if l.startswith("@metric:0:1") else l
                              for l in path.read_text(encoding="utf-8").splitlines()), encoding="utf-8")
    r = run(tmp_home, "form-load", NAME)
    assert "aplicadas: 1" in r.stdout and "recolhido:" in r.stdout and list(forms.iterdir()) == []


def test_a_file_given_by_explicit_path_outside_downloads_is_left_alone(tmp_home, tmp_path):
    f = tmp_path / "meu-questionario.txt"
    shutil.copy(FIXTURE, f)
    r = run(tmp_home, "form-load", NAME, str(f))
    assert r.returncode == 0 and "recolhido" not in r.stdout and f.exists()


def test_collecting_never_overwrites_an_earlier_archived_form(tmp_home):
    forms = tmp_home / "forms"
    forms.mkdir()
    for _ in range(2):
        fill_name(forms / "questionario-maria-exemplo.txt")
        assert run(tmp_home, "form-load", NAME).returncode == 0
    assert [p.name for p in archived(tmp_home)] == ["questionario-maria-exemplo-2.txt", "questionario-maria-exemplo.txt"]


def test_report_save_copies_to_the_visible_folder_and_the_profile(tmp_home, tmp_path):
    env = {**os.environ, "JOBBOT_HOME": str(tmp_home), "JOBBOT_REPORTS_DIR": str(tmp_path / "docs")}
    src = tmp_path / "r.md"
    src.write_text("# Teste\nolá\n", encoding="utf-8")
    cmd = [sys.executable, "-m", "jobbot", "report-save", "Ana", "02-teste", str(src)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert r.returncode == 0 and (tmp_path / "docs" / "ana" / "02-teste.md").read_text(encoding="utf-8") == "# Teste\nolá\n"
    assert (tmp_home / "profiles" / "ana" / "reports" / "02-teste.md").exists()
    bad = subprocess.run([*cmd[:-2], "../x", str(src)], capture_output=True, text=True, env=env)
    assert bad.returncode == 1 and "inválido" in bad.stderr
