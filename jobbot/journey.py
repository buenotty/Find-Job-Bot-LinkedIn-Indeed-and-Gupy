from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jobbot.schema import Profile
from jobbot.store import load_profile, next_step, profile_dir


@dataclass
class Stage:
    key: str
    skill: str
    title: str
    done: bool = False
    optional: bool = False  # never blocks the flow: skipped when picking the next skill


@dataclass
class Journey:
    stages: list[Stage]
    next_skill: str


STAGES = (
    Stage("entrevista", "jobbot-interview", "Entrevista e perfil"),
    Stage("teste", "jobbot-assessment", "Teste de perfil (opcional)", optional=True),
    Stage("mercado", "jobbot-market", "Cargos aprovados, mercado e foco recomendado"),
    Stage("perfis", "jobbot-profiles", "Perfis (LinkedIn, GitHub e outros) prontos e revisados"),
    Stage("tipos", "jobbot-types", "Um currículo para cada tipo de emprego"),
    Stage("rodada", "jobbot-round", "Rodada de vagas"),
)


def _types_done(p: Profile, folder: Path) -> bool:
    if not p.job_types:
        return False
    from jobbot.store import slugify
    return all((folder / "types" / f"{slugify(t.role)}.pdf").exists() for t in p.job_types)


def journey(name: str) -> Journey:
    """Where a person is in the JobBot flow, from their own profile and files."""
    p, folder = load_profile(name), profile_dir(name)
    done = {
        "entrevista": next_step(name) is None and bool(p.name.strip()),
        "mercado": (folder / "focus-report.md").exists() and bool(p.targets),
        "perfis": (folder / "perfis-revisados.md").exists(),
        "teste": bool(p.assessments),
        "tipos": _types_done(p, folder),
        "rodada": bool(p.applications),
    }
    stages = [Stage(s.key, s.skill, s.title, done[s.key], s.optional) for s in STAGES]
    pending = next((s for s in stages if not s.done and not s.optional), stages[-1])  # all done: keep running rounds
    return Journey(stages, pending.skill)
