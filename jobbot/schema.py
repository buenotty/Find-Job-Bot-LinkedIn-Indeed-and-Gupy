from __future__ import annotations

from dataclasses import asdict, dataclass, field

LEVELS = ("especialista", "medio", "iniciante")
CONTRACTS = ("CLT", "PJ", "ambos")
TRACKS = ("especialista", "gestao", "hibrido", "indefinido")


@dataclass
class Skill:
    name: str = ""
    level: str = "iniciante"
    evidence: str = ""


@dataclass
class Bullet:
    text: str = ""
    metric: str | None = None  # only set when the person reported it


@dataclass
class Experience:
    company: str = ""
    role: str = ""
    start: str = ""
    end: str | None = None
    bullets: list[Bullet] = field(default_factory=list)


@dataclass
class Project:
    name: str = ""
    description: str = ""
    url: str | None = None
    kind: str = "projeto"
    start: str = ""
    end: str | None = None


@dataclass
class Certification:
    name: str = ""
    issuer: str = ""
    year: int | None = None


@dataclass
class Education:
    institution: str = ""
    course: str = ""
    level: str = ""
    start: str = ""
    end: str | None = None
    status: str = ""


def education_line(e: Education) -> str:
    """One resume line, built only from the profile's own fields."""
    if e.end and not e.start:
        period = e.end
    elif e.end:
        period = f"{e.start} - {e.end}"
    elif e.status == "cursando":
        period = f"{e.start} - cursando"
    else:
        period = e.start
    head = EDU_LABELS.get(e.level, "") if e.level == "medio" else f"{EDU_LABELS.get(e.level, '')} {e.course}".strip()
    return f"{head} - {e.institution}" + (f" ({period})" if period else "")


@dataclass
class Language:
    name: str = ""
    level: str = ""


@dataclass
class Constraints:
    modality: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    vetoed_companies: list[str] = field(default_factory=list)
    vetoed_sectors: list[str] = field(default_factory=list)
    current_employer: str | None = None
    onsite_min_salary: int | None = None  # onsite postings only count at or above this monthly pay
    seniority: list[str] = field(default_factory=list)  # accepted levels (estagio, junior, pleno, senior); empty = any
    max_commute_minutes: int | None = None  # longest accepted one-way trip by bus or metro, for hybrid and onsite jobs
    home_area: str = ""  # neighborhood or metro station near home; the start of the Maps trip


@dataclass
class Screening:
    salary_expectation: int | None = None
    contract: str = ""
    availability: str = ""
    email: str = ""
    phone: str = ""
    years_by_skill: dict[str, float] = field(default_factory=dict)


@dataclass
class Behavior:
    work_style: str = ""
    motivators: list[str] = field(default_factory=list)
    track: str = ""


@dataclass
class StretchPolicy:
    stretch_from: int = 90
    risky_below: int = 50
    stretch: bool = True  # False: a posting's CV never lists skills the person does not have


KINDS = ("projeto", "voluntariado", "autodidata", "freela")
MODES = ("tipo", "do_zero")
EDU_LEVELS = ("medio", "tecnico", "graduacao", "pos", "mestrado", "doutorado")
EDU_STATUS = ("concluido", "cursando", "trancado")
EDU_LABELS = {"medio": "Ensino médio", "tecnico": "Técnico em", "graduacao": "Graduação em",
              "pos": "Pós-graduação em", "mestrado": "Mestrado em", "doutorado": "Doutorado em"}
PLATFORMS = ("linkedin", "indeed", "gupy")
APP_STATUSES = ("preparado", "enviada", "descartada", "bloqueada", "externa", "desconhecido")
SEEN_REASONS = ("preparada", "repetida", "empregador_atual", "empresa_vetada",
                "fora_das_restricoes", "falha", "bloqueada")
