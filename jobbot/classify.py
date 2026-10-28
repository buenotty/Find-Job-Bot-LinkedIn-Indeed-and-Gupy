from __future__ import annotations

from dataclasses import dataclass

from jobbot.jobtypes import find_type, releasable_targets
from jobbot.match import normalize
from jobbot.posting import Posting
from jobbot.schema import Profile

MIN_SCORE = 2
TITLE_BONUS = 2
MIN_WORD = 4


@dataclass
class Classification:
    kind: str  # "tipo" | "ambiguo" | "sem_tipo"
    role: str | None = None
    candidates: list[str] | None = None
    scores: dict[str, int] | None = None


def _score(posting: Posting, role: str, keywords: list[str]) -> int:
    wanted = {normalize(k) for k in keywords}
    hits = sum(1 for s in {normalize(s) for s in posting.skills} if s in wanted)
    title = set(normalize(posting.title).split())
    bonus = TITLE_BONUS if any(len(w) >= MIN_WORD and w in title for w in normalize(role).split()) else 0
    return hits + bonus


def classify(posting: Posting, p: Profile, forced: str | None = None) -> Classification:
    live = {t.role.casefold(): t for t in releasable_targets(p)}
    types = [jt for jt in p.job_types if jt.role.casefold() in live]
    if forced is not None:
        jt = find_type(p, forced)
        if jt is None or jt.role.casefold() not in live:
            raise ValueError(f"tipo não definido ou não liberado: {forced!r}")
        return Classification("tipo", jt.role, [jt.role], {})
    scores = {jt.role: _score(posting, jt.role, jt.keywords + live[jt.role.casefold()].required_skills) for jt in types}
    best = max(scores.values(), default=0)
    if best < MIN_SCORE:
        return Classification("sem_tipo", None, [], scores)
    top = [r for r, s in scores.items() if s == best]
    if len(top) > 1:
        return Classification("ambiguo", None, top, scores)
    return Classification("tipo", top[0], top, scores)
