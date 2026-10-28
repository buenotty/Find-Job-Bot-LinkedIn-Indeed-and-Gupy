import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = {"jobbot-interview", "jobbot-market", "jobbot-profiles", "jobbot-posts",
          "jobbot-assessment", "jobbot-orientation", "jobbot-courses",
          "jobbot-types", "jobbot-resume", "jobbot-round", "jobbot-status", "jobs-master"}
NOTICE = ("Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. "
          "O risco para a conta é de cada pessoa.")


def skill_files():
    return sorted((ROOT / "skills").glob("*/SKILL.md"))


def test_expected_skills_exist():
    assert {f.parent.name for f in skill_files()} == SKILLS


@pytest.mark.parametrize("f", skill_files(), ids=lambda f: f.parent.name)
def test_each_skill_has_frontmatter(f):
    text = f.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    meta = yaml.safe_load(text.split("---\n")[1])
    assert meta["name"] == f.parent.name
    assert meta["description"].strip()


def test_notice_in_interview_skill():
    assert NOTICE in (ROOT / "skills/jobbot-interview/SKILL.md").read_text(encoding="utf-8")


def test_referenced_files_exist():
    for f in skill_files():
        for ref in re.findall(r"references/[\w-]+\.md", f.read_text(encoding="utf-8")):
            assert (ROOT / ref).exists(), f"{f.parent.name} cites missing {ref}"


def repo_markdown():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / p for p in out if p.endswith(".md")]


def words(text):
    return re.findall(r"\w+", text.lower())


@pytest.mark.skipif(not os.environ.get("JOBBOT_EBOOK_TXT"), reason="set JOBBOT_EBOOK_TXT to run")
def test_no_ebook_text():
    ebook = words(Path(os.environ["JOBBOT_EBOOK_TXT"]).read_text(encoding="utf-8"))
    shingles = {tuple(ebook[i:i + 8]) for i in range(len(ebook) - 7)}
    for f in repo_markdown():
        w = words(f.read_text(encoding="utf-8"))
        hit = next((tuple(w[i:i + 8]) for i in range(len(w) - 7) if tuple(w[i:i + 8]) in shingles), None)
        assert hit is None, f"{f.name} copies ebook text: {' '.join(hit or ())}"


def test_no_owner_data_outside_docs():
    banned = re.compile("|".join(["sam" + "uel", "bue" + "notty", "vi" + "pp"]), re.I)
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    for p in out:
        if p.startswith(("docs/", ".claude-plugin/")) or p.endswith(".pyc"):
            continue  # the publisher handle is legitimate in plugin metadata and install commands
        text = (ROOT / p).read_text(encoding="utf-8", errors="ignore").replace("bue" + "notty/jobbot", "")
        assert not banned.search(text), p


def test_interview_skill_warns_that_put_replaces_lists():
    text = (ROOT / "skills/jobbot-interview/SKILL.md").read_text(encoding="utf-8")
    assert "reenvie a lista inteira" in text


def read_skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_assessment_skill_has_caveat_and_commands():
    text = read_skill("jobbot-assessment")
    assert "não é diagnóstico" in text
    for cmd in ("assess-status", "assess-answer", "assess-finish"):
        assert cmd in text


def test_courses_skill_mentions_query_date_and_never_invents():
    text = read_skill("jobbot-courses")
    assert "data da consulta" in text and "nunca invente" in text.lower()
    for cmd in ("project-match", "course-add", "band"):
        assert cmd in text


def test_orientation_skill_uses_market_claims_and_targets():
    text = read_skill("jobbot-orientation")
    assert "market-claims" in text and "target-add" in text
    assert "references/honest-career-talk.md" in text


def test_assessment_skill_does_not_promise_per_layer_redo():
    text = read_skill("jobbot-assessment")
    assert "refazer a camada" not in text and "refazer o teste inteiro" in text


def test_orientation_skill_words_paga_pouco_against_expectation():
    assert "abaixo da sua pretensão" in read_skill("jobbot-orientation")


def test_courses_skill_has_provisional_syllabus_list():
    text = read_skill("jobbot-courses")
    assert "lista provisória" in text and "sem dado de mercado" in text


def test_types_skill_uses_type_commands():
    text = read_skill("jobbot-types")
    for cmd in ("type-define", "type-resume", "type-list"):
        assert cmd in text
    assert "references/resume-writing.md" in text


def test_resume_skill_uses_vaga_commands_and_forbids_inventing():
    text = read_skill("jobbot-resume")
    for cmd in ("vaga-eval", "vaga-resume"):
        assert cmd in text
    assert "nunca invente" in text.lower() and "references/resume-writing.md" in text


