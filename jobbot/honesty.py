from __future__ import annotations

import re
from datetime import date

from jobbot.schema import Profile

# shortcut: only numbers are checked in free text, employer or certification names invented
# in the summary are not detected; upgrade when the summary is generated unattended.
_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?%?(?!\w)")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


class HonestyError(Exception):
    def __init__(self, tokens: list[str], message: str | None = None):
        self.tokens = tokens
        super().__init__(message or "números sem respaldo no perfil: " + ", ".join(tokens))


def _value(token: str) -> float:
    return float(token.rstrip("%").replace(",", "."))


def total_years(p: Profile, today: date) -> int:
    """Whole years from the earliest experience start (YYYY or YYYY-MM) to today."""
    starts = []
    for e in p.experiences:
        m = re.match(r"(\d{4})(?:-(\d{1,2}))?", e.start or "")
        if m:
            starts.append((int(m.group(1)), int(m.group(2) or 1)))
    if not starts:
        return 0
    y, mo = min(starts)
    return max(0, ((today.year - y) * 12 + today.month - mo) // 12)


def _allowed(p: Profile, today: date) -> set[float]:
    values: set[float] = {float(total_years(p, today))}
    for e in p.experiences:
        values.update(float(y) for y in _YEAR.findall(f"{e.start} {e.end or ''}"))
        for b in e.bullets:
            values.update(_value(t) for t in _NUMBER.findall(b.metric or ""))
    for ed in p.education:
        values.update(float(y) for y in _YEAR.findall(f"{ed.start} {ed.end or ''}"))
    for pr in p.projects:
        values.update(float(y) for y in _YEAR.findall(f"{pr.start} {pr.end or ''}"))
    values.update(float(v) for v in p.screening.years_by_skill.values())
    values.update(float(c.year) for c in p.certifications if c.year)
    return values


def unsupported_numbers(text: str, p: Profile, today: date | None = None) -> list[str]:
    """Numeric tokens in text that the profile does not back, in order, without repeats."""
    allowed = _allowed(p, today or date.today())
    found: list[str] = []
    for token in _NUMBER.findall(text):
        if _value(token) not in allowed and token not in found:
            found.append(token)
    return found
