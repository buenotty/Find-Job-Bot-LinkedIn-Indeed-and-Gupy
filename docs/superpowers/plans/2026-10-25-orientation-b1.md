# Jobs Master BR v1 — B1 Orientation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add career orientation to the plugin: a layered assessment with self-relative percentages, profession suggestions in two groups with cost, honest three-path advice, accepted `targets`, and a course trail with a projected match.

**Architecture:** Same shape as project A. Deterministic logic (item bank, scoring, consistency, projection, price bands, market-claim rules) in the Python package `jobbot`, exposed by CLI commands. Three new skills (assessment, orientation, courses) drive the conversation and call the CLI. New profile fields are optional, so profiles written by A stay valid.

**Tech Stack:** Python >= 3.10, PyYAML, pytest, Claude Code skills (Markdown). Reuses `store`, `schema`, `match`, `market`, `honesty`.

**Spec:** `docs/superpowers/specs/2026-10-25-orientacao-b1-design.md` (builds on `docs/superpowers/specs/2026-10-25-mapeamento-design.md`)

## Global Constraints

- Product language PT-BR; market Brazil. Code, tests, commit messages in English; user-facing strings and skill bodies in PT-BR.
- Personal data 100% local, stored with owner-only permissions (dir 0700, files 0600), as in A. Assessment results are sensitive.
- Test items: original wording or public domain (IPIP). No proprietary inventory items. Source and license of every item group documented in the repo.
- Percentages are self-relative (share of the maximum possible score per dimension), never a percentile. The bot never writes "você está entre os X% mais".
- Never present results as clinical diagnosis; never promise "100% pronto" or any selection result.
- Course prices and availability come from a search at run time and carry the query date. Never invent price, duration or existence of a course.
- Market claims: with fewer than 30 jobs read, write "indício, amostra de N vagas", never "saturado" or "paga pouco".
- "Disponível agora" = match >= `stretch_policy.risky_below` (default 50). Below it, always `nova_formacao`. The CV-release cutoff for a `nova_formacao` target is `stretch_policy.stretch_from` (default 90). No new cutoff field.
- Course price bands: gratuito = R$ 0; barato <= `cheap_course_max` (default 200); caro above it.
- A finished course never changes `profile.skills` by itself. It is recorded in `courses_done`; a skill is added (level `iniciante`) only on the person's confirmation plus evidence, a certification only if the person gives name and issuer.
- Git: branch `feat/orientation-b1`, cut from `feat/profile-mapping` (A is not merged). Never on `main`. Conventional Commits in English, subject <= 72 chars, explicit paths in `git add`, no `Co-Authored-By`, no push.
- Repo is public: no real person's data, no owner name, no copied third-party text.

## Review Focus

1. Straight-lining (every answer the same) or contradictory repeated items: result is produced but marked `confiabilidade: baixa` with flags (Task 2).
2. Test interrupted mid-layer and resumed; answers out of range (0, 6, "abc") or unknown ids: the whole submission is rejected and nothing is saved (Task 2, Task 5).
3. Retake after a first assessment: history keeps both dated entries and the latest wins; a profile written by A with no assessment fields loads and validates (Tasks 1, 2).
4. Market-claim boundary: 29 vs 30 jobs; no `salary_expectation` in the profile means "paga pouco" is never claimed (Task 4).
5. Projection edge cases: `skills_claimed` not in `required_skills`, empty `required_skills`, duplicate course entries, result never above 100 and never `ValueError` leaking to the person (Task 4).

---

### Task 1: Schema and storage extension

**Files:**
- Modify: `jobbot/schema.py`, `jobbot/store.py`
- Test: `tests/test_schema.py`, `tests/test_store.py`

