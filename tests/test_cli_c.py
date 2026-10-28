from datetime import date

import yaml

from jobbot.schema import Application, Assessment, Behavior, Constraints
from jobbot.store import update_profile
from tests.test_cli import run, write
from tests.test_cli_b2 import NAME, make_profile, pdir, posting, ready

TODAY = date.today().isoformat()


def profile_yaml(tmp_home):
    return yaml.safe_load((pdir(tmp_home) / "profile.yaml").read_text())


def lines(result):
    return result.stdout.splitlines()


def add_apps(n, platform="linkedin", status="enviada"):
    update_profile(NAME, lambda p: p.applications.extend(
        Application(date=TODAY, platform=platform, status=status, url=f"https://x/{platform}/{i}") for i in range(n)))


def test_round_check_fresh_profile(tmp_home):
    make_profile(tmp_home)
    out = lines(run(tmp_home, "round-check", NAME, "linkedin"))
    for expected in ("permitido: 10", "hoje: 0/30", "pendentes: 0", "pausada: nao", "examinar_ate: 50", "fit_mode: auto"):
        assert expected in out, expected


def test_round_check_after_thirty_prepared_today_is_zero(tmp_home):
    make_profile(tmp_home)
    add_apps(30)
    r = run(tmp_home, "round-check", NAME, "linkedin")
    assert "permitido: 0" in r.stdout and "limite diário" in r.stdout
    assert "permitido: 10" in run(tmp_home, "round-check", NAME, "indeed").stdout


def test_round_check_paused_and_released(tmp_home):
    make_profile(tmp_home)
    assert run(tmp_home, "platform-pause", NAME, "linkedin", "--reason", "captcha").returncode == 0
    paused = run(tmp_home, "round-check", NAME, "linkedin").stdout
    assert "pausada: sim" in paused and "permitido: 0" in paused and "captcha" in paused
    assert run(tmp_home, "platform-release", NAME, "linkedin").returncode == 0
    assert "permitido: 10" in run(tmp_home, "round-check", NAME, "linkedin").stdout


def test_vaga_check_repeated_and_filtered(tmp_home, tmp_path):
    make_profile(tmp_home, constraints=Constraints(modality=["remoto", "hibrido"], current_employer="Loja Modelo"))
    mine = run(tmp_home, "vaga-check", NAME, posting(tmp_path, company="Loja Modelo Ltda"), "--platform", "linkedin")
    assert "filtro: empregador_atual" in mine.stdout and "repetida: nao" in mine.stdout
    other = run(tmp_home, "vaga-check", NAME, posting(tmp_path, name="o.yaml", modality="presencial"), "--platform", "linkedin")
    assert "filtro: fora_das_restricoes" in other.stdout
    clean = run(tmp_home, "vaga-check", NAME, posting(tmp_path, name="c.yaml"), "--platform", "linkedin")
    assert "filtro: nao" in clean.stdout


def test_seen_add_then_vaga_check_repeated(tmp_home, tmp_path):
    make_profile(tmp_home)
    p = posting(tmp_path)
    assert run(tmp_home, "seen-add", NAME, "linkedin", p, "--reason", "falha").returncode == 0
    assert "repetida: falha" in run(tmp_home, "vaga-check", NAME, p, "--platform", "linkedin").stdout
    assert run(tmp_home, "seen-add", NAME, "linkedin", p, "--reason", "inventado").returncode == 1


