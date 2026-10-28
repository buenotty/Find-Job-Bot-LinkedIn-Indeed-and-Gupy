# JobBot A — Profile Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build project A of JobBot: a public Claude Code plugin that interviews a person, analyzes the job market, recommends a focus, and generates the profile, LinkedIn texts and a base CV.

**Architecture:** Deterministic logic (profile schema and storage, match scoring, honesty check, CV rendering, market aggregation) lives in a small Python package `jobbot` with a CLI. Three Claude Code skills (interview, market, outputs) drive the conversation and call that CLI. Each person's data lives in `$JOBBOT_HOME/profiles/<slug>/` (default `~/.jobbot`), outside the repo.

**Tech Stack:** Python >= 3.10, PyYAML, pytest, Claude Code skills (Markdown), `gh` CLI for the GitHub review.

**Spec:** `docs/superpowers/specs/2026-10-25-mapeamento-design.md`

## Global Constraints

- Product language is PT-BR; v1 market is Brazil. Code, tests, commit messages in English; user-facing strings and skill bodies in PT-BR.
- Personal data stays 100% local. No upload to any service. Only public job pages are read for market analysis.
- The repo is public: no data of the owner and no text, template or example copied from the ebook "Guia Prático LinkedIn 10k". Principles are rewritten in original words.
- The bot may stretch skills. It never invents employers, roles, dates, education, certifications or result numbers. A result number appears only if the person reported it.
- Match labels, verbatim: below 50 `Arriscado`; 50-69 `Chance média`; 70-79 `Bom match`; 80-99 `Ótimo match`; 100 `Vaga perfeita`.
- Stretch policy defaults, configurable per person: `stretch_from: 90`, `risky_below: 50`. At >= 90 stretch silently; 50-89 stretch with visible marks (bot's call, approved with the spec); below 50 open as "arriscada", never discard. A only stores the policy; B and C apply it.
- Mandatory notice shown at interview start, verbatim: "Automação em LinkedIn, Indeed e Gupy viola os termos dessas plataformas. O risco para a conta é de cada pessoa."
- A does not edit LinkedIn or GitHub. It generates text and suggestions only.
- Git: work on branch `feat/profile-mapping`, never on `main`. Conventional Commits, English, subject <= 72 chars. Stage explicit paths. No `Co-Authored-By` or generated-by lines. No push.

## Review Focus

1. Skill names with case, accents, extra spaces ("Power  BI", "analise de dados" vs "Análise de Dados") must match (Task 2).
2. Person with no work experience (student, first job): validation passes and the CV renders from projects, courses and certifications instead of crashing or showing an empty CV (Tasks 2 and 4).
3. Interview interrupted mid-way, then resumed; or `profile.yaml` hand-edited into invalid YAML: resume continues at the right step and a corrupt file raises a clear error naming the path, never silently overwriting data (Task 3).
4. Two people on one machine, or a name like `../../etc` or `José da Silva`: profiles stay isolated and paths cannot escape `$JOBBOT_HOME/profiles` (Task 3).
5. Market analysis with zero jobs, jobs without salary, or all `applicants` missing: no division by zero, medians are `None`, the report still renders (Task 5).

---

### Task 1: Repo bootstrap

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.claude-plugin/plugin.json`, `jobbot/__init__.py`, `tests/__init__.py`, `tests/conftest.py`
- Existing: `docs/superpowers/specs/2026-10-25-mapeamento-design.md`, this plan

**Interfaces:**
- Produces: `tests/conftest.py` fixture `tmp_home(tmp_path, monkeypatch) -> Path` that sets `JOBBOT_HOME` to a temp dir and returns it.

- [ ] **Step 1: Init repo and branch.** In `<pasta-do-projeto>`: `git init`, then `git checkout -b feat/profile-mapping` before any commit. Verify with `git branch --show-current` -> `feat/profile-mapping`.
- [ ] **Step 2: Scaffold.** `pyproject.toml` (project `jobbot`, `requires-python >=3.10`, dependency `pyyaml`, dev dependency `pytest`, `[tool.pytest.ini_options] testpaths=["tests"]`). `.gitignore` lists `.venv/`, `__pycache__/`, `profile/`, `profiles/`, `.jobbot/`. `plugin.json` has `name: "jobbot"`, PT-BR description, `version: "0.1.0"`, `skills: "./skills"`.
- [ ] **Step 3: Venv.** `python3 -m venv .venv && .venv/bin/pip install -e . pytest`. Run `.venv/bin/pytest` -> `no tests ran`, exit 5 is expected.
- [ ] **Step 4: Commit.** `git add pyproject.toml .gitignore .claude-plugin/plugin.json jobbot/__init__.py tests/__init__.py tests/conftest.py docs/` then `git commit -m "chore: bootstrap jobbot plugin repo"`.

### Task 2: Schema and match scoring

**Files:**
- Create: `jobbot/schema.py`, `jobbot/match.py`
- Test: `tests/test_schema.py`, `tests/test_match.py`

**Interfaces:**
- Produces in `schema.py` (all dataclasses, every field has a default so partial profiles load):
  - `LEVELS = ("especialista","medio","iniciante")`, `CONTRACTS = ("CLT","PJ","ambos")`
  - `Skill(name: str, level: str = "iniciante", evidence: str = "")`
  - `Bullet(text: str, metric: str | None = None)`
  - `Experience(company, role, start: str, end: str | None, bullets: list[Bullet])`
  - `Project(name, description, url: str | None = None)`, `Certification(name, issuer, year: int | None = None)`, `Language(name, level)`
  - `Constraints(modality: list[str], cities: list[str], vetoed_companies: list[str], vetoed_sectors: list[str], current_employer: str | None)`
  - `Screening(salary_expectation: int | None, contract: str, availability: str, email: str, phone: str, years_by_skill: dict[str, float])`
  - `Behavior(work_style: str, motivators: list[str], track: str)` with `track` in `("especialista","gestao","indefinido")`
  - `StretchPolicy(stretch_from: int = 90, risky_below: int = 50)`
  - `Profile(name, age: int | None, state, city, experiences, skills, certifications, languages, projects, constraints, screening, behavior, stretch_policy)`
  - `profile_to_dict(p) -> dict`, `profile_from_dict(d: dict) -> Profile` (unknown keys ignored, missing keys default)
  - `validate(p: Profile) -> list[str]` (PT-BR messages; `[]` when valid)
- Produces in `match.py`:
  - `normalize(skill: str) -> str` (casefold, strip accents, collapse whitespace)
  - `coverage(required: list[str], skills: list[Skill]) -> tuple[int, list[str]]` (percent floor, original-spelling missing list; `ValueError` if `required` empty)
  - `label(pct: int) -> str` (Global Constraints labels)
  - `stretch_action(pct: int, policy: StretchPolicy) -> str` -> `"esticar"` | `"esticar_marcado"` | `"arriscada"`

- [ ] **Step 1: Write failing tests.**
  - `test_schema.py`: `test_roundtrip` (`profile_from_dict(profile_to_dict(p)) == p` on a full profile); `test_partial_profile_loads` (`profile_from_dict({"name":"Ana"}).experiences == []`); `test_validate_flags_bad_level` (`Skill("SQL","guru")` yields an error containing "nível"); `test_validate_flags_bad_contract`; `test_validate_accepts_no_experience` (student profile with only projects and skills -> `[]`).
  - `test_match.py`: `test_label_boundaries` asserting 49, 50, 69, 70, 79, 80, 99, 100 map to the Global Constraints labels; `test_coverage_normalizes` (`coverage(["power bi","SQL "],[Skill("Power  BI"),Skill("sql")]) == (100, [])`); `test_coverage_accents` (`"analise de dados"` matches `Skill("Análise de Dados")`); `test_coverage_floor` (199 of 200 -> 99, never 100); `test_coverage_reports_missing`; `test_coverage_empty_required_raises`; `test_stretch_action` (90 -> esticar, 89 and 50 -> esticar_marcado, 49 -> arriscada; custom policy `StretchPolicy(80, 40)` shifts the cuts).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_schema.py tests/test_match.py -v` -> FAIL.
- [ ] **Step 3: Implement** `schema.py` and `match.py`. Use `dataclasses.asdict` for serialization.
- [ ] **Step 4: Run** the same command -> PASS.
- [ ] **Step 5: Commit.** `git add jobbot/schema.py jobbot/match.py tests/test_schema.py tests/test_match.py` -> `git commit -m "feat(schema): add profile schema, match labels and stretch policy"`.

### Task 3: Profile storage and interview state

**Files:**
- Create: `jobbot/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: `Profile`, `profile_from_dict`, `profile_to_dict` (Task 2).
- Produces:
  - `STEPS = ("identidade","experiencias","skills","certificacoes_idiomas","restricoes","triagem","comportamento")`
  - `STEP_FIELDS: dict[str, tuple[str, ...]]`: identidade -> name, age, state, city; experiencias -> experiences, projects; skills -> skills; certificacoes_idiomas -> certifications, languages; restricoes -> constraints; triagem -> screening, stretch_policy; comportamento -> behavior
  - `class ProfileError(Exception)`
  - `home() -> Path` (`JOBBOT_HOME` or `~/.jobbot`)
  - `slugify(name: str) -> str` (ASCII lowercase, hyphens, no path separators; `ValueError` if empty)
  - `profile_dir(name: str) -> Path`
  - `save_profile(name: str, p: Profile) -> Path` (atomic: write temp file then `os.replace`)
  - `load_profile(name: str) -> Profile`
  - `put_step(name: str, step: str, data: dict) -> None` (merges only `STEP_FIELDS[step]`, marks step done)
  - `next_step(name: str) -> str | None`

- [ ] **Step 1: Write failing tests** in `tests/test_store.py`:
  - `test_slugify_strips_accents`: `slugify("José da Silva") == "jose-da-silva"`.
  - `test_slugify_blocks_traversal`: `slugify("../../etc") == "etc"`; `profile_dir("../../etc").parent == tmp_home / "profiles"`.
  - `test_slugify_empty_raises`: `pytest.raises(ValueError)` for `"///"`.
  - `test_two_profiles_isolated`: `put_step` identidade for "Ana" and "Bia"; `load_profile("Ana").name == "Ana"`; Bia's file untouched.
  - `test_corrupt_yaml_raises_with_path`: write `a: [` into the profile file; `pytest.raises(ProfileError, match="profile.yaml")`; file content unchanged afterwards.
  - `test_put_step_rejects_foreign_fields`: `put_step("ana","skills",{"age":5})` raises `ValueError`.
  - `test_resume_walks_steps_in_order`: new profile -> `next_step == "identidade"`; after `put_step` for the first two steps -> `"skills"`; after all seven -> `None`.
  - `test_save_is_atomic`: monkeypatch `os.replace` to raise; the previous `profile.yaml` is intact.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_store.py -v` -> FAIL (module missing).
- [ ] **Step 3: Implement** `jobbot/store.py` per the interfaces. State is a `state.yaml` next to `profile.yaml` holding `{"done": [step, ...]}`. Corrupt YAML in either file raises `ProfileError` with the file path.
- [ ] **Step 4: Run** the same command -> PASS.
- [ ] **Step 5: Commit.** `git add jobbot/store.py tests/test_store.py` -> `git commit -m "feat(store): add per-person profile storage with resumable steps"`.

### Task 4: Honesty check and base CV

**Files:**
- Create: `jobbot/honesty.py`, `jobbot/cv.py`
- Test: `tests/test_honesty.py`, `tests/test_cv.py`

**Interfaces:**
- Consumes: `Profile`, `Skill`, `LEVELS` (Task 2).
- Produces:
  - `honesty.unsupported_numbers(text: str, p: Profile) -> list[str]`: numeric tokens in `text` not backed by the profile. Allowed values: numbers inside `Bullet.metric`, `years_by_skill` values, `Certification.year`, years found in experience `start`/`end`, and `cv.total_years(p, today)`. A token matches by numeric value, ignoring `%` and decimal comma. Token regex: `\d+(?:[.,]\d+)?`.
  - `class HonestyError(Exception)` in `honesty.py`
  - `cv.total_years(p: Profile, today: date) -> int` (span from earliest experience start to today, floored; 0 without experiences)
  - `cv.render_base_cv(p: Profile, summary: str, today: date) -> str`: PT-BR Markdown. Sections in order: header (name, city/state, email, phone), Resumo, Experiência, Projetos, Competências (grouped especialista, médio, iniciante), Certificações, Idiomas. Empty sections are omitted. Raises `HonestyError` listing the offending tokens if `summary` has unsupported numbers.
  - Known limit, to note in a code comment: `shortcut: only numbers are checked in free text, employer or certification names invented in the summary are not detected; upgrade when the summary is generated unattended.`

- [ ] **Step 1: Write failing tests.**
  - `test_honesty.py`: `test_reported_metric_allowed` (metric "40%", text "reduzi 40%" -> `[]`); `test_invented_metric_flagged` (text "reduzi 70%" -> `["70%"]`); `test_age_is_not_a_metric` (profile age 40, text "40%" -> flagged); `test_decimal_comma` ("2,5" matches `years_by_skill` 2.5); `test_total_years_allowed`.
  - `test_cv.py`: `test_cv_without_experience` (student profile: output has "Projetos" and "Competências", no "Experiência" heading, no exception); `test_cv_omits_empty_sections`; `test_cv_rejects_unsupported_number` (`pytest.raises(HonestyError)`); `test_cv_skill_order` (especialista listed before iniciante); `test_cv_uses_only_profile_employers` (every company in output is in the profile).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_honesty.py tests/test_cv.py -v` -> FAIL.
- [ ] **Step 3: Implement** both modules.
- [ ] **Step 4: Run** -> PASS.
- [ ] **Step 5: Commit.** `git add jobbot/honesty.py jobbot/cv.py tests/test_honesty.py tests/test_cv.py` -> `git commit -m "feat(cv): add base CV rendering with fabricated-number check"`.

### Task 5: Market aggregation and focus ranking

**Files:**
- Create: `jobbot/market.py`
- Test: `tests/test_market.py`

**Interfaces:**
- Consumes: `Profile`, `coverage`, `label`, `normalize` (Task 2).
- Produces:
  - `CORE_SHARE = 40` (a skill is core when it appears in at least 40% of a role's jobs)
  - `Job(title: str, company: str, skills: list[str], salary_min: int | None = None, salary_max: int | None = None, applicants: int | None = None, url: str = "")`
  - `RoleReport(role: str, n_jobs: int, top_skills: list[tuple[str, int]], salary_median: int | None, applicants_median: int | None)` where `top_skills` is `(display name, share percent)` sorted by share desc, max 15, skills merged through `normalize`
  - `build_report(role: str, jobs: list[Job]) -> RoleReport` (zero jobs -> `n_jobs=0`, empty list, `None` medians)
  - `FocusRow(role: str, coverage: int, label: str, missing: list[str], n_jobs: int, salary_median: int | None, applicants_median: int | None)`
  - `rank_focus(reports: list[RoleReport], p: Profile) -> list[FocusRow]`: sort by coverage desc, then `n_jobs` desc, then `applicants_median` asc with `None` last. Required skills = core skills of the report; a report with no core skills gets coverage 0 and label "Arriscado".
  - Salary per job is the midpoint of min and max, or the single value present; jobs with neither are skipped for the median. Medians via `statistics.median`, returned as `int`.

- [ ] **Step 1: Write failing tests.** `test_zero_jobs_report` (no exception, `top_skills == []`, medians `None`); `test_skill_merge` ("SQL", "sql ", "Sql" count as one skill at 100%); `test_salary_median_ignores_missing`; `test_applicants_all_missing`; `test_core_threshold` (skill in 39% of jobs is not required, in 40% is); `test_rank_by_coverage_then_demand`; `test_rank_handles_empty_core`.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_market.py -v` -> FAIL.
- [ ] **Step 3: Implement** `jobbot/market.py`.
- [ ] **Step 4: Run** -> PASS.
- [ ] **Step 5: Commit.** `git add jobbot/market.py tests/test_market.py` -> `git commit -m "feat(market): aggregate job listings and rank focus options"`.

### Task 6: CLI

**Files:**
- Create: `jobbot/cli.py`, `jobbot/__main__.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: all earlier modules.
- Produces `python -m jobbot <command>`; exit code 0 on success, 1 on a reported problem, message on stderr in PT-BR:
  - `status <name>` -> prints `next_step` or `completo`
  - `put <name> <step> <yaml-file>` -> `put_step`; invalid step or field -> exit 1
  - `validate <name>` -> prints each `validate` error; exit 1 if any
  - `match <name> --required "SQL,Python"` -> prints `pct`, `label`, `stretch_action`, `missing` (one `key: value` per line)
  - `market <name> <jobs.json>...` -> each file is `{"role": str, "jobs": [Job fields]}`; prints a Markdown table of `rank_focus` rows
  - `cv <name> --summary-file <path>` -> writes `cv-base.md` in the profile dir; `HonestyError` -> exit 1 listing tokens
  - `check <name> <text-file>` -> prints `unsupported_numbers`; exit 1 if any

- [ ] **Step 1: Write failing tests** with `subprocess.run([sys.executable,"-m","jobbot",...], env={"JOBBOT_HOME": ...})`: `test_status_new_profile` (`identidade`); `test_put_unknown_step_exits_1`; `test_match_output_keys`; `test_cv_blocks_invented_number` (exit 1, stderr names the token); `test_check_clean_text_exits_0`.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_cli.py -v` -> FAIL.
- [ ] **Step 3: Implement** with `argparse`, one function per command, no logic beyond calling the modules.
- [ ] **Step 4: Run** -> PASS.
- [ ] **Step 5: Commit.** `git add jobbot/cli.py jobbot/__main__.py tests/test_cli.py` -> `git commit -m "feat(cli): expose profile, match, market and cv commands"`.

### Task 7: Install and vet linkedin-skills

**Files:**
- None in the repo. Changes the user's global Claude Code plugin config, as the owner requested.

- [ ] **Step 1: Read before installing.** `gh api repos/sergebulaev/linkedin-skills/readme --jq .content | base64 -d` and use the Claude Code install section. List the skill folders under `.claude/skills/` (`linkedin-profile-optimizer`, `linkedin-interviewer`, `linkedin-humanizer`), read each `SKILL.md`, and note whether any needs an API key or network service. Do not set any key. If a skill requires one, record that in `README.md` (Task 10) and continue without it.
- [ ] **Step 2: Install** with the commands from the README (`claude plugin marketplace add sergebulaev/linkedin-skills`, then install). Confirm the exact syntax with `claude plugin --help` first.
- [ ] **Step 3: Verify.** `claude plugin list` shows `linkedin-skills`. Expected: listed and enabled.
- [ ] **Step 4:** Nothing to commit. Record the installed version and any key requirement in the commit body of Task 10.

### Task 8: Skills and references

**Files:**
- Create: `skills/jobbot-interview/SKILL.md`, `skills/jobbot-market/SKILL.md`, `skills/jobbot-outputs/SKILL.md`, `references/principles.md`, `references/visibility-checklist.md`, `references/honesty-and-stretch.md`
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: CLI commands from Task 6; `linkedin-profile-optimizer`, `linkedin-interviewer`, `linkedin-humanizer` from Task 7, used only when present. Each jobbot skill must work without them.
- Produces: three skills, each with YAML frontmatter `name` equal to its folder name and a PT-BR `description` stating when to use it.

Content each skill must carry (the implementer writes the prose):
- **jobbot-interview:** shows the mandatory notice first; loops `python -m jobbot status <name>` until `completo`; asks one step at a time in the order of `STEPS`; for every skill asks level and one piece of evidence; asks for result numbers but never suggests one; saves each step with `put`; runs `validate` at the end; covers the fields in the spec "Objetivos" first bullet; behavior step uses a simple documented instrument kept in `references/` (builder's choice).
- **jobbot-market:** picks candidate roles from the profile plus the person's interest; collects about 50 public listings per role (WebSearch, WebFetch or browser; public pages only, no bulk login scraping, respect the site's terms); writes `jobs-<role>.json` in the CLI format; runs `market`; writes `focus-report.md` (ranking, justification, skill gaps, one quick project per gap) in the profile dir.
- **jobbot-outputs:** writes `linkedin.md` (headline, Sobre, experiências, competências) from the profile only and runs `check` on it; generates the base CV with `cv`; prints the visibility checklist; reviews GitHub read-only with `gh` (README, pinned repos, activity) and writes `github-review.md`. Never edits LinkedIn or GitHub.
- `references/principles.md` restates in original words the principles listed in the spec decision "Conhecimento do ebook". `references/visibility-checklist.md` lists profile visibility and contact settings in original wording. `references/honesty-and-stretch.md` states the honesty line and the stretch policy from Global Constraints.

- [ ] **Step 1: Write failing tests** in `tests/test_skills.py`: `test_each_skill_has_frontmatter` (starts with `---`, has `name` equal to folder name and non-empty `description`); `test_notice_in_interview_skill` (the mandatory notice string appears verbatim); `test_referenced_files_exist` (every `references/*.md` path mentioned in a SKILL.md exists); `test_no_ebook_text` (skipped unless env `JOBBOT_EBOOK_TXT` points to the extracted ebook text; fails if any 8-word sequence from it appears in any repo `.md`; produce the text with `pdftotext` on the owner's PDF); `test_no_owner_data` (no `Samuel`, `buenotty` or `vipp` in tracked files outside `docs/`).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_skills.py -v` -> FAIL.
- [ ] **Step 3: Write the three skills and three reference files** to the content above.
- [ ] **Step 4: Run** with the ebook check enabled: `JOBBOT_EBOOK_TXT=<path> .venv/bin/pytest tests/test_skills.py -v` -> PASS.
- [ ] **Step 5: Commit.** `git add skills references tests/test_skills.py` -> `git commit -m "feat(skills): add interview, market and outputs skills"`.

### Task 9: End-to-end dry run

**Files:**
- Create: `tests/fixtures/maria/` (step YAML files, `jobs-analista.json`, `jobs-engenheiro.json`), `tests/test_e2e.py`

**Interfaces:**
- Consumes: the CLI. The fixture person is fictional ("Maria Exemplo"), not the owner.

- [ ] **Step 1: Write the test** `test_full_flow`: with `JOBBOT_HOME` in `tmp_path`, run `put` for all seven steps from the fixtures, assert `status` prints `completo`, `validate` exits 0, `match --required "SQL,Python"` prints the expected label, `market` on both job files lists the better-covered role first, `cv` writes `cv-base.md` containing "Maria Exemplo", and `check` exits 1 on a text containing a number absent from the fixture.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_e2e.py -v` -> FAIL until fixtures exist, then PASS.
- [ ] **Step 3: Run the full suite** `.venv/bin/pytest -v` -> all PASS.
- [ ] **Step 4: Commit.** `git add tests/fixtures tests/test_e2e.py` -> `git commit -m "test(e2e): cover full profile-mapping flow with a fictional person"`.

### Task 10: README and live check

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`** in PT-BR: what JobBot is, the A/B/C/D roadmap, install (`claude plugin marketplace add` with the repo path, plus `pip install -e .`), where data lives (`~/.jobbot`, local only), the mandatory notice, the stretch and honesty rules, and the `linkedin-skills` dependency (optional, with any key requirement found in Task 7).
- [ ] **Step 2: Live check.** In a Claude Code session with the plugin loaded and a throwaway `JOBBOT_HOME`, run `jobbot-interview` on the fictional fixture answers up to the second step. Expected: notice shown, `status` advances, a profile file appears under the throwaway home and nothing under the repo.
- [ ] **Step 3: Commit.** `git add README.md` -> `git commit -m "docs: add README with install, privacy and risk notice"`, body noting the `linkedin-skills` version from Task 7.
