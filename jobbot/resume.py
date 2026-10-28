from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from jobbot.evaluate import Evaluation, pay_of
from jobbot.honesty import HonestyError, unsupported_numbers
from jobbot.match import normalize
from jobbot.posting import Posting
from jobbot.schema import LEVELS, Profile, education_line

SUMMARY_MAX = 480
SECTION_TITLES = ("Resumo", "Experiência", "Projetos e voluntariado", "Competências", "Formação",
                  "Certificações", "Idiomas")
_KIND_LABELS = {"autodidata": "Autodidata", "voluntariado": "Voluntariado", "freela": "Freela"}


@dataclass
class ResumeContent:
    summary: str = ""
    experience_bullets: dict[str, list[str]] = field(default_factory=dict)
    project_bullets: dict[str, list[str]] = field(default_factory=dict)
    skill_order: list[str] = field(default_factory=list)
    show_projects: bool = True  # False drops the whole projects section (for types where none is relevant)
    headline: str = ""  # one line under the name, e.g. the professional focus of this CV type
    skill_groups: dict[str, list[str]] = field(default_factory=dict)  # label -> skills, shown grouped


@dataclass
class ResumeDoc:
    name: str
    contact: str
    summary: str
    experiences: list[dict]
    projects: list[dict]
    skills: list[str]
    certifications: list[str]
    languages: list[str]
    education: list[str] = field(default_factory=list)
    headline: str = ""
    skill_groups: list[tuple[str, list[str]]] = field(default_factory=list)


def _bullet_map(value, key: str) -> dict[str, list[str]]:
    if not isinstance(value, dict) or not all(
            isinstance(k, str) and isinstance(v, list) and all(isinstance(x, str) for x in v)
            for k, v in value.items()):
        raise ValueError(f"'{key}' deve ser um mapa nome: lista de textos")
    return value


def content_from_dict(d: dict) -> ResumeContent:
    if not isinstance(d, dict):
        raise ValueError("conteúdo do currículo deve ser um mapa")
    unknown = set(d) - set(ResumeContent.__dataclass_fields__)
    if unknown:
        raise ValueError(f"campo desconhecido no conteúdo: {', '.join(sorted(map(str, unknown)))}")
    summary = d.get("summary", "")
    order = d.get("skill_order", [])
    if not isinstance(summary, str):
        raise ValueError("'summary' deve ser texto")
    if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
        raise ValueError("'skill_order' deve ser uma lista de textos")
    show = d.get("show_projects", True)
    if not isinstance(show, bool):
        raise ValueError("'show_projects' deve ser verdadeiro ou falso")
    headline = d.get("headline", "")
    if not isinstance(headline, str):
        raise ValueError("'headline' deve ser texto")
    return ResumeContent(
        summary, _bullet_map(d.get("experience_bullets", {}), "experience_bullets"),
        _bullet_map(d.get("project_bullets", {}), "project_bullets"), order, show, headline,
        _bullet_map(d.get("skill_groups", {}), "skill_groups"))


def merge_content(base: ResumeContent, override: ResumeContent) -> ResumeContent:
    """Each non-empty field of override replaces the base field."""
    return ResumeContent(
        override.summary or base.summary,
        override.experience_bullets or base.experience_bullets,
        override.project_bullets or base.project_bullets,
        override.skill_order or base.skill_order,
        base.show_projects and override.show_projects,
        override.headline or base.headline,
        override.skill_groups or base.skill_groups,
    )


def _short_url(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url.strip()).rstrip("/")


def _year(text: str) -> str:
    m = re.match(r"\d{4}", text or "")
    return m.group(0) if m else ""


def _label(kind: str, start: str) -> str:
    base = _KIND_LABELS.get(kind, "")
    year = _year(start)
    return f"{base} desde {year}" if base and year else base


