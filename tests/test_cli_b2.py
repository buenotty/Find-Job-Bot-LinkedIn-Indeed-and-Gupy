import os

import yaml

from jobbot.pdf import extract_text
from jobbot.schema import (
    Bullet, Constraints, Experience, Profile, Project, Screening, Skill, Target,
)
from jobbot.store import save_profile
from tests.test_cli import run, write

NAME = "Maria"
ANALISTA = "Analista de Dados"
HARDWARE = "Técnico de Hardware"
OWNED = ["SQL", "Power BI", "Excel", "Python", "Montagem de computadores", "Diagnóstico de hardware"]


def make_profile(tmp_home, **kw):
    p = Profile(
        name="Maria Exemplo", age=28, state="RJ", city="Rio de Janeiro",
        experiences=[Experience("Loja Modelo", ANALISTA, "2021-02", None, [Bullet("Automatizei relatórios", "30%")])],
        skills=[Skill(s, "medio") for s in OWNED],
        projects=[Project("Montagem de PCs", "Monto computadores", None, "autodidata", "2022-03", None)],
        targets=[
            Target(role=ANALISTA, group="agora", source="sugerida", required_skills=["SQL", "Power BI", "Excel"]),
            Target(role=HARDWARE, group="agora", source="propria",
                   required_skills=["Montagem de computadores", "Diagnóstico de hardware"]),
            Target(role="Cozinheiro", group="sem_dado", source="propria"),
        ],
        constraints=Constraints(modality=["remoto", "hibrido"]),
        screening=Screening(salary_expectation=5000, contract="CLT", email="m@example.com", phone="21999990000"),
    )
    for k, v in kw.items():
        setattr(p, k, v)
    save_profile(NAME, p)


def pdir(tmp_home):
    return tmp_home / "profiles" / "maria"


def define_type(tmp_home, tmp_path, role, **extra):
    return run(tmp_home, "type-define", NAME, write(tmp_path / f"t-{abs(hash(role))}.yaml", {"role": role, **extra}))


def type_resume(tmp_home, tmp_path, role, summary="Profissional focada em resultados."):
    content = {"summary": summary, "skill_order": ["SQL"]}
    return run(tmp_home, "type-resume", NAME, role, write(tmp_path / f"c-{abs(hash(role))}.yaml", content))


def posting(tmp_path, name="p.yaml", **kw):
    data = {"title": "Analista de Dados", "company": "Acme", "skills": ["SQL", "Power BI", "Excel", "Kafka"],
            "salary": 6000, "modality": "hibrido", "contract": "CLT", "url": "https://x/1"}
    data.update(kw)
    return write(tmp_path / name, data)


def ready(tmp_home, tmp_path, hardware=False):
    make_profile(tmp_home)
    assert define_type(tmp_home, tmp_path, ANALISTA, salary_floor=5000).returncode == 0
    assert type_resume(tmp_home, tmp_path, ANALISTA).returncode == 0
    if hardware:
        assert define_type(tmp_home, tmp_path, HARDWARE, salary_floor=2500).returncode == 0
        assert type_resume(tmp_home, tmp_path, HARDWARE).returncode == 0


def test_type_define_requires_releasable_target(tmp_home, tmp_path):
    make_profile(tmp_home)
    r = define_type(tmp_home, tmp_path, "Cozinheiro")
    assert r.returncode == 1 and "liberada" in r.stderr and "Traceback" not in r.stderr


def test_type_define_upserts_and_type_list_shows_liberado(tmp_home, tmp_path):
    make_profile(tmp_home)
    define_type(tmp_home, tmp_path, ANALISTA, salary_floor=5000)
    r = define_type(tmp_home, tmp_path, ANALISTA, salary_floor=6000)
    assert r.returncode == 0 and "piso: 6000" in r.stdout
    out = run(tmp_home, "type-list", NAME).stdout
    assert out.count(ANALISTA) == 1 and "liberado: sim" in out and HARDWARE in out  # hardware listed as undefined


def test_type_resume_writes_yaml_and_pdf_0600(tmp_home, tmp_path):
    make_profile(tmp_home)
    define_type(tmp_home, tmp_path, ANALISTA)
    r = type_resume(tmp_home, tmp_path, ANALISTA)
    assert r.returncode == 0
    pdf = pdir(tmp_home) / "types" / "analista-de-dados.pdf"
    assert pdf.exists() and pdf.stat().st_mode & 0o777 == 0o600
    assert (pdir(tmp_home) / "types" / "analista-de-dados.yaml").stat().st_mode & 0o777 == 0o600
    assert "Maria Exemplo" in extract_text(pdf)


def test_type_resume_requires_defined_type(tmp_home, tmp_path):
    make_profile(tmp_home)
    r = type_resume(tmp_home, tmp_path, ANALISTA)
    assert r.returncode == 1 and "type-define" in r.stderr