ANSWER_CATEGORIES = ("geral", "sensivel", "legal")
FIT_MODES = ("auto", "perguntar", "pular")
AUTONOMY_MODES = ("full", "assisted")  # full: bot answers and finishes; assisted: stops before sending
GROUPS = ("agora", "nova_formacao", "sem_dado")
SOURCES = ("sugerida", "propria")
STATUSES = ("pronto", "em_formacao", "sem_dado_mercado")
RELIABILITY = ("alta", "baixa")


@dataclass
class Assessment:
    date: str = ""
    scores: dict[str, int] = field(default_factory=dict)
    confiabilidade: str = ""
    flags: list[str] = field(default_factory=list)
    situations: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Target:
    role: str = ""
    group: str = ""
    source: str = ""
    required_skills: list[str] = field(default_factory=list)
    match_at_acceptance: int | None = None
    accepted_at: str = ""
    status: str = ""


@dataclass
class CourseDone:
    course: str = ""
    provider: str = ""
    date: str = ""
    skills_claimed: list[str] = field(default_factory=list)
    evidence: str = ""


@dataclass
class JobType:
    role: str = ""
    salary_floor: int | None = None
    modality: list[str] = field(default_factory=list)
    contract: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class Application:
    date: str = ""
    url: str = ""
    company: str = ""
    title: str = ""
    type: str = ""
    mode: str = ""
    match: int | None = None
    label: str = ""
    risky: bool = False
    below_floor: bool = False
    file: str = ""
    status: str = "preparado"
    platform: str = ""


@dataclass
class SeenPosting:
    key: str = ""
    alt_key: str = ""
    platform: str = ""
    company: str = ""
    title: str = ""
    url: str = ""
    reason: str = ""
    date: str = ""


@dataclass
class AnswerEntry:
    question: str = ""
    answer: str = ""
    category: str = "geral"
    always: bool = False


@dataclass
class PendingQuestion:
    question: str = ""
    category: str = "geral"
    vaga: str = ""
    date: str = ""


@dataclass
class PlatformState:
    platform: str = ""
    paused: bool = False
    reason: str = ""
    since: str = ""


@dataclass
class RunSettings:
    per_round: int = 10
    per_day: int = 30
    max_examined: int = 50
    fit_mode: str = "auto"
    autonomy: str = "full"


@dataclass
class Profile:
    name: str = ""
    age: int | None = None
    state: str = ""
    city: str = ""
    linkedin: str = ""  # public profile link; read by the diagnosis, never edited
    github: str = ""
    links: list[str] = field(default_factory=list)  # portfolio, YouTube, sites
    experiences: list[Experience] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)
    languages: list[Language] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    constraints: Constraints = field(default_factory=Constraints)
    screening: Screening = field(default_factory=Screening)
    behavior: Behavior = field(default_factory=Behavior)
    stretch_policy: StretchPolicy = field(default_factory=StretchPolicy)
    assessments: list[Assessment] = field(default_factory=list)
    targets: list[Target] = field(default_factory=list)
    courses_done: list[CourseDone] = field(default_factory=list)
    cheap_course_max: int = 200
    education: list[Education] = field(default_factory=list)
    job_types: list[JobType] = field(default_factory=list)
    applications: list[Application] = field(default_factory=list)
    run: RunSettings = field(default_factory=RunSettings)
    seen: list[SeenPosting] = field(default_factory=list)
    answers: list[AnswerEntry] = field(default_factory=list)
    pending: list[PendingQuestion] = field(default_factory=list)
    platforms: list[PlatformState] = field(default_factory=list)


def profile_to_dict(p: Profile) -> dict:
    return asdict(p)


def _check_map(cls, data):
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{cls.__name__} deve ser um mapa, recebido {type(data).__name__}: {data!r}")
    unknown = set(data) - set(cls.__dataclass_fields__)
    if unknown:
        raise ValueError(f"campo desconhecido em {cls.__name__}: {', '.join(sorted(map(str, unknown)))}")
    return data