def test_app_status_updates_by_url_and_rejects_bad_status_and_unknown_url(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    assert run(tmp_home, "vaga-resume", NAME, posting(tmp_path), "--platform", "linkedin").returncode == 0
    ok = run(tmp_home, "app-status", NAME, "https://x/1?utm_source=zzz", "enviada")
    assert ok.returncode == 0
    assert profile_yaml(tmp_home)["applications"][0]["status"] == "enviada"
    bad = run(tmp_home, "app-status", NAME, "https://x/1", "voando")
    assert bad.returncode == 1 and "status" in bad.stderr
    assert profile_yaml(tmp_home)["applications"][0]["status"] == "enviada"
    unknown = run(tmp_home, "app-status", NAME, "https://x/999", "enviada")
    assert unknown.returncode == 1 and "não encontrada" in unknown.stderr


def test_answers_resolve_prints_lines_and_registers_pending(tmp_home, tmp_path):
    make_profile(tmp_home)
    q = write(tmp_path / "q.yaml", ["Qual sua pretensão salarial?", "Qual seu animal favorito?", "Você é PCD?"])
    r = run(tmp_home, "answers-resolve", NAME, q, "--vaga", "Analista@Acme")
    out = lines(r)
    assert "geral | respondida | perfil | Qual sua pretensão salarial? | 5000" in out
    assert "geral | em_branco |  | Qual seu animal favorito? | " in out
    assert any(l.startswith("sensivel | em_branco") for l in out)
    pending = run(tmp_home, "pending-list", NAME).stdout
    assert "Qual seu animal favorito?" in pending and "Você é PCD?" in pending and "Analista@Acme" in pending
    assert "pretensão" not in pending


def test_answers_resolve_without_vaga_does_not_register_pending(tmp_home, tmp_path):
    make_profile(tmp_home)
    run(tmp_home, "answers-resolve", NAME, write(tmp_path / "q.yaml", ["Qual seu animal favorito?"]))
    assert run(tmp_home, "pending-list", NAME).stdout.strip() == ""


def test_answers_add_clears_pending_and_next_resolve_answers(tmp_home, tmp_path):
    make_profile(tmp_home)
    q = write(tmp_path / "q.yaml", ["Qual seu animal favorito?"])
    run(tmp_home, "answers-resolve", NAME, q, "--vaga", "v")
    a = write(tmp_path / "a.yaml", [{"question": "Qual seu animal favorito?", "answer": "Gato", "category": "geral"}])
    assert run(tmp_home, "answers-add", NAME, a).returncode == 0
    assert run(tmp_home, "pending-list", NAME).stdout.strip() == ""
    assert "geral | respondida | banco | Qual seu animal favorito? | Gato" in lines(run(tmp_home, "answers-resolve", NAME, q))
    bad = write(tmp_path / "bad.yaml", [{"question": "x", "answer": "y", "category": "secreta"}])
    assert run(tmp_home, "answers-add", NAME, bad).returncode == 1


def test_pending_list_and_clear(tmp_home, tmp_path):
    make_profile(tmp_home)
    run(tmp_home, "answers-resolve", NAME, write(tmp_path / "q.yaml", ["Qual seu animal favorito?"]), "--vaga", "v")
    assert "animal" in run(tmp_home, "pending-list", NAME).stdout
    assert run(tmp_home, "pending-clear", NAME).returncode == 0
    assert run(tmp_home, "pending-list", NAME).stdout.strip() == ""


def test_fit_risks_prints_flags_and_action_for_mode(tmp_home, tmp_path):
    make_profile(tmp_home)
    watched = write(tmp_path / "t1.txt", "Tempo limite de 30 minutos. Sua câmera ficará ligada.")
    out = lines(run(tmp_home, "fit-risks", NAME, watched))
    assert "flags: cronometrado, vigiado" in out and "acao: deixar_para_pessoa" in out
    plain = write(tmp_path / "t2.txt", "Responda sem ajuda de IA.")
    assert "acao: responder" in run(tmp_home, "fit-risks", NAME, plain).stdout
    assert run(tmp_home, "run-settings", NAME, "--fit-mode", "pular").returncode == 0
    both = lines(run(tmp_home, "fit-risks", NAME, plain))
    assert "flags: proibe_ia" in both and "acao: pular" in both


def test_behavior_prints_summary(tmp_home):
    make_profile(tmp_home, behavior=Behavior("Autonomia", ["aprender"], "especialista"),
                 assessments=[Assessment("2026-10-25", {"interesses.pratico": 90}, "alta")])
    out = lines(run(tmp_home, "behavior", NAME))
    assert "work_style: Autonomia" in out and "dimensoes_altas: interesses.pratico" in out
    assert "confiabilidade: alta" in out


def test_run_settings_update_and_validation(tmp_home):
    make_profile(tmp_home)
    r = run(tmp_home, "run-settings", NAME, "--per-round", "5", "--per-day", "12", "--max-examined", "20")
    assert r.returncode == 0 and "per_round: 5" in r.stdout and "per_day: 12" in r.stdout
    assert "permitido: 5" in run(tmp_home, "round-check", NAME, "linkedin").stdout
    bad = run(tmp_home, "run-settings", NAME, "--per-round", "0")
    assert bad.returncode == 1 and "per_round" in bad.stderr
    assert "per_round: 5" in run(tmp_home, "run-settings", NAME).stdout


def test_run_settings_autonomy(tmp_home):
    make_profile(tmp_home)
    assert "autonomy: full" in run(tmp_home, "run-settings", NAME).stdout
    assert "autonomy: assisted" in run(tmp_home, "run-settings", NAME, "--autonomy", "assisted").stdout
    bad = run(tmp_home, "run-settings", NAME, "--autonomy", "x")
    assert bad.returncode == 1 and "autonomy" in bad.stderr


def test_vaga_resume_platform_flag_sets_platform_and_seen_entry(tmp_home, tmp_path):
    ready(tmp_home, tmp_path)
    p = posting(tmp_path)
    assert run(tmp_home, "vaga-resume", NAME, p, "--platform", "linkedin").returncode == 0
    data = profile_yaml(tmp_home)
    assert data["applications"][0]["platform"] == "linkedin"
    assert data["seen"][0]["reason"] == "preparada" and data["seen"][0]["platform"] == "linkedin"
    out = run(tmp_home, "round-check", NAME, "linkedin").stdout
    assert "hoje: 1/30" in out and "pendentes: 1" in out
    assert "repetida: repetida" in run(tmp_home, "vaga-check", NAME, p, "--platform", "linkedin").stdout


def test_bad_platform_exits_1(tmp_home, tmp_path):
    make_profile(tmp_home)
    r = run(tmp_home, "round-check", NAME, "orkut")
    assert r.returncode == 1 and "plataforma" in r.stderr and "Traceback" not in r.stderr
    assert run(tmp_home, "vaga-resume", NAME, posting(tmp_path), "--platform", "orkut").returncode == 1


def test_corrupt_profile_clean_error(tmp_home):
    make_profile(tmp_home)
    (pdir(tmp_home) / "profile.yaml").write_text("a: [")
    r = run(tmp_home, "round-check", NAME, "linkedin")
    assert r.returncode == 1 and "profile.yaml" in r.stderr and "Traceback" not in r.stderr


def test_files_stay_0600(tmp_home, tmp_path):
    make_profile(tmp_home)
    run(tmp_home, "platform-pause", NAME, "gupy", "--reason", "aviso")
    run(tmp_home, "answers-add", NAME, write(tmp_path / "a.yaml", [{"question": "x y z", "answer": "1"}]))
    assert (pdir(tmp_home) / "profile.yaml").stat().st_mode & 0o777 == 0o600
