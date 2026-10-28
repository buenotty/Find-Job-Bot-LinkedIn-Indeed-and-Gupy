from __future__ import annotations

from dataclasses import dataclass

from jobbot.orientation import cv_released, projected_match
from jobbot.schema import JobType, Profile, Target


@dataclass
class Rules:
    salary_floor: int | None
    modality: list[str]
    contract: str


def effective_rules(jt: JobType, p: Profile) -> Rules:
    """Type-level values win; empty ones fall back to the person's profile."""
    return Rules(
        salary_floor=jt.salary_floor if jt.salary_floor is not None else p.screening.salary_expectation,
        modality=jt.modality or p.constraints.modality,
        contract=jt.contract or p.screening.contract,
    )


def releasable_targets(p: Profile) -> list[Target]:
    out = []
    for t in p.targets:
        current = projected_match(p, t.required_skills)[0] if t.required_skills else None
        if cv_released(t, current, p.stretch_policy):
            out.append(t)
    return out


def find_type(p: Profile, role: str) -> JobType | None:
    return next((t for t in p.job_types if t.role.casefold() == role.casefold()), None)


def validate_new_type(p: Profile, record: dict) -> dict:
    role = str(record.get("role", "")).casefold()
    if not any(t.role.casefold() == role for t in releasable_targets(p)):
        raise ValueError(f"profissão ainda não liberada para currículo: {record.get('role')!r}")
    return record
