from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from jobbot.match import normalize
from jobbot.schema import AnswerEntry, PendingQuestion, Profile

_STOP = {
    "qual", "quais", "sua", "seu", "suas", "seus", "voce", "tem", "possui", "para", "por", "com", "que",
    "uma", "uns", "umas", "ao", "aos", "das", "dos", "nos", "nas", "favor", "informe", "informar",
    "de", "da", "do", "em", "no", "na", "um", "as", "os", "ou", "e", "a", "o", "meu", "minha",
}
_SENSITIVE = re.compile(
    r"\bpcd\b|deficiencia|\bgenero\b|\bsexo\b|\braca\b|\bcor\b|etnia|orientacao sexual|religiao|estado civil"
    r"|autorizacao (?:de|para) trabalh|\bvisto\b|nacionalidade|data de nascimento|\bcpf\b|\brg\b")
_LEGAL = re.compile(
    r"autoriz|consint|lgpd|termos de uso|politica de privacidade|consentimento|\bciente\b"
    r"|aceit\w* (?:os |as |o |a )?(?:termos|politica|condicoes)"
    r"|concord\w* com (?:os |as |o |a )?(?:termos|politica|condicoes|uso|tratamento)"
    r"|declar\w* (?:que|ciencia)")
SHORT_LABEL = 6  # contact-field answers apply only to short label-like questions


def classify_field(question: str) -> str:
    text = normalize(question)
    if _SENSITIVE.search(text):
        return "sensivel"
    if _LEGAL.search(text):
        return "legal"
    return "geral"


def _content(question: str) -> frozenset[str]:
    """Meaningful words (and every number) of a question: wording noise is dropped, skills and numbers stay."""
    words = re.findall(r"[a-z0-9]+", normalize(question))
    return frozenset(w for w in words if w not in _STOP and (len(w) >= 3 or w.isdigit()))


def match_bank(question: str, bank: list[AnswerEntry]) -> AnswerEntry | None:
    """A saved answer applies only when both questions have exactly the same meaningful words."""
    wanted = _content(question)
    if not wanted:
        return None
    return next((e for e in bank if _content(e.question) == wanted), None)


def _num(value: float) -> str:
    return str(int(value)) if float(value) == int(value) else str(value)


def _words(question: str) -> int:
    return len(re.findall(r"[a-z0-9]+", normalize(question)))


def builtin_answer(question: str, p: Profile) -> str | None:
    """Fill a field from the profile only when the question is clearly that field's label."""
    text, s = normalize(question), p.screening
    if _words(question) <= 10 and re.search(
            r"pretensao salarial|pretensao de salario|salario pretendido|expectativa salarial", text):
        return str(s.salary_expectation) if s.salary_expectation is not None else None
    if _content(question) == frozenset({"disponibilidade"}) or re.search(
            r"quando .{0,20}comecar|data de inicio|prazo para inicio|aviso previo"
            r"|disponibilidade (?:de|para) (?:inicio|iniciar|comecar|entrada)", text):
        return s.availability or None
    if _words(question) <= SHORT_LABEL and re.search(r"\be-?mail\b", text):
        return s.email or None
    if _words(question) <= SHORT_LABEL and re.search(r"telefone|celular|whatsapp", text):
        return s.phone or None
    m = re.search(r"experiencia\s+(?:\w+\s+){0,3}?(?:com|em|no|na)\s+(.+?)\s*\??$", text)
    if m:
        skill = m.group(1).strip()
        for name, years in s.years_by_skill.items():
            if normalize(name) == skill:
                return _num(years)
    return None


@dataclass
class Resolution:
    question: str
    category: str
    status: str  # "respondida" | "em_branco"
    answer: str | None
    source: str  # "banco" | "perfil" | ""


def resolve(questions: list[str], p: Profile) -> list[Resolution]:
    out = []
    for q in questions:
        category = classify_field(q)
        saved = match_bank(q, p.answers)
        if saved:
            out.append(Resolution(q, category, "respondida", saved.answer, "banco"))
            continue
        built = builtin_answer(q, p) if category == "geral" else None  # sensitive/legal: bank only
        if built is not None:
            out.append(Resolution(q, category, "respondida", built, "perfil"))
        else:
            out.append(Resolution(q, category, "em_branco", None, ""))
    return out


def add_pending(p: Profile, questions: list[str], vaga: str, today: date) -> None:
    for q in questions:
        content = _content(q)
        if match_bank(q, p.answers) or any(_content(x.question) == content for x in p.pending):
            continue
        p.pending.append(PendingQuestion(q, classify_field(q), vaga, today.isoformat()))


def upsert_answer(p: Profile, entry: AnswerEntry) -> None:
    content = _content(entry.question)
    p.answers = [a for a in p.answers if _content(a.question) != content] + [entry]
    p.pending = [x for x in p.pending if _content(x.question) != content]
