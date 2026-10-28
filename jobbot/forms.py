from __future__ import annotations

import re

from jobbot.match import normalize
from jobbot.schema import CONTRACTS, EDU_LEVELS, EDU_STATUS, KINDS, LEVELS

INTERVIEW_MARKER = "# JOBBOT:interview"

_TEMPLATE = """\
# JOBBOT:interview
# QUESTIONÁRIO DO PERFIL
# COMO PREENCHER
#  - Escreva depois dos dois pontos. Deixe em branco o que não se aplica (não precisa escrever "-" nem "?").
#  - Linhas que começam com # são ignoradas: são só instruções. Este arquivo fica só neste computador.
#  - Onde há "|", separe as partes com esse sinal, sempre na ordem mostrada no "Formato".
#  - Onde há uma linha só com "-", escreva um item por linha, cada um começando com "- ".
#  - Para repetir um bloco [emprego] ou [projeto], copie só as linhas [emprego]...Entregas (sem as instruções).

## 1. IDENTIDADE
Nome completo:
Idade:
# Estado: só a sigla, duas letras. Exemplo: SP
Estado:
# Cidade: o nome da cidade. Exemplo: São Paulo
Cidade:
# Links (opcional): o bot lê o que está público neles para preencher e conferir o seu perfil.
LinkedIn:
GitHub:
# Outros links: site, portfólio, YouTube. Separe por vírgula.
Outros links:

## 2. EXPERIÊNCIAS
# Um bloco [emprego] por emprego formal.
# Início e Fim: mês e ano. Exemplos: 2022-10 ou out 2022. Fim: escreva "atual" se ainda trabalha lá.
# Entregas: uma por linha, começando com "- ", no formato  o que você fez | resultado em número
#   Exemplo: - Automatizei os relatórios semanais | de 4h para 20 min por semana
#   O número é opcional, mas ajuda muito. Só escreva um número se ele for real.
[emprego]
Empresa:
Cargo:
Início:
Fim:
Entregas:
-

# Um bloco [projeto] por projeto pessoal, freela, voluntariado ou trabalho autodidata.
# Tipo: escolha UMA palavra: projeto, voluntariado, autodidata ou freela.
# Início e Fim: só o ano com 4 dígitos. Exemplo: 2026
# Descrição: o que é, para quem, e qual foi o seu papel. Pode ser em um parágrafo só.
# Link: opcional.
[projeto]
Nome:
Tipo:
Início:
Fim:
Descrição:
Link:

## 3. SKILLS
# Uma por linha, começando com "- ", com 3 partes:  nome | nível | evidência
# Nível: escolha UM destes: especialista (ensino ou resolvo qualquer caso), médio (uso com autonomia),
#   iniciante (estou aprendendo).
# Evidência: onde usou e por quanto tempo. Cursos contam, mas diga que é curso.
#   Exemplo: - SQL | médio | 2 anos na empresa atual, consultas e validação de dados
-

## 4. CERTIFICAÇÕES, IDIOMAS E FORMAÇÃO
# --- 4a. Certificações (cursos ou provas com certificado) ---
# Formato:  nome | emissor | ano      Exemplo: - Inglês C1 | WiseUP | 2021
Certificações:
-
# --- 4b. Idiomas ---
# Formato:  idioma | nível (básico, profissional, fluente ou nativo)      Exemplo: - Inglês | fluente
Idiomas:
-
# --- 4c. Formação (escola e faculdade) ---
# Formato:  instituição | curso | nível | início | fim | situação
# Nível: medio, tecnico, graduacao, pos, mestrado ou doutorado.
# Situação: concluido, cursando ou trancado. Início e Fim: só o ano; Fim pode ser a previsão.
# Exemplo: - São Judas | Sistemas de Informação | graduacao | 2023 | 2027 | cursando
Formação:
-

## 5. RESTRIÇÕES
# Modalidade: remoto, híbrido e/ou presencial, separados por vírgula. Exemplo: remoto, híbrido
Modalidade:
# Cidades: nomes separados por vírgula, sem comentários. Exemplo: São Paulo, Osasco
Cidades:
# Empresas e setores vetados: nomes separados por vírgula. Deixe vazio se nenhum.
Empresas vetadas:
Setores vetados:
Empregador atual:
# Deslocamento: tempo máximo de ônibus ou metrô, só de ida, em minutos, para vaga híbrida ou presencial. Exemplo: 120
Tempo máximo de deslocamento:
# Perto de casa: bairro ou estação de metrô (ponto de partida para medir o trajeto no Maps). Exemplo: Metrô Tatuapé
Perto de casa:
# Senioridade aceita: estágio, júnior, pleno e/ou sênior, separados por vírgula. Exemplo: júnior, pleno
Senioridade:
# Presencial só a partir de: salário mensal mínimo para aceitar vaga presencial. Exemplo: 6000
Presencial só a partir de:

## 6. TRIAGEM
# Pretensão salarial: só o valor mensal em reais. Exemplo: 5000
Pretensão salarial:
# Contrato: CLT, PJ ou ambos
Contrato:
# Disponibilidade: quando você pode começar. Exemplo: imediata ou 30 dias
Disponibilidade:
E-mail:
Telefone:
# Anos por skill, um por linha:  skill | anos      Exemplo: - SQL | 2
Anos por skill:
-

## 7. ESTILO DE TRABALHO
# Responda A ou B em cada escolha.
# 1. Aprofundar um tema por meses (A) ou coordenar vários temas (B)
# 2. Dia bem-sucedido: resolvi um problema técnico difícil (A) ou destravei o time (B)
# 3. Prefiro poucas reuniões objetivas (A) ou é nas reuniões que eu decido (B)
# 4. Crescer virando referência técnica (A) ou liderando pessoas (B)
# 5. Ritmo de foco longo e silencioso (A) ou muitas interações curtas (B)
# 6. Quando algo quebra, conserto a causa técnica (A) ou alinho o processo (B)
# 7. Aprender sozinho estudando (A) ou montando um grupo de estudo (B)
# 8. Sucesso é a qualidade do que entrego (A) ou o resultado da equipe (B)
Escolha 1:
Escolha 2:
Escolha 3:
Escolha 4:
Escolha 5:
Escolha 6:
Escolha 7:
Escolha 8:
# Estilo: como você descreveria seu jeito de trabalhar, em palavras soltas. Exemplo: organizador, analítico
Estilo:
# Motivadores: o que te move, separados por vírgula. Exemplo: autonomia, aprender, dinheiro
Motivadores:
"""


