from __future__ import annotations

from dataclasses import dataclass, field

from jobbot.jobtypes import effective_rules, find_type
from jobbot.match import label, normalize, stretch_action
from jobbot.orientation import projected_detail
from jobbot.posting import Posting
from jobbot.schema import Profile

GOOD_MATCH = 70


@dataclass
class Evaluation:
    match: int
    label: str
    action: str
    missing: list[str]
    stretched: list[str]
    risky: bool
    below_floor: bool
    constraints_ok: bool
    good_without_type: bool
    notes: list[str] = field(default_factory=list)
    adjacent: dict[str, str] = field(default_factory=dict)
    salary_is_estimate: bool = False


def pay_of(posting: Posting) -> int | None:
    """The posting's own salary, else the sourced web estimate."""
    return posting.salary if posting.salary is not None else posting.salary_estimate


def constraints_ok(posting: Posting, p: Profile) -> bool:
    onsite_min = p.constraints.onsite_min_salary
    if onsite_min is not None and posting.modality == "presencial":
        pay = pay_of(posting)
        modality_ok = pay is None or pay >= onsite_min
    else:
        modality_ok = (posting.modality is None or not p.constraints.modality
                       or posting.modality in p.constraints.modality)
    level_ok = not p.constraints.seniority or posting.level is None or posting.level in p.constraints.seniority
    cities = {normalize(c) for c in p.constraints.cities}
    maximum = p.constraints.max_commute_minutes
    if posting.modality == "remoto":
        city_ok = True
    elif maximum is not None and posting.commute_minutes is not None:
        city_ok = posting.commute_minutes <= maximum  # a measured trip replaces the city list
    else:
        city_ok = not cities or not posting.city or normalize(posting.city) in cities
    contract = p.screening.contract
    contract_ok = posting.contract is None or contract in ("", "ambos") or posting.contract == contract
    return modality_ok and contract_ok and level_ok and city_ok


_constraints_ok = constraints_ok  # kept for older callers


def evaluate(posting: Posting, p: Profile, type_role: str | None) -> Evaluation:
    if not posting.skills:
        raise ValueError("vaga sem lista de skills")
    pct, missing, adjacent = projected_detail(p, posting.skills)
    action = stretch_action(pct, p.stretch_policy)
    notes: list[str] = []
    pay = pay_of(posting)
    if posting.salary is None:
        notes.append(f"salário estimado ({posting.salary_source})" if pay is not None else "salário não informado")

    below_floor = False
    if type_role is not None:
        jt = find_type(p, type_role)
        if jt is None:
            raise ValueError(f"tipo não definido: {type_role!r}")
        floor = effective_rules(jt, p).salary_floor
        below_floor = floor is not None and pay is not None and pay < floor

    floors = [f for f in (effective_rules(jt, p).salary_floor for jt in p.job_types) if f is not None]
    salary_ok = pay is None or not floors or pay >= min(floors)
    within = constraints_ok(posting, p)
    return Evaluation(
        match=pct, label=label(pct), action=action, missing=missing,
        stretched=[*missing, *adjacent] if action in ("esticar", "esticar_marcado") and p.stretch_policy.stretch else [],
        risky=action == "arriscada", below_floor=below_floor, constraints_ok=within,
        good_without_type=pct >= GOOD_MATCH and within and salary_ok, notes=notes, adjacent=adjacent,
        salary_is_estimate=posting.salary is None and pay is not None,
    )
