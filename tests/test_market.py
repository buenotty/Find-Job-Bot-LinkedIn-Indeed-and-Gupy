from jobbot.market import CORE_SHARE, Job, build_report, rank_focus
from jobbot.schema import Profile, Skill


def J(skills, **kw):
    return Job("Vaga", "Empresa", skills, **kw)


def report_with_skills(role, skill_lists):
    return build_report(role, [J(s) for s in skill_lists])


def test_core_share_is_forty():
    assert CORE_SHARE == 40


def test_zero_jobs_report():
    r = build_report("Analista", [])
    assert (r.n_jobs, r.top_skills, r.salary_median, r.applicants_median) == (0, [], None, None)


def test_skill_merge_across_spellings():
    r = build_report("A", [J(["SQL"]), J(["sql "]), J(["Sql"])])
    assert r.top_skills == [("SQL", 100)]


def test_skill_counted_once_per_job():
    r = build_report("A", [J(["SQL", "sql"]), J([])])
    assert r.top_skills == [("SQL", 50)]


def test_top_skills_capped_and_sorted():
    jobs = [J([f"s{i}" for i in range(20)]), J(["s0"])]
    r = build_report("A", jobs)
    assert len(r.top_skills) == 15
    assert r.top_skills[0] == ("s0", 100)


def test_salary_median_ignores_missing_and_uses_midpoint():
    jobs = [J([], salary_min=4000, salary_max=6000), J([], salary_min=7000), J([])]
    assert build_report("A", jobs).salary_median == 6000


def test_applicants_all_missing():
    assert build_report("A", [J(["x"]), J(["y"])]).applicants_median is None


def test_applicants_median():
    jobs = [J([], applicants=10), J([], applicants=30), J([])]
    assert build_report("A", jobs).applicants_median == 20


def test_core_threshold_39_vs_40():
    jobs = [J((["A"] if i < 39 else []) + (["B"] if i < 40 else [])) for i in range(100)]
    row = rank_focus([build_report("R", jobs)], Profile())[0]
    assert row.missing == ["B"]


def test_rank_by_coverage_then_demand():
    p = Profile(skills=[Skill("SQL")])
    low = report_with_skills("Baixa", [["SQL", "Kafka"]] * 3)          # 50%
    high_small = report_with_skills("Alta pequena", [["SQL"]] * 2)      # 100%, 2 jobs
    high_big = report_with_skills("Alta grande", [["SQL"]] * 5)         # 100%, 5 jobs
    rows = rank_focus([low, high_small, high_big], p)
    assert [r.role for r in rows] == ["Alta grande", "Alta pequena", "Baixa"]
    assert rows[0].label == "Vaga perfeita" and rows[2].label == "Chance média"


def test_rank_tiebreak_fewer_applicants_first_none_last():
    p = Profile(skills=[Skill("SQL")])
    mk = lambda role, n: build_report(role, [J(["SQL"], applicants=n) for _ in range(3)])
    unknown = build_report("Sem dado", [J(["SQL"]) for _ in range(3)])
    rows = rank_focus([unknown, mk("Muitos", 200), mk("Poucos", 20)], p)
    assert [r.role for r in rows] == ["Poucos", "Muitos", "Sem dado"]


def test_rank_handles_empty_core():
    row = rank_focus([build_report("Vazio", [J([]), J([])])], Profile())[0]
    assert row.coverage == 0 and row.label == "Arriscado" and row.missing == []
