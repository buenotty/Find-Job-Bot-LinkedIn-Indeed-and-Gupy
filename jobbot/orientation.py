from __future__ import annotations

from jobbot.match import coverage_detail, normalize
from jobbot.schema import Profile, Skill, StretchPolicy, Target

MIN_SAMPLE = 30
SATURATED_APPLICANTS = 200


def classify_group(pct: int, policy: StretchPolicy) -> str:
    return "agora" if pct >= policy.risky_below else "nova_formacao"


def cv_released(target: Target, current_pct: int | None, policy: StretchPolicy) -> bool:
    if target.group == "agora":
        return True
    if target.group == "nova_formacao":
        return current_pct is not None and current_pct >= policy.stretch_from
    return False


def price_band(price: int | None, cheap_max: int) -> str:
    if price is None:
        return "sem_preco"
    if price == 0:
        return "gratuito"
    return "barato" if price <= cheap_max else "caro"


def projected_detail(p: Profile, required: list[str]) -> tuple[int, list[str], dict[str, str]]:
    """Match counting confirmed course skills; a projection, never written to profile.skills."""
    unique: dict[str, str] = {}
    for r in required:
        unique.setdefault(normalize(r), r.strip())
    if not unique:
        return 0, [], {}
    claimed = [
        Skill(c) for course in p.courses_done for c in course.skills_claimed if normalize(c) in unique
    ]
    return coverage_detail(list(unique.values()), [*p.skills, *claimed])


def projected_match(p: Profile, required: list[str]) -> tuple[int, list[str]]:
    pct, missing, _ = projected_detail(p, required)
    return pct, missing


def market_claims(n_jobs: int, salary_median: int | None, applicants_median: int | None, p: Profile) -> dict[str, str]:
    def verdict(flag: bool | None) -> str:
        if flag is None:
            return "sem_dado"
        if n_jobs < MIN_SAMPLE:
            return "indicio"
        return "sim" if flag else "nao"

    expectation = p.screening.salary_expectation
    return {
        "saturado": verdict(None if applicants_median is None else applicants_median >= SATURATED_APPLICANTS),
        "paga_pouco": verdict(None if salary_median is None or expectation is None else salary_median < expectation),
    }
