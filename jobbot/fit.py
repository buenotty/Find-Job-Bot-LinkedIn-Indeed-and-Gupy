from __future__ import annotations

import re

from jobbot.match import normalize
from jobbot.schema import Profile

FLAGS = ("proibe_ia", "cronometrado", "tentativa_unica", "vigiado")
_AI = r"(?:\bia\b|inteligencia artificial|chatgpt)"
_PATTERNS = {
    "proibe_ia": [
        rf"sem (?:o )?(?:uso|ajuda|auxilio|apoio|consulta)(?: de| a| da| do)? {_AI}",
        rf"nao (?:consulte|use|utilize|usar|utilizar|pode)\b.{{0,40}}{_AI}",
        rf"nao e permitid[oa].{{0,30}}{_AI}",
        rf"proibid[oa].{{0,50}}{_AI}",
        rf"{_AI}.{{0,25}}(?:proibid|nao e permitid|nao sera permitid|nao pode)",
    ],
    "cronometrado": [r"cronometr\w*", r"temporizador",
                     r"tempo (?:limite|maximo|total|de duracao|para (?:responder|concluir))"],
    "tentativa_unica": [
        r"(?:unica|uma so) tentativa", r"uma unica vez",
        r"nao (?:podera|sera possivel|e possivel) (?:refazer|voltar|repetir)",
        r"apenas uma (?:vez|chance|tentativa)",
        r"so (?:pode|podera)(?: ser)? (?:fazer|feito|realizar|realizado|responder|respondido)(?: o teste)?(?: apenas)? uma vez",
    ],
    "vigiado": [r"camera", r"webcam", r"monitorad", r"monitoramento", r"proctor", r"fiscaliz", r"vigiad",
                r"gravacao da tela", r"tela .{0,20}gravad", r"gravad\w* .{0,10}tela", r"reconhecimento facial"],
}
HIGH, LOW = 70, 30
_DURATION = re.compile(r"\b\d+ ?(?:minutos|min|horas?)\b")
_ESTIMATE = re.compile(r"estimad|\bleva\b|levam|em media|aproximadamente|cerca de")


def _has_time_limit(norm: str) -> bool:
    """A duration counts as a limit unless its sentence only estimates how long things take."""
    return any(_DURATION.search(s) and not _ESTIMATE.search(s) for s in re.split(r"[.!?\n]+", norm))


def fit_risks(text: str) -> list[str]:
    """Risk flags found in a fit test's own text (PT-BR), in fixed order and without repeats."""
    norm = normalize(text)
    found = []
    for flag in FLAGS:
        hit = any(re.search(p, norm) for p in _PATTERNS[flag])
        if flag == "cronometrado":
            hit = hit or _has_time_limit(norm)
        if hit:
            found.append(flag)
    return found


def fit_action(mode: str, flags: list[str]) -> str:
    if "vigiado" in flags:
        return "deixar_para_pessoa"
    return {"pular": "pular", "perguntar": "perguntar"}.get(mode, "responder")


def behavior_summary(p: Profile) -> dict[str, str]:
    """What the model may use to draft honest fit answers; empty values mean no data, never a guess."""
    b = p.behavior
    out = {"work_style": b.work_style, "motivators": ", ".join(b.motivators), "track": b.track,
           "ultimo_teste": "", "dimensoes_altas": "", "dimensoes_baixas": "", "confiabilidade": ""}
    if p.assessments:
        a = p.assessments[-1]
        out["ultimo_teste"] = a.date
        out["confiabilidade"] = a.confiabilidade
        out["dimensoes_altas"] = ", ".join(k for k, v in a.scores.items() if v >= HIGH)
        out["dimensoes_baixas"] = ", ".join(k for k, v in a.scores.items() if v <= LOW)
    return out
