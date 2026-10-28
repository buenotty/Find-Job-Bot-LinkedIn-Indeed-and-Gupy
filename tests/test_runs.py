from datetime import date

import pytest

from jobbot.posting import Posting
from jobbot.runs import alt_key, capacity, filter_reason, mark_seen, seen_reason, vaga_key
from jobbot.schema import Application, Constraints, PlatformState, Profile, RunSettings, SeenPosting

TODAY = date(2026, 10, 25)


def app(platform="linkedin", status="enviada", day="2026-10-25", url="", company="", title=""):
    return Application(date=day, platform=platform, status=status, url=url, company=company, title=title)


def test_vaga_key_ignores_tracking_trailing_slash_case_and_fragment():
    a = vaga_key("https://www.LinkedIn.com/jobs/view/12345/?trackingId=abc&refId=x#frag")
    b = vaga_key("http://linkedin.com/jobs/view/12345")
    assert a == b == "linkedin.com/jobs/view/12345"


def test_vaga_key_keeps_indeed_jk_and_linkedin_current_job_id():
    assert vaga_key("https://br.indeed.com/viewjob?jk=ABC123&utm_source=x") == "br.indeed.com/viewjob?jk=abc123"
    assert vaga_key("https://br.indeed.com/viewjob?jk=abc123") != vaga_key("https://br.indeed.com/viewjob?jk=zzz999")
    key = vaga_key("https://www.linkedin.com/jobs/collections/recommended/?currentJobId=999&x=1")
    assert key == "linkedin.com/jobs/collections/recommended?currentjobid=999"


def test_vaga_key_without_scheme_and_empty():
    assert vaga_key("linkedin.com/jobs/view/1/") == "linkedin.com/jobs/view/1"
    assert vaga_key("") == "" and vaga_key("   ") == ""


def test_alt_key_normalizes_accents_and_case():
    assert alt_key("Acme  Dados", "Analista de Dados") == alt_key("ACME dados", "Analista  de dados")
    assert alt_key("Ação", "Técnico") == "acao|tecnico"


def test_seen_by_url_in_seen_and_in_applications():
    p = Profile(seen=[SeenPosting(key="linkedin.com/jobs/view/1", platform="linkedin", reason="empresa_vetada")],
                applications=[app(url="https://gupy.io/vaga/55?utm=x", platform="gupy")])
    assert seen_reason(p, "https://www.linkedin.com/jobs/view/1/?t=1", "", "", "linkedin") == "empresa_vetada"
    assert seen_reason(p, "https://gupy.io/vaga/55", "", "", "gupy") == "repetida"
    assert seen_reason(p, "https://gupy.io/vaga/56", "", "", "gupy") is None


def test_seen_reason_preparada_reads_as_repetida():
    p = Profile(seen=[SeenPosting(key="a.com/1", platform="indeed", reason="preparada")])
    assert seen_reason(p, "https://a.com/1", "", "", "indeed") == "repetida"


def test_seen_across_platforms_by_company_and_title():
    p = Profile(applications=[app(platform="linkedin", url="https://linkedin.com/jobs/view/1",
                                  company="Acme Dados", title="Analista de Dados")])
    assert seen_reason(p, "https://gupy.io/vaga/9", "ACME dados", "Analista de dados", "gupy") == "repetida"


def test_same_company_and_title_on_same_platform_with_different_url_is_not_a_repeat():
    p = Profile(applications=[app(platform="linkedin", url="https://linkedin.com/jobs/view/1",
                                  company="Acme", title="Analista")])
    assert seen_reason(p, "https://linkedin.com/jobs/view/2", "Acme", "Analista", "linkedin") is None


def post(**kw):
    base = dict(title="Analista", company="Acme", skills=["SQL"])
    base.update(kw)
    return Posting(**base)