def _ordered_skills(p: Profile, order: list[str], stretched: list[str]) -> list[str]:
    owned = {normalize(s.name): s for s in p.skills}
    out: list[str] = []
    seen: set[str] = set()

    def add(display: str) -> None:
        if normalize(display) not in seen:
            seen.add(normalize(display))
            out.append(display)

    for name in order:
        if normalize(name) in owned:
            add(owned[normalize(name)].name)
    for level in (*LEVELS, None):
        for s in p.skills:
            if (s.level == level) if level else (s.level not in LEVELS):
                add(s.name)
    for name in stretched:
        add(name)
    return out


SHORT_SKILL = 4  # shorter names ("Go", "R", "C") are matched as whole words to avoid false positives


def _mentions(text: str, skill: str) -> bool:
    """Longer skill names also match inside longer words ("dockerização", "kafkaizou")."""
    name, hay = normalize(skill), normalize(text)
    if len(name) >= SHORT_SKILL:
        return name in hay
    return re.search(rf"(?<!\w){re.escape(name)}(?!\w)", hay) is not None


def build_resume(p: Profile, content: ResumeContent, stretched: list[str], today: date,
                 missing: list[str] = ()) -> ResumeDoc:
    if len(content.summary) > SUMMARY_MAX:
        raise ValueError(f"resumo passa de {SUMMARY_MAX} caracteres (máximo de 4 linhas)")
    companies = {e.company.casefold() for e in p.experiences}
    projects = {x.name.casefold() for x in p.projects}
    for key in content.experience_bullets:
        if key.casefold() not in companies:
            raise HonestyError([key], f"empregador fora do perfil: {key!r}")
    for key in content.project_bullets:
        if key.casefold() not in projects:
            raise HonestyError([key], f"projeto fora do perfil: {key!r}")

    texts = [content.summary, *(b for v in content.experience_bullets.values() for b in v),
             *(b for v in content.project_bullets.values() for b in v)]
    bad = unsupported_numbers("\n".join(texts), p, today)
    if bad:
        raise HonestyError(bad)
    # stretched skills may only sit in Competências; skills the person lacks (missing) may not appear at all
    forbidden = list(dict.fromkeys([*stretched, *missing]))
    leaked = [s for s in forbidden if any(_mentions(t, s) for t in texts)]
    if leaked:
        raise HonestyError(leaked, f"skill que a pessoa não tem citada no texto (as esticadas só podem ficar em Competências): {', '.join(leaked)}")

    # experience_bullets, when given, also selects and orders the jobs shown; empty means all of them
    by_company = {e.company.casefold(): e for e in p.experiences}
    chosen_jobs = [by_company[k.casefold()] for k in content.experience_bullets] or p.experiences
    experiences = []
    for e in chosen_jobs:
        own = [b.text + (f" ({b.metric})" if b.metric and b.metric not in b.text else "") for b in e.bullets]
        bullets = next((v for k, v in content.experience_bullets.items() if k.casefold() == e.company.casefold()), own)
        experiences.append({"title": e.role, "company": e.company, "period": f"{e.start} - {e.end or 'Atual'}", "bullets": bullets})
    by_name = {x.name.casefold(): x for x in p.projects}
    # project_bullets, when given, also selects and orders the projects shown; empty means all of them
    chosen = ([by_name[k.casefold()] for k in content.project_bullets] or p.projects) if content.show_projects else []
    project_blocks = []
    for x in chosen:
        bullets = next((v for k, v in content.project_bullets.items() if k.casefold() == x.name.casefold()),
                       [x.description] if x.description else [])
        project_blocks.append({"name": x.name, "label": _label(x.kind, x.start), "bullets": bullets})

    place = ", ".join(filter(None, [p.city, p.state]))
    owned = {normalize(s.name): s.name for s in p.skills}
    groups: list[tuple[str, list[str]]] = []
    for label, names in content.skill_groups.items():
        unknown = [n for n in names if normalize(n) not in owned]
        if unknown:
            raise HonestyError(unknown, f"skill fora do perfil no grupo {label!r}: {', '.join(unknown)}")
        groups.append((label, [owned[normalize(n)] for n in names]))
    if groups and stretched:  # stretched skills only ever sit in Competências, never in the text
        groups.append(("Também", list(stretched)))
    links = [_short_url(u) for u in (p.linkedin, p.github) if u]
    return ResumeDoc(
        name=p.name,
        contact=" | ".join(filter(None, [place, p.screening.email, p.screening.phone, *links])),
        summary=content.summary.strip(),
        experiences=experiences,
        projects=project_blocks,
        skills=_ordered_skills(p, content.skill_order, stretched),
        certifications=[f"{c.name} - {c.issuer}" + (f" ({c.year})" if c.year else "") for c in p.certifications],
        languages=[f"{x.name} - {x.level}" for x in p.languages],
        education=[education_line(e) for e in p.education],
        headline=content.headline.strip(),
        skill_groups=groups,
    )