def interview_form() -> str:
    return _TEMPLATE


# (section, block) -> label -> (key, is_list)
_FIELDS: dict[tuple[int, str], dict[str, tuple[str, bool]]] = {
    (1, ""): {"nome completo": ("name", False), "idade": ("age", False), "estado": ("state", False),
              "cidade": ("city", False), "linkedin": ("linkedin", False), "github": ("github", False),
              "outros links": ("links", False)},
    (2, "emprego"): {"empresa": ("company", False), "cargo": ("role", False), "inicio": ("start", False),
                     "fim": ("end", False), "entregas": ("bullets", True)},
    (2, "projeto"): {"nome": ("name", False), "tipo": ("kind", False), "inicio": ("start", False),
                     "fim": ("end", False), "descricao": ("description", False), "link": ("url", False)},
    (4, ""): {"certificacoes": ("certs", True), "idiomas": ("langs", True), "formacao": ("edu", True)},
    (5, ""): {"modalidade": ("modality", False), "cidades": ("cities", False),
              "empresas vetadas": ("vetoed_companies", False), "setores vetados": ("vetoed_sectors", False),
              "empregador atual": ("current_employer", False),
              "presencial so a partir de": ("onsite_min", False), "senioridade": ("seniority", False),
              "tempo maximo de deslocamento": ("commute", False), "perto de casa": ("home", False)},
    (6, ""): {"pretensao salarial": ("salary", False), "contrato": ("contract", False),
              "disponibilidade": ("availability", False), "e-mail": ("email", False),
              "telefone": ("phone", False), "anos por skill": ("years", True)},
    (7, ""): {**{f"escolha {i}": (f"c{i}", False) for i in range(1, 9)},
              "estilo": ("style", False), "motivadores": ("motivators", False)},
}
_SECTION_LIST = {3: "skills"}  # section 3 has no label: its "-" lines are the list
_MODALITIES = ("remoto", "hibrido", "presencial")
_DATE = re.compile(r"^\d{4}(-\d{2})?$")
_MONTHS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
_NOW = ("atual", "atualmente", "hoje", "presente")
_YEAR = re.compile(r"^\d{4}$")

