from __future__ import annotations

from dataclasses import dataclass, field

MODALITIES = ("remoto", "hibrido", "presencial")
POSTING_CONTRACTS = ("CLT", "PJ")
LEVELS = ("estagio", "junior", "pleno", "senior")


@dataclass
class Posting:
    title: str
    company: str = ""
    skills: list[str] = field(default_factory=list)
    salary: int | None = None
    salary_estimate: int | None = None  # looked up on the web when the posting has no pay; see docs/salary-estimate.md
    salary_source: str = ""
    modality: str | None = None
    contract: str | None = None
    url: str = ""
    level: str | None = None  # seniority the posting asks for; None when it does not say
    city: str = ""
    address: str = ""  # where the job is, for the Maps trip
    commute_minutes: int | None = None  # one-way bus or metro time from home, measured on Maps


def posting_from_dict(d: dict) -> Posting:
    """Strict parse of the structured fields the skill extracts from a vacancy."""
    if not isinstance(d, dict):
        raise ValueError("vaga deve ser um mapa")
    unknown = set(d) - set(Posting.__dataclass_fields__)
    if unknown:
        raise ValueError(f"campo desconhecido na vaga: {', '.join(sorted(map(str, unknown)))}")
    title = d.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("vaga precisa de 'title'")
    skills = d.get("skills", [])
    if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
        raise ValueError("skills da vaga devem ser uma lista de textos")
    salary = d.get("salary")
    if salary is not None and (isinstance(salary, bool) or not isinstance(salary, int)):
        raise ValueError("salary deve ser um número inteiro em reais por mês")
    estimate = d.get("salary_estimate")
    if estimate is not None and (isinstance(estimate, bool) or not isinstance(estimate, int)):
        raise ValueError("salary_estimate deve ser um número inteiro em reais por mês")
    source = str(d.get("salary_source", "")).strip()
    if estimate is not None and not source:
        raise ValueError("salary_estimate precisa de salary_source (fonte e data da consulta)")
    modality, contract = d.get("modality"), d.get("contract")
    if modality is not None and modality not in MODALITIES:
        raise ValueError(f"modality inválida: {modality!r} (use {', '.join(MODALITIES)})")
    if contract is not None and contract not in POSTING_CONTRACTS:
        raise ValueError(f"contract inválido: {contract!r} (use {', '.join(POSTING_CONTRACTS)})")
    level = d.get("level")
    if level is not None and level not in LEVELS:
        raise ValueError(f"level inválido: {level!r} (use {', '.join(LEVELS)})")
    commute = d.get("commute_minutes")
    if commute is not None and (isinstance(commute, bool) or not isinstance(commute, int) or commute < 0):
        raise ValueError("commute_minutes deve ser um número inteiro de minutos")
    return Posting(title.strip(), str(d.get("company", "")), skills, salary, estimate, source, modality, contract,
                   str(d.get("url", "")), level, str(d.get("city", "")).strip(), str(d.get("address", "")).strip(),
                   commute)
