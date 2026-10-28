from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.parse import parse_qsl, urlsplit

from jobbot.evaluate import constraints_ok
from jobbot.match import normalize
from jobbot.posting import Posting
from jobbot.schema import Profile, SeenPosting

COUNTED = ("preparado", "enviada", "descartada", "externa", "desconhecido")
KEEP_PARAMS = ("jk", "vjk", "currentjobid", "id")  # query parameters that identify the vacancy
MIN_NAME = 4


def vaga_key(url: str) -> str:
    """Stable identity of a vacancy URL: no scheme, www, tracking parameters, fragment or trailing slash."""
    url = (url or "").strip()
    if not url:
        return ""
    parts = urlsplit(url if "//" in url else f"https://{url}")
    host = parts.netloc.lower().removeprefix("www.")
    if not host:
        return ""
    query = sorted((k.lower(), v.lower()) for k, v in parse_qsl(parts.query) if k.lower() in KEEP_PARAMS)
    qs = "&".join(f"{k}={v}" for k, v in query)
    return host + parts.path.lower().rstrip("/") + (f"?{qs}" if qs else "")


def alt_key(company: str, title: str) -> str:
    return f"{normalize(company)}|{normalize(title)}"


def _reason(raw: str) -> str:
    return "repetida" if raw == "preparada" else raw


def seen_reason(p: Profile, url: str, company: str, title: str, platform: str) -> str | None:
    """Why this vacancy must be skipped as already known, or None. company+title only crosses platforms."""
    key = vaga_key(url)
    if key:
        for e in p.seen:
            if e.key == key:
                return _reason(e.reason)
        if any(vaga_key(a.url) == key for a in p.applications):
            return "repetida"
    if company.strip() and title.strip():
        alt = alt_key(company, title)
        for e in p.seen:
            if e.platform != platform and e.alt_key == alt:
                return _reason(e.reason)
        if any(a.platform and a.platform != platform and alt_key(a.company, a.title) == alt for a in p.applications):
            return "repetida"
    return None


def _same_company(a: str, b: str) -> bool:
    a, b = normalize(a or ""), normalize(b or "")
    if not a or not b or min(len(a), len(b)) < MIN_NAME:
        return a == b and bool(a)
    return a in b or b in a


def filter_reason(posting: Posting, p: Profile) -> str | None:
    c = p.constraints
    if c.current_employer and _same_company(c.current_employer, posting.company):
        return "empregador_atual"
    if any(v and _same_company(v, posting.company) for v in c.vetoed_companies):
        return "empresa_vetada"
    if not constraints_ok(posting, p):
        return "fora_das_restricoes"
    return None


@dataclass
class Capacity:
    allowed: int
    today: int
    pending: int
    paused: bool
    reason: str


def capacity(p: Profile, platform: str, today: date) -> Capacity:
    done = sum(1 for a in p.applications
               if a.platform == platform and a.date == today.isoformat() and a.status in COUNTED)
    pending = sum(1 for a in p.applications if a.platform == platform and a.status == "preparado")
    state = next((s for s in p.platforms if s.platform == platform), None)
    paused = bool(state and state.paused)
    if paused:
        return Capacity(0, done, pending, True, f"plataforma pausada ({state.reason or 'sem motivo informado'})")
    if pending >= p.run.per_round:
        return Capacity(0, done, pending, False, f"revise as {pending} abas pendentes antes de uma nova rodada")
    left = p.run.per_day - done
    if left <= 0:
        return Capacity(0, done, pending, False, "limite diário atingido")
    return Capacity(min(p.run.per_round, left), done, pending, False, "")


def mark_seen(p: Profile, platform: str, posting: Posting, reason: str, today: date) -> None:
    key = vaga_key(posting.url)
    for e in p.seen:
        if e.key == key and e.platform == platform and key:
            e.reason, e.date = reason, today.isoformat()
            return
    p.seen.append(SeenPosting(key, alt_key(posting.company, posting.title), platform, posting.company,
                              posting.title, posting.url, reason, today.isoformat()))