Raw = tuple[str, int]  # value, line number


def _scan(text: str) -> tuple[dict, list[str]]:
    """Read the file into raw values with line numbers. Nothing is interpreted here."""
    errors: list[str] = []
    data: dict = {n: {"": {}} for n in range(1, 8)}
    data[2] = {"emprego": [], "projeto": []}
    data[3] = {"skills": []}
    section, block, current = None, None, None
    first = True
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if first and line:
            first = False
            if line != INTERVIEW_MARKER:
                return data, [f"linha {n}: este arquivo não é o questionário (esperado {INTERVIEW_MARKER})"]
            continue
        if not line:
            continue
        if line.startswith("##"):
            m = re.match(r"##\s*(\d)", line)
            section, block, current = (int(m.group(1)) if m and 1 <= int(m.group(1)) <= 7 else None), None, None
            if section is None:
                errors.append(f"linha {n}: seção inválida: {line!r}")
            continue
        if line.startswith("#"):
            continue
        if section is None:
            errors.append(f"linha {n}: texto fora de uma seção: {line!r}")
            continue
        if line.lower() in ("[emprego]", "[projeto]") and section == 2:
            block = line.strip("[]").lower()
            data[2][block].append({})
            current = None
            continue
        if line.startswith("-"):
            item = line[1:].strip()
            if current is None and section in _SECTION_LIST:
                current = _SECTION_LIST[section]
            if current is None:
                errors.append(f"linha {n}: item solto, sem um campo de lista acima: {line!r}")
            elif item:
                _bucket(data, section, block, current).append((item, n))
            continue
        label, sep, value = line.partition(":")
        key = normalize(label)
        spec = _FIELDS.get((section, block or ""), {}).get(key)
        if not sep or spec is None:
            errors.append(f"linha {n}: campo desconhecido {label.strip()!r}")
            continue
        field, is_list = spec
        if is_list:
            current = field
            if value.strip():
                _bucket(data, section, block, field).append((value.strip(), n))
        else:
            current = None
            blank = value.strip() in ("-", "?")  # a lone placeholder means "not answered"
            _record(data, section, block)[field] = ("" if blank else value.strip(), n)
    return data, errors


def _record(data: dict, section: int, block: str | None) -> dict:
    return data[2][block][-1] if section == 2 else data[section][""]


def _bucket(data: dict, section: int, block: str | None, field: str) -> list:
    if section == 3:
        return data[3]["skills"]
    return _record(data, section, block).setdefault(field, [])


def _month(value: str) -> str:
    """Turn 'out 2022' into '2022-10'; anything else is returned unchanged for validation."""
    m = re.match(r"^([a-zç]{3})[a-z]*\.?(?:\s+de)?\s+(\d{4})$", normalize(value))
    return f"{m.group(2)}-{_MONTHS.index(m.group(1)) + 1:02d}" if m and m.group(1) in _MONTHS else value


def _val(rec: dict, key: str) -> str:
    return rec.get(key, ("", 0))[0]


def _line(rec: dict, key: str) -> int:
    return rec.get(key, ("", 0))[1]


def _split(item: str, parts: int) -> list[str]:
    cells = [c.strip() for c in item.split("|")]
    return (cells + [""] * parts)[:parts]


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _choice(value: str, options, n: int, label: str, errors: list[str]) -> str | None:
    if not value:
        return None
    norm = normalize(value)
    found = next((o for o in options if normalize(o) == norm), None)
    if found is None:
        errors.append(f"linha {n}: {label} inválido(a): {value!r} (use {', '.join(options)})")
    return found


