from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from jobbot.match import coverage, label, normalize
from jobbot.schema import Profile

CORE_SHARE = 40  # a skill is core when it appears in at least this % of a role's jobs
MAX_TOP_SKILLS = 15


@dataclass
class Job:
    title: str
    company: str
    skills: list[str]
    salary_min: int | None = None
    salary_max: int | None = None
    applicants: int | None = None
    url: str = ""


@dataclass
class RoleReport:
    role: str
    n_jobs: int
    top_skills: list[tuple[str, int]]  # (display name, share of jobs in percent)
    salary_median: int | None
    applicants_median: int | None


@dataclass
class FocusRow:
    role: str
    coverage: int
    label: str
    missing: list[str]
    n_jobs: int
    salary_median: int | None
    applicants_median: int | None


def _median(values: list[float]) -> int | None:
    return int(median(values)) if values else None


def _salary(job: Job) -> float | None:
    present = [v for v in (job.salary_min, job.salary_max) if v is not None]
    return sum(present) / len(present) if present else None


def build_report(role: str, jobs: list[Job]) -> RoleReport:
    counts: dict[str, int] = {}
    display: dict[str, str] = {}
    for job in jobs:
        for key in {normalize(s) for s in job.skills if s.strip()}:
            counts[key] = counts.get(key, 0) + 1
        for s in job.skills:
            display.setdefault(normalize(s), s.strip())
    n = len(jobs)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_TOP_SKILLS]
    salaries = [s for s in map(_salary, jobs) if s is not None]
    return RoleReport(
        role=role,
        n_jobs=n,
        top_skills=[(display[k], 100 * c // n) for k, c in ranked],
        salary_median=_median(salaries),
        applicants_median=_median([j.applicants for j in jobs if j.applicants is not None]),
    )


def rank_focus(reports: list[RoleReport], p: Profile) -> list[FocusRow]:
    rows = []
    for r in reports:
        required = [name for name, share in r.top_skills if share >= CORE_SHARE]
        pct, missing = coverage(required, p.skills) if required else (0, [])
        rows.append(FocusRow(r.role, pct, label(pct), missing, r.n_jobs,
                             r.salary_median, r.applicants_median))
    return sorted(rows, key=lambda x: (
        -x.coverage, -x.n_jobs, x.applicants_median is None, x.applicants_median or 0))