def _build(cls, data):
    return cls(**_check_map(cls, data))


def _records(d: dict, key: str, make) -> list:
    items = d.get(key)
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError(f"'{key}' deve ser uma lista")
    return [make(x) for x in items]


def _experience(data) -> Experience:
    data = _check_map(Experience, data)
    return Experience(**{**data, "bullets": _records(data, "bullets", lambda b: _build(Bullet, b))})


def profile_from_dict(d: dict) -> Profile:
    """Build a Profile; unknown top-level keys are ignored, nested records must match exactly."""
    d = d or {}
    if not isinstance(d, dict):
        raise ValueError("perfil deve ser um mapa")
    return Profile(
        name=d.get("name", ""), age=d.get("age"), state=d.get("state", ""), city=d.get("city", ""),
        linkedin=d.get("linkedin", ""), github=d.get("github", ""), links=list(d.get("links") or []),
        experiences=_records(d, "experiences", _experience),
        skills=_records(d, "skills", lambda x: _build(Skill, x)),
        certifications=_records(d, "certifications", lambda x: _build(Certification, x)),
        languages=_records(d, "languages", lambda x: _build(Language, x)),
        projects=_records(d, "projects", lambda x: _build(Project, x)),
        constraints=_build(Constraints, d.get("constraints")),
        screening=_build(Screening, d.get("screening")),
        behavior=_build(Behavior, d.get("behavior")),
        stretch_policy=_build(StretchPolicy, d.get("stretch_policy")),
        assessments=_records(d, "assessments", lambda x: _build(Assessment, x)),
        targets=_records(d, "targets", lambda x: _build(Target, x)),
        courses_done=_records(d, "courses_done", lambda x: _build(CourseDone, x)),
        cheap_course_max=d.get("cheap_course_max", 200),
        education=_records(d, "education", lambda x: _build(Education, x)),
        job_types=_records(d, "job_types", lambda x: _build(JobType, x)),
        applications=_records(d, "applications", lambda x: _build(Application, x)),
        run=_build(RunSettings, d.get("run")),
        seen=_records(d, "seen", lambda x: _build(SeenPosting, x)),
        answers=_records(d, "answers", lambda x: _build(AnswerEntry, x)),
        pending=_records(d, "pending", lambda x: _build(PendingQuestion, x)),
        platforms=_records(d, "platforms", lambda x: _build(PlatformState, x)),
    )