def parse_interview(text: str) -> tuple[dict[str, dict], list[str]]:
    """Parse the filled questionnaire into the data of each interview step, or a list of line-numbered errors."""
    raw, errors = _scan(text)
    if errors and errors[0].endswith(f"(esperado {INTERVIEW_MARKER})"):
        return {}, errors
    steps: dict[str, dict] = {}

    ident = raw[1][""]
    if ident:
        data: dict = {}
        if _val(ident, "age"):
            if _val(ident, "age").isdigit():
                data["age"] = int(_val(ident, "age"))
            else:
                errors.append(f"linha {_line(ident, 'age')}: idade deve ser um número inteiro")
        if _val(ident, "state") and not re.fullmatch(r"[A-Za-z]{2}", _val(ident, "state")):
            errors.append(f"linha {_line(ident, 'state')}: estado deve ser a sigla de duas letras (por exemplo SP)")
        for key in ("name", "state", "city", "linkedin", "github"):
            if _val(ident, key):
                data[key] = _val(ident, key)
        if _val(ident, "links"):
            data["links"] = _csv(_val(ident, "links"))
        if data and not data.get("name"):
            errors.append("linha 1: o nome completo é obrigatório")
        if data:
            steps["identidade"] = data

    exp_step: dict = {}
    experiences = []
    for rec in raw[2]["emprego"]:
        if not rec:
            continue
        if not _val(rec, "company") or not _val(rec, "role"):
            if any(v for k, v in rec.items() if k != "bullets" and v[0]) or rec.get("bullets"):
                errors.append("linha 1: emprego sem empresa ou cargo")
            continue
        for key in ("start", "end"):
            if normalize(_val(rec, key)) in _NOW:
                rec[key] = ("", _line(rec, key))
            else:
                rec[key] = (_month(_val(rec, key)), _line(rec, key))
            if _val(rec, key) and not _DATE.match(_val(rec, key)):
                errors.append(f"linha {_line(rec, key)}: data inválida {_val(rec, key)!r} (use AAAA-MM, por exemplo 2022-10)")
        bullets = []
        for item, n in rec.get("bullets", []):
            what, result = _split(item, 2)
            bullets.append({"text": what, "metric": result or None})
        experiences.append({"company": _val(rec, "company"), "role": _val(rec, "role"), "start": _val(rec, "start"),
                            "end": _val(rec, "end") or None, "bullets": bullets})
    projects = []
    for rec in raw[2]["projeto"]:
        if not rec or not _val(rec, "name"):
            continue
        kind = _choice(_val(rec, "kind") or "projeto", KINDS, _line(rec, "kind"), "tipo", errors)
        for key in ("start", "end"):
            if _val(rec, key) and not _YEAR.match(_val(rec, key)):
                errors.append(f"linha {_line(rec, key)}: ano inválido {_val(rec, key)!r} (use AAAA)")
        projects.append({"name": _val(rec, "name"), "description": _val(rec, "description"),
                         "url": _val(rec, "url") or None, "kind": kind or "projeto",
                         "start": _val(rec, "start"), "end": _val(rec, "end") or None})
    if experiences:
        exp_step["experiences"] = experiences
    if projects:
        exp_step["projects"] = projects
    if exp_step:
        steps["experiencias"] = exp_step

    skills = []
    for item, n in raw[3]["skills"]:
        name, level, evidence = _split(item, 3)
        lv = _choice(level, LEVELS, n, "nível", errors)
        if name and not level:
            errors.append(f"linha {n}: nível obrigatório para {name!r} (especialista, médio ou iniciante)")
        if name:
            skills.append({"name": name, "level": lv or "iniciante", "evidence": evidence})
    if skills:
        steps["skills"] = {"skills": skills}

    sec4, cert_step = raw[4][""], {}
    certs = []
    for item, n in sec4.get("certs", []):
        name, issuer, year = _split(item, 3)
        if year and not _YEAR.match(year):
            errors.append(f"linha {n}: ano inválido {year!r} na certificação")
        certs.append({"name": name, "issuer": issuer, "year": int(year) if _YEAR.match(year or "x") else None})
    langs = [dict(zip(("name", "level"), _split(item, 2))) for item, _ in sec4.get("langs", [])]
    edu = []
    for item, n in sec4.get("edu", []):
        inst, course, level, start, end, status = _split(item, 6)
        lv = _choice(level, EDU_LEVELS, n, "nível de formação", errors)
        st = _choice(status, EDU_STATUS, n, "situação", errors)
        edu.append({"institution": inst, "course": course, "level": lv or "", "start": start,
                    "end": end or None, "status": st or ""})
    for key, value in (("certifications", certs), ("languages", langs), ("education", edu)):
        if value:
            cert_step[key] = value
    if cert_step:
        steps["certificacoes_idiomas"] = cert_step

    sec5 = raw[5][""]
    if any(v[0] for v in sec5.values()):
        modality = []
        for token in _csv(_val(sec5, "modality")):
            m = _choice(token, _MODALITIES, _line(sec5, "modality"), "modalidade", errors)
            if m:
                modality.append(m)
        steps["restricoes"] = {"constraints": {
            "modality": modality, "cities": _csv(_val(sec5, "cities")),
            "vetoed_companies": _csv(_val(sec5, "vetoed_companies")),
            "vetoed_sectors": _csv(_val(sec5, "vetoed_sectors")),
            "current_employer": _val(sec5, "current_employer") or None}}
        levels = [m for t in _csv(_val(sec5, "seniority"))
                  if (m := _choice(t, ("estagio", "junior", "pleno", "senior"), _line(sec5, "seniority"), "senioridade", errors))]
        if levels:
            steps["restricoes"]["constraints"]["seniority"] = levels
        if _val(sec5, "home"):
            steps["restricoes"]["constraints"]["home_area"] = _val(sec5, "home")
        commute = re.search(r"\d+", _val(sec5, "commute"))
        if commute:
            steps["restricoes"]["constraints"]["max_commute_minutes"] = int(commute.group())
        elif _val(sec5, "commute"):
            errors.append(f"linha {_line(sec5, 'commute')}: o tempo de deslocamento deve ser um número de minutos")
        digits = re.sub(r"[^\d]", "", _val(sec5, "onsite_min").split(",")[0])
        if digits:
            steps["restricoes"]["constraints"]["onsite_min_salary"] = int(digits)
        elif _val(sec5, "onsite_min"):
            errors.append(f"linha {_line(sec5, 'onsite_min')}: salário mínimo presencial deve ser um número")

    sec6 = raw[6][""]
    screening: dict = {}
    if _val(sec6, "salary"):
        digits = re.sub(r"[^\d]", "", _val(sec6, "salary").split(",")[0])
        if digits:
            screening["salary_expectation"] = int(digits)
        else:
            errors.append(f"linha {_line(sec6, 'salary')}: pretensão salarial deve ser um número")
    contract = _choice(_val(sec6, "contract"), CONTRACTS, _line(sec6, "contract"), "contrato", errors)
    if contract:
        screening["contract"] = contract
    for key, out in (("availability", "availability"), ("email", "email"), ("phone", "phone")):
        if _val(sec6, key):
            screening[out] = _val(sec6, key)
    years = {}
    for item, n in sec6.get("years", []):
        skill, value = _split(item, 2)
        try:
            years[skill] = float(value.replace(",", "."))
        except ValueError:
            errors.append(f"linha {n}: anos inválidos para {skill!r}: {value!r}")
    if years:
        screening["years_by_skill"] = years
    if screening:
        steps["triagem"] = {"screening": screening}

    sec7 = raw[7][""]
    picks = [(_val(sec7, f"c{i}").upper(), _line(sec7, f"c{i}")) for i in range(1, 9)]
    answered = [p for p in picks if p[0]]
    behavior: dict = {}
    if answered:
        bad = [(v, n) for v, n in answered if v not in ("A", "B")]
        for i, (v, n) in enumerate(picks, 1):
            if v and v not in ("A", "B"):
                errors.append(f"linha {n}: escolha {i} deve ser A ou B")
        if len(answered) < 8 and not bad:
            errors.append("linha 1: responda as 8 escolhas do estilo de trabalho (A ou B)")
        elif not bad:
            a = sum(1 for v, _ in picks if v == "A")
            behavior["track"] = "especialista" if a >= 6 else "gestao" if 8 - a >= 6 else "indefinido"
    if _val(sec7, "style"):
        behavior["work_style"] = _val(sec7, "style")
    if _val(sec7, "motivators"):
        behavior["motivators"] = _csv(_val(sec7, "motivators"))
    if behavior:
        steps["comportamento"] = {"behavior": behavior}

    return ({} if errors else steps), errors