**Interfaces:**
- Consumes: A's dataclasses, `profile_from_dict`, `STEP_FIELDS`, `put_step`, `_atomic_write`, `_read_yaml`, `_dump`.
- Produces in `schema.py` (all fields defaulted):
  - `Assessment(date: str, scores: dict[str, int], confiabilidade: str, flags: list[str], situations: list[dict[str, str]])` with `confiabilidade` in `("alta", "baixa", "")`; situation items are `{"pergunta": ..., "resposta": ...}`
  - `Target(role: str, group: str, source: str, required_skills: list[str], match_at_acceptance: int | None, accepted_at: str, status: str)` with `group` in `("agora", "nova_formacao", "sem_dado")`, `source` in `("sugerida", "propria")`, `status` in `("pronto", "em_formacao", "sem_dado_mercado")`
  - `CourseDone(course: str, provider: str, date: str, skills_claimed: list[str], evidence: str)`
  - `Profile` gains `assessments: list[Assessment]`, `targets: list[Target]`, `courses_done: list[CourseDone]`, `cheap_course_max: int = 200`
  - `validate` flags invalid `group`, `source`, `status`, `confiabilidade`, and `cheap_course_max < 0`
- Produces in `store.py`:
  - `append_record(name: str, field: str, record: dict) -> None` for `field` in `("assessments", "targets", "courses_done")`: loads the profile, appends the built record, saves atomically; unknown field raises `ValueError`; a corrupt file raises `ProfileError` and writes nothing
  - `STEP_FIELDS` is NOT extended: B1 data is written only through `append_record`, so A's `STEPS` and `next_step` behavior do not change.