def test_filter_current_employer_and_vetoed_company_substring_and_accents():
    p = Profile(constraints=Constraints(current_employer="Loja Modelo", vetoed_companies=["Empresa Vetada", ""]))
    assert filter_reason(post(company="LOJA MODELO LTDA"), p) == "empregador_atual"
    assert filter_reason(post(company="Émpresa vetada S.A."), p) == "empresa_vetada"
    assert filter_reason(post(company="Acme"), p) is None


def test_filter_empty_current_employer_never_matches_everything():
    assert filter_reason(post(company="Qualquer"), Profile(constraints=Constraints(current_employer=None))) is None
    assert filter_reason(post(company="Qualquer"), Profile(constraints=Constraints(current_employer=""))) is None


def test_filter_constraints():
    p = Profile(constraints=Constraints(modality=["remoto"]))
    assert filter_reason(post(modality="presencial"), p) == "fora_das_restricoes"
    assert filter_reason(post(modality="remoto"), p) is None


def test_filter_none_for_clean_vacancy():
    assert filter_reason(post(), Profile()) is None


@pytest.mark.parametrize("done,allowed", [(0, 10), (9, 10), (20, 10), (25, 5), (29, 1), (30, 0)])
def test_capacity_boundaries(done, allowed):
    p = Profile(applications=[app() for _ in range(done)])
    cap = capacity(p, "linkedin", TODAY)
    assert (cap.allowed, cap.today) == (allowed, done)
    if done == 30:
        assert "limite diário" in cap.reason


def test_capacity_blocked_and_filtered_not_counted():
    p = Profile(applications=[app(status="bloqueada") for _ in range(20)])
    assert capacity(p, "linkedin", TODAY).today == 0


def test_capacity_per_platform_independent():
    p = Profile(applications=[app("linkedin") for _ in range(30)])
    assert capacity(p, "linkedin", TODAY).allowed == 0 and capacity(p, "indeed", TODAY).allowed == 10


def test_capacity_ten_pending_blocks_new_round():
    p = Profile(applications=[app(status="preparado", day="2026-10-24") for _ in range(10)])
    cap = capacity(p, "linkedin", TODAY)
    assert cap.allowed == 0 and cap.pending == 10 and "revise" in cap.reason


def test_capacity_paused_blocks_with_reason():
    p = Profile(platforms=[PlatformState("indeed", True, "captcha", "2026-10-24")])
    cap = capacity(p, "indeed", TODAY)
    assert cap.allowed == 0 and cap.paused and "pausada" in cap.reason and "captcha" in cap.reason


def test_capacity_next_day_resets_counter_but_not_pause():
    p = Profile(applications=[app() for _ in range(30)], platforms=[PlatformState("linkedin", True, "aviso")])
    nxt = capacity(p, "linkedin", date(2026, 10, 26))
    assert nxt.today == 0 and nxt.paused and nxt.allowed == 0
    p.platforms = []
    assert capacity(p, "linkedin", date(2026, 10, 26)).allowed == 10


def test_capacity_respects_custom_limits():
    p = Profile(run=RunSettings(per_round=3, per_day=5), applications=[app() for _ in range(4)])
    assert capacity(p, "linkedin", TODAY).allowed == 1


def test_mark_seen_no_duplicates_and_updates_reason():
    p = Profile()
    mark_seen(p, "linkedin", Posting(title="Analista", company="Acme", url="https://linkedin.com/jobs/view/1?x=1"), "falha", TODAY)
    mark_seen(p, "linkedin", Posting(title="Analista", company="Acme", url="https://linkedin.com/jobs/view/1"), "preparada", TODAY)
    assert len(p.seen) == 1 and p.seen[0].reason == "preparada"
    assert p.seen[0].key == "linkedin.com/jobs/view/1" and p.seen[0].alt_key == "acme|analista"
    mark_seen(p, "gupy", Posting(title="Analista", company="Acme", url="https://linkedin.com/jobs/view/1"), "repetida", TODAY)
    assert len(p.seen) == 2