# ---------------------------------------------------------------- assessment form

TEST_MARKER = "# JOBBOT:teste"
SITUATION_QUESTIONS = (
    "Conte uma vez em que você ficou realmente orgulhoso de um trabalho. O que você fez?",
    "Descreva um dia de trabalho ideal, do começo ao fim.",
    "Se dinheiro não fosse problema por um ano, no que você trabalharia ou estudaria?",
)
_SCALES = {
    "valores": "1 = nada importante · 3 = neutro · 5 = extremamente importante",
    "interesses": "1 = não gostaria nada · 3 = tanto faz · 5 = gostaria muito",
    "personalidade": "1 = discordo totalmente · 3 = neutro · 5 = concordo totalmente",
    "ancoras": "1 = não me descreve · 3 = em parte · 5 = me descreve totalmente",
    "estilo": "1 = quase nunca · 3 = às vezes · 5 = quase sempre",
}


def assessment_form(bank) -> str:
    lines = [
        TEST_MARKER,
        "# TESTE DE PERFIL (cerca de 10 minutos)",
        "# Em cada linha, escreva um número de 1 a 5 depois do sinal =. Responda sem pensar na resposta certa.",
        "# Pode parar e voltar depois: o que você deixar em branco continua pendente.",
        "",
    ]
    for layer in ("valores", "interesses", "personalidade", "ancoras", "estilo"):
        lines += [f"## {layer.upper()}", f"# Escala: {_SCALES[layer]}"]
        lines += [f"{i.id} | {i.text} | =" for i in bank if i.layer == layer]
        lines.append("")
    lines += ["## PERGUNTAS ABERTAS", "# Responda com exemplos reais. Pode usar mais de uma linha."]
    for n, q in enumerate(SITUATION_QUESTIONS, 1):
        lines += [f"Pergunta {n}: {q}", "Resposta:", ""]
    return "\n".join(lines)