def validate(p: Profile) -> list[str]:
    """Return PT-BR problems; empty list means the profile is valid."""
    errors: list[str] = []
    if not p.name.strip():
        errors.append("nome é obrigatório")
    if p.age is not None and not (isinstance(p.age, int) and 14 <= p.age <= 100):
        errors.append(f"idade fora do intervalo esperado: {p.age}")
    for e in p.experiences:
        if not e.company.strip() or not e.role.strip():
            errors.append("experiência sem empresa ou cargo")
    for s in p.skills:
        if not s.name.strip():
            errors.append("skill sem nome")
        if s.level not in LEVELS:
            errors.append(f"nível inválido para '{s.name}': '{s.level}' (use {', '.join(LEVELS)})")
    if p.screening.contract and p.screening.contract not in CONTRACTS:
        errors.append(f"contrato inválido: '{p.screening.contract}' (use {', '.join(CONTRACTS)})")
    if p.behavior.track and p.behavior.track not in TRACKS:
        errors.append(f"trilha inválida: '{p.behavior.track}' (use {', '.join(TRACKS)})")
    for a in p.assessments:
        if a.confiabilidade and a.confiabilidade not in RELIABILITY:
            errors.append(f"confiabilidade inválida: '{a.confiabilidade}'")
    for t in p.targets:
        if t.group and t.group not in GROUPS:
            errors.append(f"grupo inválido em '{t.role}': '{t.group}'")
        if t.source and t.source not in SOURCES:
            errors.append(f"origem inválida em '{t.role}': '{t.source}'")
        if t.status and t.status not in STATUSES:
            errors.append(f"status inválido em '{t.role}': '{t.status}'")
    def texts(v):
        return isinstance(v, list) and all(isinstance(x, str) for x in v)

    for t in p.targets:
        if not texts(t.required_skills):
            errors.append(f"required_skills de '{t.role}' deve ser uma lista de textos")
    for c in p.courses_done:
        if not texts(c.skills_claimed):
            errors.append(f"skills_claimed do curso '{c.course}' deve ser uma lista de textos")
    for a in p.assessments:
        ok = isinstance(a.situations, list) and all(
            isinstance(x, dict) and all(isinstance(v, str) for v in x.values()) for x in a.situations)
        if not ok:
            errors.append("situations deve ser uma lista de mapas {pergunta, resposta} com textos")
    for ed in p.education:
        if ed.level not in EDU_LEVELS:
            errors.append(f"nível de formação inválido em '{ed.institution}': '{ed.level}'")
        if ed.status not in EDU_STATUS:
            errors.append(f"situação de formação inválida em '{ed.institution}': '{ed.status}'")
        if not ed.institution.strip():
            errors.append("formação sem instituição")
        if ed.level != "medio" and not ed.course.strip():
            errors.append(f"formação sem curso em '{ed.institution}'")
    for pr in p.projects:
        if pr.kind not in KINDS:
            errors.append(f"kind inválido em '{pr.name}': '{pr.kind}'")
    for ap in p.applications:
        if ap.mode and ap.mode not in MODES:
            errors.append(f"modo inválido na candidatura '{ap.company}': '{ap.mode}'")
        if ap.status not in APP_STATUSES:
            errors.append(f"status inválido na candidatura '{ap.company}': '{ap.status}'")
        if ap.platform and ap.platform not in PLATFORMS:
            errors.append(f"plataforma inválida na candidatura '{ap.company}': '{ap.platform}'")
    for sp in p.seen:
        if sp.reason not in SEEN_REASONS:
            errors.append(f"motivo inválido na vaga vista '{sp.title}': '{sp.reason}'")
        if sp.platform not in PLATFORMS:
            errors.append(f"plataforma inválida na vaga vista '{sp.title}': '{sp.platform}'")
    for an in p.answers:
        if an.category not in ANSWER_CATEGORIES:
            errors.append(f"categoria inválida na resposta '{an.question}': '{an.category}'")
    for ps in p.platforms:
        if ps.platform not in PLATFORMS:
            errors.append(f"plataforma inválida no estado: '{ps.platform}'")
    for field_name in ("per_round", "per_day", "max_examined"):
        value = getattr(p.run, field_name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            errors.append(f"{field_name} deve ser um inteiro maior ou igual a 1")
    if p.run.fit_mode not in FIT_MODES:
        errors.append(f"fit_mode inválido: '{p.run.fit_mode}' (use {', '.join(FIT_MODES)})")
    if p.run.autonomy not in AUTONOMY_MODES:
        errors.append(f"autonomy inválido: '{p.run.autonomy}' (use {', '.join(AUTONOMY_MODES)})")
    for jt in p.job_types:
        if jt.contract and jt.contract not in CONTRACTS:
            errors.append(f"contrato inválido no tipo '{jt.role}': '{jt.contract}'")
        if jt.salary_floor is not None and (not isinstance(jt.salary_floor, int) or jt.salary_floor < 0):
            errors.append(f"piso inválido no tipo '{jt.role}'")
        if not texts(jt.keywords) or not texts(jt.modality):
            errors.append(f"keywords e modality do tipo '{jt.role}' devem ser listas de textos")
    if not isinstance(p.cheap_course_max, int) or p.cheap_course_max < 0:
        errors.append("cheap_course_max deve ser um inteiro não negativo")
    return errors
