from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

import yaml

from jobbot import store
from jobbot.assessment import finish, holland_code, load_bank, progress, submit_answers, track_from_scores
from jobbot.honesty import HonestyError, unsupported_numbers
from jobbot.cv import render_base_cv
from jobbot.market import Job, build_report, rank_focus
from jobbot.match import coverage, label, stretch_action
from jobbot.answers import add_pending, resolve, upsert_answer
from jobbot.classify import classify
from jobbot.evaluate import GOOD_MATCH, evaluate
from jobbot.forms import (
    FOLLOWUP_MARKER, INTERVIEW_MARKER, TEST_MARKER, apply_followup, assessment_form, followup_form,
    interview_form, parse_assessment, parse_followup, parse_interview,
)
from jobbot.fit import behavior_summary, fit_action, fit_risks
from jobbot.journey import journey
from jobbot.jobtypes import effective_rules, find_type, releasable_targets, validate_new_type
from jobbot.pdf import lossy_chars, write_pdf
from jobbot.posting import posting_from_dict
from jobbot.runs import capacity, filter_reason, mark_seen, seen_reason, vaga_key
from jobbot.resume import ResumeContent, build_resume, content_from_dict, doc_text, merge_content, review_sheet
from jobbot.orientation import classify_group, cv_released, market_claims, price_band, projected_match
from jobbot.schema import PLATFORMS, PlatformState, profile_from_dict, validate


def _status(a) -> int:
    print(store.next_step(a.name) or "completo")
    return 0


def _path(a) -> int:
    print(store.profile_dir(a.name))
    return 0


def _put(a) -> int:
    data = yaml.safe_load(Path(a.file).read_text(encoding="utf-8")) or {}
    store.put_step(a.name, a.step, data)
    return 0


def _validate(a) -> int:
    errors = validate(store.load_profile(a.name))
    print("\n".join(errors) if errors else "ok")
    return 1 if errors else 0


def _match(a) -> int:
    p = store.load_profile(a.name)
    pct, missing = coverage([r for r in a.required.split(",") if r.strip()], p.skills)
    print(f"pct: {pct}\nlabel: {label(pct)}\nstretch_action: {stretch_action(pct, p.stretch_policy)}"
          f"\nmissing: {', '.join(missing)}")
    return 0


def _market(a) -> int:
    p = store.load_profile(a.name)
    reports = []
    for f in a.files:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        reports.append(build_report(d["role"], [Job(**j) for j in d["jobs"]]))
    dash = lambda v: "-" if v is None else str(v)
    print("| Cargo | Match | Rótulo | Vagas | Salário mediano | Candidatos (mediana) | Skills que faltam |")
    print("|---|---|---|---|---|---|---|")
    for r in rank_focus(reports, p):
        print(f"| {r.role} | {r.coverage}% | {r.label} | {r.n_jobs} | {dash(r.salary_median)} "
              f"| {dash(r.applicants_median)} | {', '.join(r.missing) or '-'} |")
    return 0


def _cv(a) -> int:
    p = store.load_profile(a.name)
    summary = Path(a.summary_file).read_text(encoding="utf-8")
    text = render_base_cv(p, summary, date.today())
    out = store.profile_dir(a.name) / "cv-base.md"
    out.write_text(text, encoding="utf-8")
    print(out)
    return 0


def _check(a) -> int:
    p = store.load_profile(a.name)
    bad = unsupported_numbers(Path(a.file).read_text(encoding="utf-8"), p)
    print("\n".join(bad))
    return 1 if bad else 0


def _yaml(path: str):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _print_progress(name: str) -> None:
    layer, answered, total = progress(name, load_bank())
    print(f"proxima_camada: {layer}" if layer else "completo")
    print(f"respondidas: {answered}/{total}")


def _assess_answer(a) -> int:
    answers = _yaml(a.file)
    if not isinstance(answers, dict):
        raise ValueError("respostas devem ser um mapa id: valor")
    submit_answers(a.name, answers, load_bank())
    _, answered, total = progress(a.name, load_bank())
    print(f"respondidas: {answered}/{total}")
    return 0