def test_resume_writing_reference_bans_hidden_text():
    text = (ROOT / "references" / "resume-writing.md").read_text(encoding="utf-8")
    assert "texto escondido" in text.lower() and "XYZ" in text and "Competências" in text


def test_interview_and_types_skills_explain_project_kind_and_start():
    for name in ("jobbot-interview", "jobbot-types"):
        text = read_skill(name)
        assert "kind" in text and "start" in text and "autodidata" in text, name


def test_resume_skill_asks_the_person_to_approve_the_pdf_and_names_the_limits():
    text = read_skill("jobbot-resume")
    assert "aprove" in text.lower() and "texto livre" in text.lower()
    assert "texto livre" in (ROOT / "README.md").read_text(encoding="utf-8").lower()


def test_interview_skill_collects_education():
    text = read_skill("jobbot-interview")
    assert "education" in text and "graduacao" in text and "cursando" in text


def test_round_skill_commands_and_notice():
    text = read_skill("jobbot-round")
    for cmd in ("round-check", "vaga-check", "vaga-eval", "vaga-resume", "answers-resolve", "answers-add",
                "fit-risks", "behavior", "platform-pause", "seen-add", "app-status"):
        assert cmd in text, cmd
    assert NOTICE in text and "references/platforms.md" in text


def test_round_skill_autonomy_and_hard_limits():
    text = read_skill("jobbot-round").lower()
    assert "--autonomy" in text and "`full`" in text and "`assisted`" in text
    assert "nunca digite rg, cpf" in text and "nunca invente dado" in text
    assert "não clique em enviar" in text  # assisted mode still stops before sending


def test_status_skill_commands():
    text = read_skill("jobbot-status")
    for cmd in ("round-check", "app-status", "platform-release"):
        assert cmd in text, cmd


def test_platforms_reference_lists_stop_conditions():
    text = (ROOT / "references" / "platforms.md").read_text(encoding="utf-8").lower()
    for word in ("captcha", "verificação", "login", "atividade incomum", "em paralelo"):
        assert word in text, word


def test_round_skill_asks_when_behavior_data_is_blank_and_keeps_pending_questions():
    text = read_skill("jobbot-round").lower()
    assert "tudo em branco" in text and "pergunte à pessoa" in text
    assert "só rode `jobbot pending-clear" in text and "descartar" in text


def test_master_skill_routes_the_whole_flow():
    text = read_skill("jobs-master")
    assert "jobbot next" in text and NOTICE in text
    for name in ("jobbot-interview", "jobbot-market", "jobbot-profiles", "jobbot-assessment",
                 "jobbot-types", "jobbot-round", "jobbot-status"):
        assert name in text, name


def test_platform_notes_cover_linkedin_load_wait_and_added_filters():
    text = (ROOT / "references" / "platforms.md").read_text(encoding="utf-8").lower()
    assert "4 segundos" in text and "leitura vazia" in text and "filtros" in text
    round_text = read_skill("jobbot-round").lower()
    assert "aguarde" in round_text and "leitura vazia" in round_text


def test_honesty_reference_explains_adjacent_skills():
    text = (ROOT / "references" / "honesty-and-stretch.md").read_text(encoding="utf-8").lower()
    assert "adjacente" in text and "sql server" in text and "competências" in text


def test_interview_and_assessment_skills_use_text_forms_not_chat_blocks():
    interview = read_skill("jobbot-interview")
    for cmd in ("form-new", "form-load", "form-gaps"):
        assert cmd in interview, cmd
    assert "uma única mensagem" in interview and "no máximo um" in interview
    assessment = read_skill("jobbot-assessment")
    assert "form-new" in assessment and "form-load" in assessment and "depois do sinal" in assessment
    assert "10 a 15" not in assessment and "uma etapa por vez" not in interview.lower()


def test_form_skills_point_to_the_visible_downloads_folder_and_load_without_a_path():
    for name in ("jobbot-interview", "jobbot-assessment"):
        text = read_skill(name)
        assert "Downloads" in text and "sem caminho" in text and "pasta oculta" not in text.replace("não numa pasta oculta", ""), name


def test_form_skills_explain_that_loaded_forms_are_collected():
    for name in ("jobbot-interview", "jobbot-assessment"):
        assert "recolh" in read_skill(name), name


def test_posts_skill_keeps_discretion_and_never_publishes_alone():
    text = read_skill("jobbot-posts")
    assert NOTICE in text
    for rule in ("Discrição", "Confidencialidade", "Nunca publique sozinho", "jobbot check",
                 "linkedin-content-planner", "linkedin-post-writer", "report-save"):
        assert rule in text, rule