_ITEM = re.compile(r"^(?P<id>[a-z0-9]+)\s*\|.*\|\s*=\s*(?P<v>.*)$")


def parse_assessment(text: str, bank) -> tuple[dict[str, int], list[dict[str, str]], list[str]]:
    known = {i.id for i in bank}
    answers: dict[str, int] = {}
    errors: list[str] = []
    situations: list[dict[str, str]] = []
    current: dict | None = None
    in_open = False
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("## "):
            in_open = line.upper().startswith("## PERGUNTAS")
            current = None
            continue
        if not line or (line.startswith("#") and not line.startswith("# JOBBOT")):
            continue
        if in_open:
            m = re.match(r"^Pergunta\s+(\d+):", line)
            if m:
                idx = int(m.group(1)) - 1
                current = {"pergunta": SITUATION_QUESTIONS[idx] if 0 <= idx < len(SITUATION_QUESTIONS) else line, "resposta": ""}
                situations.append(current)
            elif line.lower().startswith("resposta:") and current is not None:
                current["resposta"] = line.split(":", 1)[1].strip()
            elif current is not None:
                current["resposta"] = f"{current['resposta']} {line}".strip()
            continue
        m = _ITEM.match(line)
        if not m:
            continue
        item_id, value = m.group("id"), m.group("v").strip()
        if item_id not in known:
            errors.append(f"linha {n}: item desconhecido {item_id!r}")
        elif value:
            if value.isdigit() and 1 <= int(value) <= 5:
                answers[item_id] = int(value)
            else:
                errors.append(f"linha {n}: {item_id}: use um número de 1 a 5 (recebi {value!r})")
    return answers, [s for s in situations if s["resposta"]], errors


