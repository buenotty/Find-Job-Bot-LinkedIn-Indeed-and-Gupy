from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import yaml

from jobbot.schema import Assessment
from jobbot.store import append_record, atomic_write, dump, profile_dir, read_yaml

LAYERS = ("valores", "interesses", "personalidade", "ancoras", "estilo")
SCALE = (1, 5)
UNIFORM_SHARE = 0.9
TWIN_GAP = 3
TRACK_GAP = 17  # technical vs management anchors closer than this (about one answer step on 4 items) are a tie
BOTH_HIGH = 67  # both anchors this high: a technical-leadership profile, not a tie
LEADS, AVOIDS = 63, 37  # leadership style score that breaks a tie toward management / toward the specialist path
HOLLAND = {"pratico": "R", "investigativo": "I", "artistico": "A", "social": "S", "empreendedor": "E",
           "convencional": "C"}


@dataclass(frozen=True)
class Item:
    id: str
    layer: str
    dimension: str
    text: str
    reverse: bool = False
    twin: str | None = None


def load_bank(path: Path | None = None) -> list[Item]:
    path = path or Path(__file__).parent / "data" / "items.yaml"
    try:
        items = [Item(**row) for row in yaml.safe_load(path.read_text(encoding="utf-8"))]
    except (TypeError, yaml.YAMLError) as e:
        raise ValueError(f"{path}: banco de itens inválido ({e})") from e
    ids = [i.id for i in items]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError(f"ids duplicados no banco: {dup}")
    for i in items:
        if i.layer not in LAYERS:
            raise ValueError(f"camada desconhecida em {i.id}: {i.layer!r}")
        if i.twin is not None and i.twin not in ids:
            raise ValueError(f"twin inexistente em {i.id}: {i.twin!r}")
    return items


def dimension_key(item: Item) -> str:
    return f"{item.layer}.{item.dimension}"


def _state_path(name: str) -> Path:
    return profile_dir(name) / "test_state.yaml"


def _answers(name: str) -> dict[str, int]:
    return dict(read_yaml(_state_path(name)).get("answers", {}))


def submit_answers(name: str, answers: dict[str, int], bank: list[Item]) -> None:
    """All-or-nothing: any bad id or value rejects the whole submission."""
    known = {i.id for i in bank}
    bad = sorted(
        k for k, v in answers.items()
        if k not in known or isinstance(v, bool) or not isinstance(v, int) or not SCALE[0] <= v <= SCALE[1]
    )
    if bad:
        raise ValueError(f"respostas inválidas (use inteiros de 1 a 5 e ids do banco): {bad}")
    atomic_write(_state_path(name), dump({"answers": {**_answers(name), **answers}}))


def progress(name: str, bank: list[Item]) -> tuple[str | None, int, int]:
    done = _answers(name)
    answered = sum(1 for i in bank if i.id in done)
    for layer in LAYERS:
        if any(i.layer == layer and i.id not in done for i in bank):
            return layer, answered, len(bank)
    return None, answered, len(bank)


def _adjusted(item: Item, value: int) -> int:
    return SCALE[0] + SCALE[1] - value if item.reverse else value


def score(answers: dict[str, int], bank: list[Item]) -> dict[str, int]:
    """Per dimension: share of the maximum possible score (self-relative, not a percentile)."""
    sums: dict[str, list[int]] = {}
    for item in bank:
        if item.id in answers:
            sums.setdefault(dimension_key(item), []).append(_adjusted(item, answers[item.id]))
    span = SCALE[1] - SCALE[0]
    return {k: int(100 * (sum(v) - len(v)) / (span * len(v)) + 0.5) for k, v in sums.items()}


def track_from_scores(scores: dict[str, int]) -> str:
    """Career track: technical vs management anchors; close scores are settled by high anchors, then by leadership style."""
    tech, mgmt = scores.get("ancoras.tecnica"), scores.get("ancoras.gestao")
    if tech is None or mgmt is None:
        return "indefinido"
    if abs(tech - mgmt) >= TRACK_GAP:
        return "especialista" if tech > mgmt else "gestao"
    if min(tech, mgmt) >= BOTH_HIGH:
        return "hibrido"
    lead = scores.get("estilo.lideranca")
    if lead is None or AVOIDS < lead < LEADS:
        return "indefinido"
    return "gestao" if lead >= LEADS else "especialista"


def holland_code(scores: dict[str, int]) -> str:
    """Three-letter Holland code (RIASEC) from the six interest scores, highest first; ties keep RIASEC order."""
    ranked = sorted(HOLLAND, key=lambda d: -scores.get(f"interesses.{d}", -1))
    return "".join(HOLLAND[d] for d in ranked[:3])


def consistency(answers: dict[str, int], bank: list[Item]) -> tuple[str, list[str]]:
    flags: list[str] = []
    if answers and max(Counter(answers.values()).values()) / len(answers) >= UNIFORM_SHARE:
        flags.append("respostas_uniformes")
    by_id = {i.id: i for i in bank}
    gaps = [
        abs(_adjusted(i, answers[i.id]) - _adjusted(by_id[i.twin], answers[i.twin]))
        for i in bank if i.twin and i.id in answers and i.twin in answers
    ]
    if gaps and 3 * sum(g >= TWIN_GAP for g in gaps) >= len(gaps):
        flags.append("pares_incoerentes")
    return ("baixa" if flags else "alta"), flags


def finish(name: str, bank: list[Item], situations: list[dict[str, str]], today: date) -> Assessment:
    answers = _answers(name)
    missing = [i.id for i in bank if i.id not in answers]
    if missing:
        raise ValueError(f"faltam {len(missing)} respostas para concluir o teste")
    reliability, flags = consistency(answers, bank)
    result = Assessment(today.isoformat(), score(answers, bank), reliability, flags, situations)
    append_record(name, "assessments", asdict(result))
    _state_path(name).unlink(missing_ok=True)
    return result