def test_vaga_eval_output_keys(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    r = run(tmp_home, "vaga-eval", NAME, posting(tmp_path))
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    for expected in ("classificacao: tipo", f"tipo: {ANALISTA}", "match: 75", "acao: esticar_marcado",
                     "faltam: Kafka", "esticadas: Kafka", "arriscada: nao", "abaixo_do_piso: nao", "restricoes: ok"):
        assert expected in lines, expected


def test_vaga_eval_empty_skills_exits_1_cleanly(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    r = run(tmp_home, "vaga-eval", NAME, posting(tmp_path, skills=[]))
    assert r.returncode == 1 and "sem lista de skills" in r.stderr and "Traceback" not in r.stderr


def test_vaga_resume_tipo_generates_pdf_review_and_log(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    r = run(tmp_home, "vaga-resume", NAME, posting(tmp_path))
    assert r.returncode == 0 and "modo: tipo" in r.stdout
    files = sorted((pdir(tmp_home) / "resumes").iterdir())
    pdfs = [f for f in files if f.suffix == ".pdf"]
    sheets = [f for f in files if f.name.endswith(".review.txt")]
    assert len(pdfs) == 1 and len(sheets) == 1
    assert all(f.stat().st_mode & 0o777 == 0o600 for f in files)
    text = extract_text(pdfs[0])
    assert "Kafka" in text.split("Competências")[1] and "Kafka" not in text.split("Competências")[0]
    assert "Kafka" in sheets[0].read_text(encoding="utf-8")
    log = yaml.safe_load((pdir(tmp_home) / "profile.yaml").read_text())["applications"]
    assert len(log) == 1 and log[0]["mode"] == "tipo" and log[0]["status"] == "preparado"
    assert log[0]["file"].startswith("resumes/")


def test_vaga_resume_content_file_overrides_summary(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    cf = write(tmp_path / "cf.yaml", {"summary": "Resumo novo para esta vaga."})
    assert run(tmp_home, "vaga-resume", NAME, posting(tmp_path), "--content-file", cf).returncode == 0
    pdf = next((pdir(tmp_home) / "resumes").glob("*.pdf"))
    assert "Resumo novo para esta vaga." in extract_text(pdf)


def test_vaga_resume_risky_has_no_stretched_skills_in_pdf(tmp_home, tmp_path):
    ready(tmp_home, tmp_path, hardware=True)
    p = posting(tmp_path, title="Técnico de Hardware", skills=["Montagem de computadores", "Redes", "Cabeamento", "Linux", "Docker"])
    r = run(tmp_home, "vaga-resume", NAME, p)
    assert r.returncode == 0 and "arriscada: sim" in r.stdout
    pdf = next((pdir(tmp_home) / "resumes").glob("*.pdf"))
    text = extract_text(pdf)
    for missing in ("Redes", "Cabeamento", "Linux", "Docker"):
        assert missing not in text
    assert "Redes" in next((pdir(tmp_home) / "resumes").glob("*.review.txt")).read_text(encoding="utf-8")


def test_vaga_resume_ambiguo_exits_1_and_type_flag_resolves(tmp_home, tmp_path):
    ready(tmp_home, tmp_path, hardware=True)
    p = posting(tmp_path, title="Analista Hardware", skills=["Windows"])
    r = run(tmp_home, "vaga-resume", NAME, p)
    assert r.returncode == 1 and ANALISTA in r.stderr and HARDWARE in r.stderr and "--type" in r.stderr
    assert run(tmp_home, "vaga-resume", NAME, p, "--type", HARDWARE).returncode == 0


def test_vaga_resume_sem_tipo_below_criterion_exits_1(tmp_home, tmp_path):
    make_profile(tmp_home)
    r = run(tmp_home, "vaga-resume", NAME, posting(tmp_path, title="Contador", skills=["Cobol", "Fiscal"]))
    assert r.returncode == 1 and "vaga boa" in r.stderr
    assert not (pdir(tmp_home) / "resumes").exists()


def test_vaga_resume_do_zero_generates_pdf(tmp_home, tmp_path):
    make_profile(tmp_home)
    p = posting(tmp_path, title="Especialista BI", skills=["SQL", "Power BI", "Excel"])
    assert run(tmp_home, "vaga-resume", NAME, p).returncode == 1  # needs a content file
    cf = write(tmp_path / "cf.yaml", {"summary": "Especialista em BI.", "skill_order": ["Power BI"]})
    r = run(tmp_home, "vaga-resume", NAME, p, "--content-file", cf)
    assert r.returncode == 0 and "modo: do_zero" in r.stdout
    assert "Power BI" in extract_text(next((pdir(tmp_home) / "resumes").glob("*.pdf")))


def test_vaga_resume_twice_for_one_posting_rewrites_one_file_and_one_record(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    for _ in range(2):
        assert run(tmp_home, "vaga-resume", NAME, posting(tmp_path)).returncode == 0
    assert len(list((pdir(tmp_home) / "resumes").glob("*.pdf"))) == 1
    assert len(yaml.safe_load((pdir(tmp_home) / "profile.yaml").read_text())["applications"]) == 1


def test_resume_file_name_is_generic_with_a_code_and_never_names_the_company(tmp_home, tmp_path):
    import re
    ready(tmp_home, tmp_path)
    assert run(tmp_home, "vaga-resume", NAME, posting(tmp_path, company="Acme Corp", title="Analista de Dados")).returncode == 0
    names = [f.name for f in (pdir(tmp_home) / "resumes").iterdir()]
    assert names and all(re.fullmatch(r"curriculo-[a-z0-9-]+-[0-9A-F]{5}\.(pdf|review\.txt)", n) for n in names), names
    assert not any("acme" in n.lower() or "analista" in n.lower() for n in names)


def test_vaga_resume_unsafe_company_and_title_names(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    for i, (company, title) in enumerate([("../x", "Analista de Dados / ç"), ("", "Analista de Dados")]):
        r = run(tmp_home, "vaga-resume", NAME, posting(tmp_path, name=f"p{i}.yaml", company=company, title=title))
        assert r.returncode == 0, r.stderr
    root = (pdir(tmp_home) / "resumes").resolve()
    for f in root.iterdir():
        assert f.resolve().parent == root and ".." not in f.name
    assert len(list(root.glob("*.pdf"))) >= 1


def test_vaga_resume_without_type_resume_gives_clear_error(tmp_home, tmp_path):
    make_profile(tmp_home)
    define_type(tmp_home, tmp_path, ANALISTA)
    r = run(tmp_home, "vaga-resume", NAME, posting(tmp_path))
    assert r.returncode == 1 and "type-resume" in r.stderr and "Traceback" not in r.stderr


def test_vaga_resume_invented_number_exits_1_and_writes_nothing(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    cf = write(tmp_path / "cf.yaml", {"summary": "Reduzi custos em 70% na empresa."})
    r = run(tmp_home, "vaga-resume", NAME, posting(tmp_path), "--content-file", cf)
    assert r.returncode == 1 and "70%" in r.stderr
    assert not (pdir(tmp_home) / "resumes").exists()
    assert yaml.safe_load((pdir(tmp_home) / "profile.yaml").read_text())["applications"] == []


def test_applications_lists_records(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    run(tmp_home, "vaga-resume", NAME, posting(tmp_path))
    out = run(tmp_home, "applications", NAME).stdout
    assert "Acme" in out and ANALISTA in out and "75" in out and "resumes/" in out


def test_corrupt_profile_is_clean_error(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    (pdir(tmp_home) / "profile.yaml").write_text("a: [")
    r = run(tmp_home, "vaga-eval", NAME, posting(tmp_path))
    assert r.returncode == 1 and "profile.yaml" in r.stderr and "Traceback" not in r.stderr


def test_vaga_resume_risky_rejects_missing_skill_named_in_summary(tmp_home, tmp_path):
    ready(tmp_home, tmp_path, hardware=True)
    p = posting(tmp_path, title="Técnico de Hardware", skills=["Montagem de computadores", "Redes", "Cabeamento", "Linux", "Docker"])
    cf = write(tmp_path / "cf.yaml", {"summary": "Técnico com experiência em Redes e Docker."})
    r = run(tmp_home, "vaga-resume", NAME, p, "--content-file", cf)
    assert r.returncode == 1 and "Redes" in r.stderr
    assert not (pdir(tmp_home) / "resumes").exists()


def test_non_latin1_character_warns_on_stderr_and_notes_in_review(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    cf = write(tmp_path / "cf.yaml", {"summary": "Foco em dados ≥ fontes públicas."})
    r = run(tmp_home, "vaga-resume", NAME, posting(tmp_path), "--content-file", cf)
    assert r.returncode == 0 and "Latin-1" in r.stderr and "≥" in r.stderr
    sheet = next((pdir(tmp_home) / "resumes").glob("*.review.txt")).read_text(encoding="utf-8")
    assert "Latin-1" in sheet


def test_vaga_resume_never_claims_an_adjacent_skill_in_the_text(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    p = posting(tmp_path, skills=["SQL Server", "Power BI", "Excel"])
    out = run(tmp_home, "vaga-eval", NAME, p).stdout
    assert "adjacentes: SQL Server (SQL)" in out
    cf = write(tmp_path / "cf.yaml", {"summary": "Analista com experiência em SQL Server."})
    r = run(tmp_home, "vaga-resume", NAME, p, "--content-file", cf)
    assert r.returncode == 1 and "SQL Server" in r.stderr
    assert run(tmp_home, "vaga-resume", NAME, p).returncode == 0
    sheet = next((pdir(tmp_home) / "resumes").glob("*.review.txt")).read_text(encoding="utf-8")
    assert "você tem SQL" in sheet
