from __future__ import annotations

import unicodedata

from jobbot.schema import Skill, StretchPolicy


def normalize(skill: str) -> str:
    """Casefold, strip accents and collapse whitespace so spellings compare equal."""
    decomposed = unicodedata.normalize("NFKD", skill)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.casefold().split())


# Curated, deliberately short: a skill the person owns that clearly transfers to a more specific one.
# A match on these counts toward coverage, but the resume never claims the specific skill in its text.
ADJACENT: dict[str, frozenset[str]] = {
    "sql": frozenset({"sql server", "t-sql", "tsql", "mysql", "postgresql", "postgres", "pl/sql", "oracle sql",
                      "sql avancado", "sql intermediario", "sql basico"}),
    "ssms": frozenset({"sql server", "t-sql", "tsql"}),
    "excel": frozenset({"excel avancado", "excel intermediario", "excel basico", "google sheets",
                        "planilhas", "planilhas eletronicas"}),
    "power bi": frozenset({"power bi desktop", "power bi service", "power bi avancado"}),
    "python": frozenset({"python 3", "python avancado"}),
}


def coverage_detail(required: list[str], skills: list[Skill]) -> tuple[int, list[str], dict[str, str]]:
    """Percent (floored), missing skills and the required skills covered only by an adjacent owned skill."""
    if not required:
        raise ValueError("lista de requisitos vazia")
    owned = {normalize(s.name): s.name for s in skills}
    missing: list[str] = []
    adjacent: dict[str, str] = {}
    for r in required:
        n = normalize(r)
        if n in owned:
            continue
        via = next((name for key, name in owned.items() if n in ADJACENT.get(key, ())), None)
        if via is not None:
            adjacent[r.strip()] = via
        else:
            missing.append(r.strip())
    return 100 * (len(required) - len(missing)) // len(required), missing, adjacent


def coverage(required: list[str], skills: list[Skill]) -> tuple[int, list[str]]:
    """Percent (floored) of required skills the person has, plus the missing ones."""
    pct, missing, _ = coverage_detail(required, skills)
    return pct, missing


def label(pct: int) -> str:
    if pct >= 100:
        return "Vaga perfeita"
    if pct >= 80:
        return "Ótimo match"
    if pct >= 70:
        return "Bom match"
    if pct >= 50:
        return "Chance média"
    return "Arriscado"


def stretch_action(pct: int, policy: StretchPolicy) -> str:
    if pct >= policy.stretch_from:
        return "esticar"
    if pct >= policy.risky_below:
        return "esticar_marcado"
    return "arriscada"