def doc_text(doc: ResumeDoc) -> str:
    lines = [doc.name, *([doc.headline] if doc.headline else []), doc.contact, ""]

    def section(title: str, body: list[str]) -> None:
        if body:
            lines.extend([title, *body, ""])

    section("Resumo", [doc.summary] if doc.summary else [])
    exp: list[str] = []
    for e in doc.experiences:
        exp += [f"{e['title']} - {e['company']} ({e['period']})", *(f"- {b}" for b in e["bullets"])]
    section("Experiência", exp)
    proj: list[str] = []
    for x in doc.projects:
        proj += [x["name"] + (f" - {x['label']}" if x["label"] else ""), *(f"- {b}" for b in x["bullets"])]
    section("Projetos e voluntariado", proj)
    if doc.skill_groups:
        section("Competências", [f"{label}: {', '.join(names)}" for label, names in doc.skill_groups])
    else:
        section("Competências", [", ".join(doc.skills)] if doc.skills else [])
    section("Formação", [f"- {e}" for e in doc.education])
    section("Certificações", [f"- {c}" for c in doc.certifications])
    section("Idiomas", [f"- {x}" for x in doc.languages])
    return "\n".join(lines).strip() + "\n"


def review_sheet(posting: Posting, ev: Evaluation, type_role: str | None, mode: str, salary_floor: int | None) -> str:
    kind = type_role if type_role else "sem tipo (currículo do zero)" if mode == "do_zero" else "sem tipo"
    if posting.salary is not None:
        salary = f"{posting.salary}"
    elif posting.salary_estimate is not None:
        salary = f"não informado (estimado em {posting.salary_estimate}: {posting.salary_source})"
    else:
        salary = "não informado"
    lines = [
        "Folha de revisão",
        f"Vaga: {posting.title} - {posting.company}",
        f"Link: {posting.url or 'não informado'}",
        f"Tipo: {kind}",
        f"Match: {ev.match}% ({ev.label})",
        f"Salário da vaga: {salary}",
    ]
    if salary_floor is not None:
        lines.append(f"Piso do tipo: {salary_floor}")
    if ev.below_floor:
        kind_of_pay = "salário estimado" if ev.salary_is_estimate else "salário"
        lines.append(f"Abaixo do piso: sim ({kind_of_pay} {pay_of(posting)}, piso {salary_floor}). A vaga foi mantida; você decide.")
    lines.append(f"Restrições de modalidade e contrato: {'ok' if ev.constraints_ok else 'fora das suas restrições'}")
    if ev.adjacent:
        lines.append("Skills adjacentes (contam no match; listadas em Competências sem alegar experiência): "
                     + ", ".join(f"{req} (você tem {own})" for req, own in ev.adjacent.items()))
    if ev.risky:
        lines.append("Vaga arriscada: match abaixo do corte. Nenhuma skill foi esticada no currículo.")
        lines.append("Skills que faltam: " + (", ".join(ev.missing) or "nenhuma"))
    elif ev.stretched:
        lines.append("Skills esticadas (listadas em Competências, sem alegar experiência; "
                     "podem ser perguntadas na entrevista): " + ", ".join(ev.stretched))
    lines.extend(f"Nota: {n}" for n in ev.notes)
    return "\n".join(lines) + "\n"