- [ ] **Step 1: Write failing tests.**
  - `test_schema.py`: `test_a_profile_without_b1_fields_loads_and_validates` (dict with only A fields -> `assessments == []`, `validate == []`); `test_b1_roundtrip` (full profile with one of each B1 record survives `profile_from_dict(profile_to_dict(p)) == p`); `test_validate_flags_bad_group` (`Target(group="x")` -> error containing "grupo"); `test_nested_unknown_key_in_target_raises` (`{"targets":[{"cargo":"x"}]}` -> `ValueError` matching "cargo").
  - `test_store.py`: `test_append_record_keeps_history` (two `append_record(..., "assessments", ...)` calls -> `len(load_profile().assessments) == 2`, order preserved); `test_append_record_unknown_field_raises`; `test_append_record_on_corrupt_file_writes_nothing` (file bytes unchanged, `ProfileError`); `test_append_record_does_not_touch_interview_state` (`next_step` unchanged).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_schema.py tests/test_store.py -q` -> FAIL.
- [ ] **Step 3: Implement** the dataclasses (reuse A's `_build`/`_records` pattern so unknown keys and wrong shapes raise) and `append_record` (build the record with the same `_build`, validate by round-tripping through `profile_from_dict` before saving).
- [ ] **Step 4: Run** the same command, then `.venv/bin/pytest -q` -> all PASS.
- [ ] **Step 5: Commit.** On branch `feat/orientation-b1` (create it first with `git checkout -b feat/orientation-b1`): `git add jobbot/schema.py jobbot/store.py tests/test_schema.py tests/test_store.py` -> `git commit -m "feat(schema): add assessment, targets and courses_done records"`.

### Task 2: Assessment engine

**Files:**
- Create: `jobbot/assessment.py`
- Test: `tests/test_assessment.py`

**Interfaces:**
- Consumes: `store.profile_dir`, `store._atomic_write`, `store._read_yaml`, `store._dump` (make these three public as `atomic_write`, `read_yaml`, `dump` in `store.py` in this task, keeping A's call sites working).
- Produces:
  - `LAYERS = ("valores", "interesses", "personalidade")`
  - `Item(id: str, layer: str, dimension: str, text: str, reverse: bool = False, twin: str | None = None)` (`twin` = id of the repeated item this one is checked against)
  - `load_bank(path: Path | None = None) -> list[Item]` (default: packaged `jobbot/data/items.yaml`; raises `ValueError` on duplicate ids, unknown layer, or a `twin` that does not exist)
  - `dimension_key(item: Item) -> str` -> `"<layer>.<dimension>"`
  - `submit_answers(name: str, answers: dict[str, int], bank: list[Item]) -> None`: all-or-nothing; every id must exist and every value be an int 1..5, else `ValueError` naming the offending ids and nothing is written. Merges into `test_state.yaml` in the profile dir. Later answers overwrite earlier ones.
  - `progress(name: str, bank: list[Item]) -> tuple[str | None, int, int]` -> (next layer with unanswered items or `None`, answered, total)
  - `score(answers: dict[str, int], bank: list[Item]) -> dict[str, int]`: per dimension key, reverse items use `6 - x`; result is `round(100 * (sum - n) / (4 * n))` where `n` is the item count of the dimension.
  - `consistency(answers: dict[str, int], bank: list[Item]) -> tuple[str, list[str]]` -> (`"alta"` or `"baixa"`, flags). Flags: `respostas_uniformes` when one value covers >= 90% of answers; `pares_incoerentes` when at least a third of the twin pairs differ by >= 3 after reverse-adjusting.
  - `finish(name: str, bank: list[Item], situations: list[dict[str, str]], today: date) -> Assessment`: requires every item answered (`ValueError` with the missing count otherwise); builds the `Assessment`, appends it via `append_record`, deletes `test_state.yaml`.
- Test double: tests build a small in-memory bank (2 layers, 3 dimensions, one reverse item, one twin pair); they do not depend on the real bank.

- [ ] **Step 1: Write failing tests:** `test_score_is_percent_of_max` (all 5s -> 100, all 1s -> 0, all 3s -> 50); `test_reverse_item_flips` (reverse item answered 5 lowers the dimension); `test_score_does_not_depend_on_any_population_input` (`score` takes only answers and bank); `test_submit_rejects_out_of_range_all_or_nothing` (answers `{"a1": 3, "a2": 6}` -> `ValueError`, `progress` still shows 0 answered); `test_submit_rejects_unknown_id`; `test_submit_rejects_non_int` ("abc" and `True`); `test_resume_progress_by_layer` (answer first layer fully -> `progress` returns the second layer); `test_straight_lining_flagged` (all 3s -> `("baixa", ["respostas_uniformes"])`); `test_incoherent_twins_flagged`; `test_coherent_answers_are_alta`; `test_finish_requires_all_answers`; `test_finish_appends_and_clears_state` (profile has one assessment, `test_state.yaml` gone); `test_retake_keeps_history_latest_wins` (two `finish` calls, two entries, last one has the later date); `test_bank_loader_rejects_bad_twin_and_duplicate_ids`.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_assessment.py -q` -> FAIL.
- [ ] **Step 3: Implement** `jobbot/assessment.py` and the `store.py` renames. State file: `test_state.yaml` with `{"answers": {id: int}}`.
- [ ] **Step 4: Run** `.venv/bin/pytest -q` -> all PASS (A's tests still green after the rename).
- [ ] **Step 5: Commit.** `git add jobbot/assessment.py jobbot/store.py tests/test_assessment.py` -> `git commit -m "feat(assessment): add scoring, consistency checks and resumable test"`.

### Task 3: Item bank

**Files:**
- Create: `jobbot/data/items.yaml`, `references/assessment-sources.md`
- Modify: `pyproject.toml` (package data `jobbot/data/*.yaml`)
- Test: `tests/test_bank.py`

**Interfaces:**
- Consumes: `load_bank`, `Item`, `dimension_key` (Task 2).
- Produces: the real bank, PT-BR, five-point agreement scale ("discordo totalmente" to "concordo totalmente"; for values, "nada importante" to "extremamente importante"). Required contents:
  - **valores** (8 dimensions, 3 items each): salario, estabilidade_emprego, autonomia, proposito, crescimento, equilibrio, reconhecimento, colaboracao. Original wording.
  - **interesses** (6 dimensions, 8 items each): pratico, investigativo, artistico, social, empreendedor, convencional. Original wording about activities the person would like to do.
  - **personalidade** (5 dimensions, 10 items each, mixed keying): abertura, conscienciosidade, extroversao, amabilidade, estabilidade. Items adapted to PT-BR from the public-domain IPIP; `assessment-sources.md` names the IPIP source and its public-domain status for these items and states that interest and value items are original.
  - At least 10 twin pairs spread across layers (a reworded or negated repeat of an earlier item, with `twin` set on the repeat).
  - Situational questions are not in the bank; they live in the orientation skill (Task 6).

- [ ] **Step 1: Write failing tests** in `tests/test_bank.py`: `test_bank_loads`; `test_counts_per_dimension` (valores 3, interesses 8, personalidade 10 per dimension, 19 dimensions in total); `test_every_personality_dimension_has_reverse_items`; `test_at_least_ten_twin_pairs`; `test_ids_unique_and_texts_unique`; `test_total_items_fit_time_budget` (total <= 150, since ~8 s per item plus situations stays within 30 minutes); `test_sources_doc_mentions_ipip_and_originals`; `test_no_item_text_matches_known_proprietary_stems` (assert no item text contains the strings `"MBTI"`, `"Myers"`, `"16PF"`).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_bank.py -q` -> FAIL.
- [ ] **Step 3: Write the bank and the sources doc.** Content is the implementer's writing; the tests fix its shape.
- [ ] **Step 4: Run** `.venv/bin/pytest -q` -> all PASS. Also run `JOBBOT_EBOOK_TXT=<path> .venv/bin/pytest tests/test_skills.py -q` if the extracted text is available.
- [ ] **Step 5: Commit.** `git add jobbot/data/items.yaml references/assessment-sources.md pyproject.toml tests/test_bank.py` -> `git commit -m "feat(assessment): add PT-BR item bank with sources and licenses"`.

### Task 4: Orientation rules

**Files:**
- Create: `jobbot/orientation.py`
- Test: `tests/test_orientation.py`

**Interfaces:**
- Consumes: `Profile`, `Target`, `CourseDone`, `StretchPolicy`, `match.coverage`, `match.label`, `match.normalize`.
- Produces:
  - `MIN_SAMPLE = 30`, `SATURATED_APPLICANTS = 200` (owner's call: 100 applicants per job is common, "saturado" starts at 200)
  - `classify_group(pct: int, policy: StretchPolicy) -> str` -> `"agora"` when `pct >= policy.risky_below`, else `"nova_formacao"`
  - `cv_released(target: Target, current_pct: int | None, policy: StretchPolicy) -> bool`: `agora` -> True; `nova_formacao` -> True only if `current_pct is not None and current_pct >= policy.stretch_from`; `sem_dado` -> False
  - `price_band(price: int | None, cheap_max: int) -> str` -> `"gratuito"` (0), `"barato"` (<= cheap_max), `"caro"`, `"sem_preco"` (None)
  - `projected_match(p: Profile, required: list[str]) -> tuple[int, list[str]]`: skills = `p.skills` names plus every `skills_claimed` of `p.courses_done` that is in `required` (normalized); delegates to `coverage`; empty `required` returns `(0, [])` instead of raising; result is clamped to 0..100 and counts each required skill once.
  - `market_claims(n_jobs: int, salary_median: int | None, applicants_median: int | None, p: Profile) -> dict[str, str]` with keys `saturado` and `paga_pouco`, values `"sim"`, `"nao"`, `"indicio"`, `"sem_dado"`: `n_jobs < MIN_SAMPLE` -> `"indicio"` for any key that has data; `saturado` is `"sim"` when `applicants_median >= SATURATED_APPLICANTS`; `paga_pouco` is `"sim"` when `salary_median < p.screening.salary_expectation`, and `"sem_dado"` when either value is missing or the person has no `salary_expectation`.

- [ ] **Step 1: Write failing tests:** `test_group_boundary_49_50` (49 -> nova_formacao, 50 -> agora; custom policy shifts it); `test_cv_released_rules` (agora True; nova_formacao at 89 False, at 90 True; sem_dado False; nova_formacao with `current_pct=None` False); `test_price_band` (0, 200, 201, None, custom `cheap_max`); `test_projection_counts_only_claimed_required` (claimed skill outside `required` changes nothing); `test_projection_is_not_inflated_by_duplicates` (same course twice, same result as once); `test_projection_empty_required_returns_zero_without_error`; `test_projection_never_exceeds_100`; `test_projection_does_not_mutate_profile_skills`; `test_claims_29_vs_30_jobs` (29 -> `indicio`, 30 -> definitive); `test_claims_without_salary_expectation_never_say_paga_pouco`; `test_claims_saturated_threshold` (199 -> nao, 200 -> sim at n=30).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_orientation.py -q` -> FAIL.
- [ ] **Step 3: Implement** `jobbot/orientation.py`.
- [ ] **Step 4: Run** `.venv/bin/pytest -q` -> PASS.
- [ ] **Step 5: Commit.** `git add jobbot/orientation.py tests/test_orientation.py` -> `git commit -m "feat(orientation): add group, projection, price band and claim rules"`.

### Task 5: CLI commands

**Files:**
- Modify: `jobbot/cli.py`
- Test: `tests/test_cli_b1.py`

**Interfaces:**
- Consumes: Tasks 1-4. Errors follow A: `erro: <msg>` on stderr, exit 1, no traceback.
- Produces commands (output is `key: value` lines unless stated):
  - `assess-answer <name> <answers.yaml>` -> `submit_answers`; prints `respondidas: N/M`
  - `assess-status <name>` -> `proxima_camada: <layer>` or `completo`, plus `respondidas: N/M`
  - `assess-finish <name> [--situations <file.yaml>]` -> `finish`; prints one `<layer>.<dimension>: <pct>` line per dimension, then `confiabilidade: alta|baixa` and `flags: ...`
  - `target-add <name> <target.yaml>`: file has `role`, `source`, optional `required_skills`. The CLI fills `group`, `match_at_acceptance`, `accepted_at` (today) and `status`: with `required_skills` -> `projected_match` -> `classify_group`, status `pronto` for `agora`, `em_formacao` for `nova_formacao`; without them -> group `sem_dado`, status `sem_dado_mercado`, `match_at_acceptance` null. Appends via `append_record`.
  - `course-add <name> <course.yaml>` -> appends a `CourseDone`
  - `project-match <name> <role>` -> reads the target by role (`ValueError` "profissão não está em targets" otherwise); prints `pct`, `label`, `missing`, `cv_liberado: sim|nao`
  - `band <name> <price|gratis>` -> prints `faixa: gratuito|barato|caro`
  - `market-claims <name> --n-jobs N [--salary-median S] [--applicants-median A]` -> prints `saturado: ...` and `paga_pouco: ...`

- [ ] **Step 1: Write failing tests** with the subprocess helper from `tests/test_cli.py`: `test_assess_flow_end_to_end` (answer every item of the real bank in two submissions, status goes `valores` -> ... -> `completo`, `assess-finish` prints 19 dimension lines); `test_assess_answer_rejects_out_of_range_and_saves_nothing` (`assess-status` still shows 0 answered); `test_assess_finish_before_complete_exits_1`; `test_straight_lining_prints_baixa`; `test_target_add_with_skills_sets_group_and_status`; `test_target_add_without_skills_is_sem_dado`; `test_project_match_unknown_role_exits_1`; `test_course_add_then_project_match_rises` (claimed skill raises the pct; `profile.skills` unchanged); `test_band_gratis_and_price`; `test_market_claims_boundary`; `test_corrupt_profile_is_clean_error`.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_cli_b1.py -q` -> FAIL.
- [ ] **Step 3: Implement** the commands in `jobbot/cli.py`, one function per command.
- [ ] **Step 4: Run** `.venv/bin/pytest -q` -> PASS.
- [ ] **Step 5: Commit.** `git add jobbot/cli.py tests/test_cli_b1.py` -> `git commit -m "feat(cli): add assessment, targets and courses commands"`.

### Task 6: Skills and references

**Files:**
- Create: `skills/jobbot-assessment/SKILL.md`, `skills/jobbot-orientation/SKILL.md`, `skills/jobbot-courses/SKILL.md`, `references/honest-career-talk.md`
- Modify: `tests/test_skills.py` (expected skill set)
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: CLI commands from Task 5 and A's `jobbot-market` output (`focus-report.md`, `jobs-<cargo>.json`).
- Each skill: frontmatter `name` equal to folder, PT-BR `description` with trigger phrases; works without `linkedin-skills`.

Content each skill must carry:
- **jobbot-assessment:** prerequisite `status` is `completo` and `validate` is `ok`; explains length (20 to 30 minutes), that it can stop and resume (`assess-status`), shows the items layer by layer in blocks of 10 to 15, writes each block to a temp YAML and submits with `assess-answer`; never fills an answer for the person; collects 6 situational questions with real examples ("conte uma vez em que...") and writes them to a `situations.yaml`; runs `assess-finish`; presents the percentages in direct language with the caveat "pontuação relativa ao máximo possível, não ranking contra outras pessoas, não é diagnóstico"; reports `confiabilidade: baixa` honestly and offers to redo the flagged layer; points out contradictions between the results and the profile history.
- **jobbot-orientation:** reads the profile, the latest assessment and `focus-report.md`; proposes 8 to 15 professions in two groups; reads market data (30 to 50 public ads each, same rules as A) only for a shortlist of about 5 and marks the rest "sem dado de mercado", offering deeper reads on request; uses `market-claims` for every "saturado"/"paga pouco" statement; shows cost per profession (salary median, competition, and for `nova_formacao` the cost and time to get there); when love and money diverge, presents the three paths of `references/honest-career-talk.md`; the person accepts or adds professions; saves each with `target-add`.
- **jobbot-courses:** for each target with `required_skills`, lists the missing skills (`project-match`), searches public pages for courses that cover them, records the query date ("data da consulta"), classifies each price with `band`, never invents price or existence, and shows free, cheap and expensive separately; after the person reports a finished course, proposes skills from the syllabus, records only the ones the person confirms via `course-add`, then re-runs `project-match`; adds a skill to `profile.skills` only on confirmation plus evidence; says clearly that a course does not guarantee selection.
- **references/honest-career-talk.md:** rules for the three paths (love with its real cost, money with why the person fits, hybrid), tone (direct, no flattery, no pushing toward money), and the evidence rule (every claim from data, with sample size).

- [ ] **Step 1: Write failing tests** in `tests/test_skills.py`: update the expected set to include the three new skills; `test_assessment_skill_has_caveat` (contains "não é diagnóstico"); `test_courses_skill_mentions_query_date` (contains "data da consulta"); `test_orientation_skill_uses_market_claims` (contains `market-claims`); existing referenced-file and owner-data tests keep passing.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_skills.py -q` -> FAIL.
- [ ] **Step 3: Write the three skills and the reference.**
- [ ] **Step 4: Run** `.venv/bin/pytest -q` -> PASS.
- [ ] **Step 5: Commit.** `git add skills references/honest-career-talk.md tests/test_skills.py` -> `git commit -m "feat(skills): add assessment, orientation and courses skills"`.

### Task 7: End-to-end and README

**Files:**
- Create: `tests/fixtures/maria/answers-valores.yaml`, `answers-interesses.yaml`, `answers-personalidade.yaml`, `situations.yaml`, `target-analista.yaml`, `target-hardware.yaml`, `course-sql.yaml`; `tests/test_e2e_b1.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: the CLI and the A fixtures for the fictional "Maria Exemplo".

- [ ] **Step 1: Write the test** `test_orientation_flow`: with A's seven steps already put, run `assess-answer` for the three layers, `assess-finish` (expect 19 dimension lines and `confiabilidade: alta`), `target-add` for a target with skills (expect `agora`) and for one without (expect `sem_dado`), a `nova_formacao` target below 50 (expect `em_formacao`, `cv_liberado: nao`), `course-add` for a course whose `skills_claimed` raises the projection, `project-match` shows the higher pct, and `validate` still exits 0. Also assert the profile file mode is 0600.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_e2e_b1.py -q` -> FAIL until fixtures exist, then PASS. Then `.venv/bin/pytest -q` -> all PASS.
- [ ] **Step 3: Update `README.md`:** B1 section (three skills, test length, honesty rules, price bands, sources doc link).
- [ ] **Step 4: Live check.** `claude plugin validate .` passes. In a headless session with `--plugin-dir` and a throwaway `JOBBOT_HOME`, invoke `jobbot-assessment` for its start only: expected, it states the length and the caveat, runs `assess-status`, writes nothing into the repo.
- [ ] **Step 5: Commit.** `git add tests/fixtures tests/test_e2e_b1.py README.md` -> `git commit -m "test(e2e): cover orientation flow and document B1 in README"`.