def _assess_status(a) -> int:
    _print_progress(a.name)
    return 0


def _assess_finish(a) -> int:
    situations = _yaml(a.situations) if a.situations else []
    if not isinstance(situations, list):
        raise ValueError("situações devem ser uma lista de {pergunta, resposta}")
    result = finish(a.name, load_bank(), situations, date.today())
    for key in sorted(result.scores):
        print(f"{key}: {result.scores[key]}")
    print(f"confiabilidade: {result.confiabilidade}\nflags: {', '.join(result.flags)}")
    print(f"codigo_holland: {holland_code(result.scores)}")
    track = track_from_scores(result.scores)
    print(f"trilha: {track}")
    if track != "indefinido":  # a tie keeps what the interview recorded
        def set_track(p) -> None:
            p.behavior.track = track
        store.update_profile(a.name, set_track)
    return 0


def _report_save(a) -> int:
    """Copy a stage's mini report into the person's visible folder (and keep a copy in the profile)."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.stage):
        raise ValueError(f"nome de relatório inválido: {a.stage!r} (use letras minúsculas, números e hífen)")
    text = Path(a.file).read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("relatório vazio")
    out = store.reports_dir(a.name) / f"{a.stage}.md"
    store.atomic_write(out, text, private_dir=False)
    store.atomic_write(store.profile_dir(a.name) / "reports" / f"{a.stage}.md", text)
    print(f"relatorio: {out}")
    return 0


def _target_add(a) -> int:
    data = _yaml(a.file)
    if not isinstance(data, dict) or not data.get("role"):
        raise ValueError("alvo precisa de um mapa com 'role'")
    p = store.load_profile(a.name)
    required = data.get("required_skills") or []
    if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
        raise ValueError("required_skills deve ser uma lista de textos")
    if required:
        pct, _ = projected_match(p, required)
        group = classify_group(pct, p.stretch_policy)
        status = "pronto" if group == "agora" else "em_formacao"
    else:
        pct, group, status = None, "sem_dado", "sem_dado_mercado"
    record = {**data, "group": group, "status": status, "match_at_acceptance": pct,
              "accepted_at": date.today().isoformat()}
    store.append_record(a.name, "targets", record)
    print(f"group: {group}\nstatus: {status}\nmatch_at_acceptance: {pct}")
    return 0


def _course_add(a) -> int:
    data = _yaml(a.file)
    if not isinstance(data, dict):
        raise ValueError("curso deve ser um mapa")
    store.append_record(a.name, "courses_done", {"date": date.today().isoformat(), **data})
    return 0


def _project_match(a) -> int:
    p = store.load_profile(a.name)
    found = [t for t in p.targets if t.role.casefold() == a.role.casefold()]
    if not found:
        raise ValueError(f"profissão não está em targets: {a.role!r}")
    target = found[-1]
    if not target.required_skills:
        raise ValueError("profissão sem lista de skills; rode a análise de mercado ou informe a lista")
    pct, missing = projected_match(p, target.required_skills)
    released = cv_released(target, pct, p.stretch_policy)
    print(f"pct: {pct}\nlabel: {label(pct)}\nmissing: {', '.join(missing)}\ncv_liberado: {'sim' if released else 'nao'}")
    return 0


def _band(a) -> int:
    price = 0 if a.price == "gratis" else int(a.price)  # int() ValueError is reported by main
    print(f"faixa: {price_band(price, store.load_profile(a.name).cheap_course_max)}")
    return 0


def _market_claims(a) -> int:
    claims = market_claims(a.n_jobs, a.salary_median, a.applicants_median, store.load_profile(a.name))
    print("\n".join(f"{k}: {v}" for k, v in claims.items()))
    return 0


def _slug(text: str) -> str:
    try:
        return store.slugify(text)
    except ValueError:
        return "vaga"


def _type_files(name: str, role: str) -> tuple[Path, Path]:
    base = store.profile_dir(name) / "types" / _slug(role)
    return base.with_suffix(".yaml"), base.with_suffix(".pdf")


def _type_define(a) -> int:
    p = store.load_profile(a.name)
    data = _yaml(a.file)
    if not isinstance(data, dict):
        raise ValueError("tipo deve ser um mapa com 'role'")
    store.upsert_job_type(a.name, validate_new_type(p, data))
    rules = effective_rules(find_type(store.load_profile(a.name), data["role"]), p)
    print(f"piso: {rules.salary_floor}\nmodalidade: {', '.join(rules.modality)}\ncontrato: {rules.contract}")
    return 0


def _type_list(a) -> int:
    p = store.load_profile(a.name)
    live = {t.role.casefold() for t in releasable_targets(p)}
    for jt in p.job_types:
        r = effective_rules(jt, p)
        print(f"{jt.role} | piso: {r.salary_floor} | modalidade: {', '.join(r.modality)} | contrato: {r.contract}"
              f" | liberado: {'sim' if jt.role.casefold() in live else 'nao'}")
    defined = {jt.role.casefold() for jt in p.job_types}
    pending = [t.role for t in releasable_targets(p) if t.role.casefold() not in defined]
    print("sem_tipo_definido: " + ", ".join(pending))
    return 0


def _type_resume(a) -> int:
    p = store.load_profile(a.name)
    if find_type(p, a.role) is None:
        raise ValueError(f"defina o tipo antes (type-define): {a.role!r}")
    content = content_from_dict(_yaml(a.file))
    doc = build_resume(p, content, [], date.today())
    if warning := _lossy_warning(doc):
        print(f"aviso: {warning}", file=sys.stderr)
    yaml_path, pdf_path = _type_files(a.name, a.role)
    store.atomic_write(yaml_path, store.dump(asdict(content)))
    write_pdf(doc, pdf_path)
    print(f"pdf: {pdf_path}")
    return 0


def _lossy_warning(doc) -> str | None:
    lossy = lossy_chars(doc_text(doc))
    if not lossy:
        return None
    return 'caracteres fora do Latin-1 viraram "?" no PDF: ' + ", ".join(lossy)


def _yes(flag: bool) -> str:
    return "sim" if flag else "nao"


def _vaga_eval(a) -> int:
    p = store.load_profile(a.name)
    posting = posting_from_dict(_yaml(a.file))
    cls = classify(posting, p, a.type)
    ev = evaluate(posting, p, cls.role if cls.kind == "tipo" else None)
    print(f"classificacao: {cls.kind}\ntipo: {cls.role or '-'}\ncandidatos: {', '.join(cls.candidates or [])}\n"
          f"match: {ev.match}\nlabel: {ev.label}\nacao: {ev.action}\nfaltam: {', '.join(ev.missing)}\n"
          f"esticadas: {', '.join(ev.stretched)}\n"
          f"adjacentes: {', '.join(f'{r} ({o})' for r, o in ev.adjacent.items())}\narriscada: {_yes(ev.risky)}\nabaixo_do_piso: {_yes(ev.below_floor)}\n"
          f"restricoes: {'ok' if ev.constraints_ok else 'fora'}\nvaga_boa_sem_tipo: {_yes(ev.good_without_type)}")
    return 0


def resume_code(posting) -> str:
    """Short stable code for a posting. The file name carries this code, never the company or the job title."""
    seed = vaga_key(posting.url) or f"{posting.company}|{posting.title}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:5].upper()


def _unique_base(folder: Path, stem: str) -> Path:
    base, n = folder / stem, 1
    while base.with_suffix(".pdf").exists():
        n += 1
        base = folder / f"{stem}-{n}"
    return base


def _vaga_resume(a) -> int:
    if a.platform:
        _check_platform(a.platform)
    p = store.load_profile(a.name)
    posting = posting_from_dict(_yaml(a.file))
    cls = classify(posting, p, a.type)
    if cls.kind == "ambiguo":
        raise ValueError("mais de um tipo serve para a vaga: " + ", ".join(cls.candidates) + "; rode de novo com --type")
    type_role = cls.role if cls.kind == "tipo" else None
    ev = evaluate(posting, p, type_role)
    override = content_from_dict(_yaml(a.content_file)) if a.content_file else ResumeContent()
    if type_role:
        mode, (type_yaml, _) = "tipo", _type_files(a.name, type_role)
        if not type_yaml.exists():
            raise ValueError(f"gere o modelo do tipo antes (type-resume): {type_role!r}")
        content = merge_content(content_from_dict(store.read_yaml(type_yaml)), override)
    else:
        mode = "do_zero"
        if not ev.good_without_type:
            reasons = [f"match {ev.match}% abaixo de {GOOD_MATCH}%"] if ev.match < GOOD_MATCH else []
            reasons += [] if ev.constraints_ok else ["fora das suas restrições de modalidade ou contrato"]
            raise ValueError("vaga sem tipo fora do critério de vaga boa: " + ("; ".join(reasons) or "salário abaixo do menor piso"))
        if not a.content_file:
            raise ValueError("vaga sem tipo precisa de --content-file com o conteúdo completo do currículo")
        content = override
    doc = build_resume(p, content, ev.stretched, date.today(), missing=[*ev.missing, *ev.adjacent])  # raises before anything is written
    if warning := _lossy_warning(doc):
        print(f"aviso: {warning}", file=sys.stderr)
        ev.notes.append(warning)

    folder = store.profile_dir(a.name) / "resumes"
    base = folder / f"curriculo-{store.slugify(p.name)}-{resume_code(posting)}"  # same posting, same file: it is rewritten
    floor = effective_rules(find_type(p, type_role), p).salary_floor if type_role else None
    write_pdf(doc, base.with_suffix(".pdf"))
    store.atomic_write(base.with_name(base.name + ".review.txt"), review_sheet(posting, ev, type_role, mode, floor))
    key = vaga_key(posting.url)
    if key:  # regenerating a posting replaces its record instead of duplicating it
        store.update_profile(a.name, lambda prof: setattr(
            prof, "applications", [x for x in prof.applications if vaga_key(x.url) != key]))
    store.append_record(a.name, "applications", {
        "date": date.today().isoformat(), "url": posting.url, "company": posting.company, "title": posting.title,
        "type": type_role or "", "mode": mode, "match": ev.match, "label": ev.label, "risky": ev.risky,
        "below_floor": ev.below_floor, "file": str(base.with_suffix(".pdf").relative_to(store.profile_dir(a.name))),
        "platform": a.platform or "",
    })
    if a.platform:
        store.update_profile(a.name, lambda prof: mark_seen(prof, a.platform, posting, "preparada", date.today()))
    print(f"modo: {mode}\ntipo: {type_role or '-'}\nmatch: {ev.match}\nlabel: {ev.label}\narriscada: {_yes(ev.risky)}\n"
          f"abaixo_do_piso: {_yes(ev.below_floor)}\npdf: {base.with_suffix('.pdf')}\nrevisao: {base}.review.txt")
    return 0


def _applications(a) -> int:
    for r in store.load_profile(a.name).applications:
        print(f"{r.date} | {r.company} | {r.title} | {r.type or '-'} | {r.match} | {r.label} | {r.file}")
    return 0


def _check_platform(platform: str) -> None:
    if platform not in PLATFORMS:
        raise ValueError(f"plataforma inválida: {platform!r} (use {', '.join(PLATFORMS)})")


def _round_check(a) -> int:
    _check_platform(a.platform)
    p = store.load_profile(a.name)
    cap = capacity(p, a.platform, date.today())
    print(f"permitido: {cap.allowed}\nmotivo: {cap.reason}\nhoje: {cap.today}/{p.run.per_day}\n"
          f"pendentes: {cap.pending}\npausada: {_yes(cap.paused)}\nexaminar_ate: {p.run.max_examined}\n"
          f"fit_mode: {p.run.fit_mode}")
    return 0


def _vaga_check(a) -> int:
    _check_platform(a.platform)
    p = store.load_profile(a.name)
    posting = posting_from_dict(_yaml(a.file))
    print(f"repetida: {seen_reason(p, posting.url, posting.company, posting.title, a.platform) or 'nao'}\n"
          f"filtro: {filter_reason(posting, p) or 'nao'}")
    return 0


def _seen_add(a) -> int:
    _check_platform(a.platform)
    posting = posting_from_dict(_yaml(a.file))
    store.update_profile(a.name, lambda p: mark_seen(p, a.platform, posting, a.reason, date.today()))
    return 0


def _app_status(a) -> int:
    key = vaga_key(a.url)

    def change(p) -> None:
        found = [x for x in p.applications if key and vaga_key(x.url) == key]
        if not found:
            raise ValueError(f"candidatura não encontrada para a url: {a.url!r}")
        found[-1].status = a.status

    store.update_profile(a.name, change)
    return 0


def _set_pause(platform: str, paused: bool, reason: str):
    def change(p) -> None:
        state = next((s for s in p.platforms if s.platform == platform), None)
        if state is None:
            state = PlatformState(platform)
            p.platforms.append(state)
        state.paused, state.reason, state.since = paused, reason, date.today().isoformat() if paused else ""
    return change


def _platform_pause(a) -> int:
    _check_platform(a.platform)
    store.update_profile(a.name, _set_pause(a.platform, True, a.reason))
    return 0


def _platform_release(a) -> int:
    _check_platform(a.platform)
    store.update_profile(a.name, _set_pause(a.platform, False, ""))
    return 0


def _answers_resolve(a) -> int:
    questions = _yaml(a.file)
    if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
        raise ValueError("perguntas devem ser uma lista de textos")
    results = resolve(questions, store.load_profile(a.name))
    for r in results:
        print(f"{r.category} | {r.status} | {r.source} | {r.question} | {r.answer or ''}")
    blanks = [r.question for r in results if r.status == "em_branco"]
    if a.vaga and blanks:
        store.update_profile(a.name, lambda p: add_pending(p, blanks, a.vaga, date.today()))
    return 0


def _answers_add(a) -> int:
    data = _yaml(a.file)
    if not isinstance(data, list):
        raise ValueError("respostas devem ser uma lista de {question, answer, category, always}")
    entries = profile_from_dict({"answers": data}).answers

    def change(p) -> None:
        for e in entries:
            upsert_answer(p, e)

    store.update_profile(a.name, change)
    return 0


def _pending_list(a) -> int:
    for q in store.load_profile(a.name).pending:
        print(f"{q.category} | {q.question} | {q.vaga}")
    return 0


def _pending_clear(a) -> int:
    store.update_profile(a.name, lambda p: p.pending.clear())
    return 0


def _fit_risks(a) -> int:
    p = store.load_profile(a.name)
    flags = fit_risks(Path(a.file).read_text(encoding="utf-8"))
    print(f"flags: {', '.join(flags)}\nacao: {fit_action(p.run.fit_mode, flags)}")
    return 0


def _behavior(a) -> int:
    for key, value in behavior_summary(store.load_profile(a.name)).items():
        print(f"{key}: {value}")
    return 0


def _run_settings(a) -> int:
    changes = {k: v for k, v in (("per_round", a.per_round), ("per_day", a.per_day),
                                 ("max_examined", a.max_examined), ("fit_mode", a.fit_mode),
                                 ("autonomy", a.autonomy)) if v is not None}
    if changes:
        def change(p) -> None:
            for k, v in changes.items():
                setattr(p.run, k, v)
        store.update_profile(a.name, change)
    r = store.load_profile(a.name).run
    print(f"per_round: {r.per_round}\nper_day: {r.per_day}\nmax_examined: {r.max_examined}\nfit_mode: {r.fit_mode}\nautonomy: {r.autonomy}")
    return 0


def _next(a) -> int:
    j = journey(a.name)
    for n, stage in enumerate(j.stages, 1):
        print(f"{n}. {stage.title} | {stage.skill} | {'feito' if stage.done else 'pendente'}")
    print(f"proximo: {j.next_skill}")
    return 0


def _numbered(folder: Path, stem: str) -> Path:
    path, n = folder / f"{stem}.txt", 1
    while path.exists():
        n += 1
        path = folder / f"{stem}-{n}.txt"
    return path


def _form_new(a) -> int:
    if a.kind not in ("interview", "teste"):
        raise ValueError(f"tipo de formulário inválido: {a.kind!r} (use interview ou teste)")
    stem, text = ("questionario", interview_form()) if a.kind == "interview" else ("teste", assessment_form(load_bank()))
    path = _numbered(store.forms_dir(), f"{stem}-{store.slugify(a.name)}")
    store.atomic_write(path, text, private_dir=False)  # a shared visible folder: only the file is made private
    print(f"arquivo: {path}")
    return 0


def _find_form(name: str) -> Path:
    """The newest form of this person: the visible folder first, the old hidden location as a fallback."""
    slug = store.slugify(name)
    kinds = r"(?:questionario|teste|seguimento)"
    visible = [p for p in store.forms_dir().glob("*.txt") if re.fullmatch(rf"{kinds}-{re.escape(slug)}(?:-\d+)?\.txt", p.name)]
    hidden = [p for p in store.profile_dir(name).glob("*.txt") if re.fullmatch(rf"{kinds}(?:-\d+)?\.txt", p.name)]

    def has_marker(p: Path) -> bool:
        first = next((l.strip() for l in p.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()), "")
        return first.startswith("# JOBBOT:")

    found = sorted((p for p in [*visible, *hidden] if has_marker(p)), key=lambda p: p.stat().st_mtime)
    if not found:
        raise ValueError(f"nenhum formulário de {name!r} encontrado em {store.forms_dir()}")
    return found[-1]


def _archive(name: str, path: Path) -> None:
    """Move a loaded form out of the shared Downloads folder into the person's private folder."""
    if path.parent.resolve() != store.forms_dir().resolve():
        return
    folder = store.profile_dir(name) / "forms"
    folder.mkdir(parents=True, exist_ok=True)
    os.chmod(folder, 0o700)
    dest, n = folder / path.name, 1
    while dest.exists():
        n += 1
        dest = folder / f"{path.stem}-{n}{path.suffix}"
    shutil.move(str(path), str(dest))
    os.chmod(dest, 0o600)
    print(f"recolhido: {dest}")