# ---------------------------------------------------------------- follow-up form

FOLLOWUP_MARKER = "# JOBBOT:followup"
MAX_GAPS = 12
_FIELD_QUESTIONS = {
    "age": "Qual a sua idade?",
    "state": "Em que estado você mora (sigla, por exemplo SP)?",
    "city": "Em que cidade você mora?",
    "salary_expectation": "Qual a sua pretensão salarial (R$ por mês)?",
    "email": "Qual e-mail devo usar nas candidaturas?",
    "phone": "Qual telefone devo usar nas candidaturas?",
}


def _gaps(p) -> list[tuple[str, str]]:
    gaps: list[tuple[str, str]] = []
    have = {"age": p.age, "state": p.state, "city": p.city, "salary_expectation": p.screening.salary_expectation,
            "email": p.screening.email, "phone": p.screening.phone}
    gaps += [(f"field:{k}", q) for k, q in _FIELD_QUESTIONS.items() if have[k] in (None, "")]
    gaps += [(f"evidence:{s.name}", f"Skill {s.name} ({s.level}): onde usou e por quanto tempo?")
             for s in p.skills if s.level in ("especialista", "medio") and not s.evidence.strip()]
    for i, e in enumerate(p.experiences):
        gaps += [(f"metric:{i}:{j}", f"{e.company}, \"{b.text}\": qual foi o resultado em número? (deixe vazio se não souber)")
                 for j, b in enumerate(e.bullets) if not b.metric]
    return gaps[:MAX_GAPS]


def followup_form(p) -> str | None:
    gaps = _gaps(p)
    if not gaps:
        return None
    lines = [FOLLOWUP_MARKER, "# SEGUIMENTO: só o que ainda falta. Escreva a resposta depois do sinal =.",
             "# Deixe em branco o que não souber. Só escreva números que sejam reais.", ""]
    lines += [f"@{token} | {question} | =" for token, question in gaps]
    return "\n".join(lines) + "\n"


_FOLLOW = re.compile(r"^@(?P<token>\S+)\s*\|.*\|\s*=\s*(?P<ans>.*)$")


def parse_followup(text: str) -> tuple[list[tuple[str, str, int]], list[str]]:
    items, errors = [], []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if n == 1 and line != FOLLOWUP_MARKER:
            return [], [f"linha 1: este arquivo não é um seguimento (esperado {FOLLOWUP_MARKER})"]
        m = _FOLLOW.match(line)
        if m and m.group("ans").strip():
            items.append((m.group("token"), m.group("ans").strip(), n))
    return items, errors


def apply_followup(p, items: list[tuple[str, str, int]]) -> list[str]:
    errors = []
    for token, answer, n in items:
        kind, _, rest = token.partition(":")
        try:
            if kind == "field":
                if rest in ("age", "salary_expectation"):
                    digits = re.sub(r"[^\d]", "", answer.split(",")[0])
                    if not digits:
                        raise ValueError
                    value = int(digits)
                    if rest == "age":
                        p.age = value
                    else:
                        p.screening.salary_expectation = value
                elif rest in ("state", "city"):
                    setattr(p, rest, answer)
                elif rest in ("email", "phone"):
                    setattr(p.screening, rest, answer)
                else:
                    errors.append(f"linha {n}: campo desconhecido {rest!r}")
            elif kind == "evidence":
                skill = next((s for s in p.skills if normalize(s.name) == normalize(rest)), None)
                if skill is None:
                    errors.append(f"linha {n}: skill desconhecida {rest!r}")
                else:
                    skill.evidence = answer
            elif kind == "metric":
                i, j = (int(x) for x in rest.split(":"))
                p.experiences[i].bullets[j].metric = answer
            else:
                errors.append(f"linha {n}: item desconhecido {token!r}")
        except (ValueError, IndexError):
            label = {"age": "idade", "salary_expectation": "pretensão salarial"}.get(rest, token)
            errors.append(f"linha {n}: {label} inválido(a): {answer!r}")
    return errors
