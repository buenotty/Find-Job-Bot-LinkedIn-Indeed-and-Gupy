from __future__ import annotations

from datetime import date

from jobbot.honesty import HonestyError, total_years, unsupported_numbers
from jobbot.schema import LEVELS, Profile, education_line

__all__ = ["render_base_cv", "total_years"]

_LEVEL_TITLES = {"especialista": "Especialista", "medio": "Médio", "iniciante": "Iniciante"}


def _section(title: str, lines: list[str]) -> list[str]:
    return [f"## {title}", *lines, ""] if lines else []


def render_base_cv(p: Profile, summary: str, today: date) -> str:
    bad = unsupported_numbers(summary, p, today)
    if bad:
        raise HonestyError(bad)

    contact = [x for x in (", ".join(filter(None, [p.city, p.state])), p.screening.email, p.screening.phone) if x]
    out = [f"# {p.name}", " · ".join(contact), ""]
    out += _section("Resumo", [summary.strip()] if summary.strip() else [])

    exp: list[str] = []
    for e in p.experiences:
        exp += [f"### {e.role} — {e.company}", f"{e.start} – {e.end or 'Atual'}"]
        for b in e.bullets:
            extra = f" ({b.metric})" if b.metric and b.metric not in b.text else ""
            exp.append(f"- {b.text}{extra}")
        exp.append("")
    out += _section("Experiência", exp[:-1] if exp else [])

    out += _section("Projetos", [
        f"- **{x.name}** — {x.description}" + (f" ({x.url})" if x.url else "") for x in p.projects
    ])
    out += _section("Competências", [
        f"**{_LEVEL_TITLES[lv]}:** " + ", ".join(s.name for s in p.skills if s.level == lv)
        for lv in LEVELS if any(s.level == lv for s in p.skills)
    ])
    out += _section("Formação", [f"- {education_line(e)}" for e in p.education])
    out += _section("Certificações", [
        f"- {c.name} — {c.issuer}" + (f" ({c.year})" if c.year else "") for c in p.certifications
    ])
    out += _section("Idiomas", [f"- {x.name} — {x.level}" for x in p.languages])
    return "\n".join(out).strip() + "\n"