def _form_load(a) -> int:
    path = Path(a.file) if a.file else _find_form(a.name)
    if not a.file:
        print(f"lendo: {path}")
    text = path.read_text(encoding="utf-8")
    marker = next((l.strip() for l in text.splitlines() if l.strip()), "")
    if marker == INTERVIEW_MARKER:
        steps, errors = parse_interview(text)
        if errors:
            raise ValueError("\n".join(errors))
        from jobbot.store import STEPS
        for step in STEPS:
            if step in steps:
                store.put_step(a.name, step, steps[step])
                print(f"salvo: {step}")
            else:
                print(f"nao_preenchida: {step}")
        problems = validate(store.load_profile(a.name))
        print("\n".join(f"aviso: {p}" for p in problems))
        print(f"proxima_etapa: {store.next_step(a.name) or 'completo'}")
        _archive(a.name, path)
    elif marker == TEST_MARKER:
        bank = load_bank()
        answers, situations, errors = parse_assessment(text, bank)
        if errors:
            raise ValueError("\n".join(errors))
        if answers:
            submit_answers(a.name, answers, bank)
        if situations:
            store.atomic_write(store.profile_dir(a.name) / "situations.yaml",
                               yaml.safe_dump(situations, allow_unicode=True, sort_keys=False))
        layer, answered, total = progress(a.name, bank)
        print(f"respondidas: {answered}/{total}")
        print("proximo: assess-finish" if layer is None else f"proxima_camada: {layer}")
        if layer is None:  # a half-filled test stays where the person is still working on it
            _archive(a.name, path)
    elif marker == FOLLOWUP_MARKER:
        items, errors = parse_followup(text)
        if errors:
            raise ValueError("\n".join(errors))

        def change(p) -> None:
            problems = apply_followup(p, items)
            if problems:
                raise ValueError("\n".join(problems))

        store.update_profile(a.name, change)
        print(f"aplicadas: {len(items)}")
        _archive(a.name, path)
    else:
        raise ValueError("arquivo sem marcador JOBBOT (esperado # JOBBOT:interview, # JOBBOT:teste ou # JOBBOT:followup)")
    return 0


def _form_gaps(a) -> int:
    text = followup_form(store.load_profile(a.name))
    if text is None:
        print("sem lacunas")
        return 0
    path = _numbered(store.forms_dir(), f"seguimento-{store.slugify(a.name)}")
    store.atomic_write(path, text, private_dir=False)
    print(f"arquivo: {path}")
    return 0


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="jobbot")
    sub = ap.add_subparsers(dest="cmd", required=True)
    def add(name, fn, *args, **opts):
        sp = sub.add_parser(name)
        sp.add_argument("name")
        for a in args:
            if a.endswith("?"):
                sp.add_argument(a[:-1], nargs="?")
            else:
                sp.add_argument(a)
        for flag in opts.get("flags", []):
            sp.add_argument(flag, required=True)
        for flag, kind in opts.get("optional", {}).items():
            sp.add_argument(flag, type=kind)
        for flag, kind in opts.get("required_typed", {}).items():
            sp.add_argument(flag, type=kind, required=True)
        if opts.get("many"):
            sp.add_argument("files", nargs="+")
        sp.set_defaults(fn=fn)
    add("status", _status)
    add("path", _path)
    add("put", _put, "step", "file")
    add("validate", _validate)
    add("match", _match, flags=["--required"])
    add("market", _market, many=True)
    add("cv", _cv, flags=["--summary-file"])
    add("check", _check, "file")
    add("assess-answer", _assess_answer, "file")
    add("assess-status", _assess_status)
    add("assess-finish", _assess_finish, optional={"--situations": str})
    add("report-save", _report_save, "stage", "file")
    add("target-add", _target_add, "file")
    add("course-add", _course_add, "file")
    add("project-match", _project_match, "role")
    add("band", _band, "price")
    add("type-define", _type_define, "file")
    add("type-list", _type_list)
    add("type-resume", _type_resume, "role", "file")
    add("vaga-eval", _vaga_eval, "file", optional={"--type": str})
    add("vaga-resume", _vaga_resume, "file", optional={"--type": str, "--content-file": str, "--platform": str})
    add("applications", _applications)
    add("next", _next)
    add("form-new", _form_new, "kind")
    add("form-load", _form_load, "file?")
    add("form-gaps", _form_gaps)
    add("round-check", _round_check, "platform")
    add("vaga-check", _vaga_check, "file", flags=["--platform"])
    add("seen-add", _seen_add, "platform", "file", flags=["--reason"])
    add("app-status", _app_status, "url", "status")
    add("platform-pause", _platform_pause, "platform", flags=["--reason"])
    add("platform-release", _platform_release, "platform")
    add("answers-resolve", _answers_resolve, "file", optional={"--vaga": str})
    add("answers-add", _answers_add, "file")
    add("pending-list", _pending_list)
    add("pending-clear", _pending_clear)
    add("fit-risks", _fit_risks, "file")
    add("behavior", _behavior)
    add("run-settings", _run_settings, optional={"--per-round": int, "--per-day": int,
                                                 "--max-examined": int, "--fit-mode": str,
                                                 "--autonomy": str})
    add("market-claims", _market_claims, required_typed={"--n-jobs": int},
        optional={"--salary-median": int, "--applicants-median": int})
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return args.fn(args)
    except (ValueError, KeyError, TypeError, OSError, yaml.YAMLError,
            store.ProfileError, HonestyError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
