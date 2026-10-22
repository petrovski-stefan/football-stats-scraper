---
name: check
description: Run the mechanical checks — the eight quality gates (ruff check, ruff format --check, mypy, complexipy, pyscn, deptry, bandit, pytest under coverage), the engine self-check when features/engine.py changed, and the manual caller and coverage sweeps over the current diff — and say whether a statistical review (/stats-review) is due. Use after any code change, before committing. It never starts the stats-reviewer agent.
allowed-tools: Bash(uv run ruff *) Bash(uv run mypy *) Bash(uv run complexipy *) Bash(uv run pyscn *) Bash(uv run deptry *) Bash(uv run bandit *) Bash(uv run coverage *) Bash(uv run pytest *) Bash(git diff *) Bash(git ls-files *) Bash(git status *) Bash(git log *) Bash(uv run python -m features.engine --self-check) Grep Read
---

# /check — the mechanical checks

Root `CLAUDE.md` ("Quality gates") requires all eight tools on every change **and** a caller
sweep by hand, because ruff and mypy pass clean on unused functions, unreferenced constants
and private names called across modules, and pyscn's dead-code detector misses
unreferenced definitions too (`notes/LOG/MIGRATIONS.md`). It also requires that new code ships
with its tests, which the coverage sweep checks line by line. This skill does all of that.
Every check here gives the same result for the same code.

The statistical review is a judgment, not a gate, and it is slow, so it is a skill of its own:
`/stats-review`, run once per finished change. This skill only says when it is due (§4).

Run everything from the repo root. Do not fix anything unless the user asks; this skill
reports.

## 1. The eight tools, then the engine self-check

Run each one even if an earlier one fails. Capture exit code and the failing lines.

1. `uv run ruff check`
2. `uv run ruff format --check`
3. `uv run mypy .`
4. `uv run complexipy . --failed`
5. `uv run pyscn analyze .`
6. `uv run deptry .`
7. `uv run bandit -q -r domain scrapers features analysis ml qa` — FAIL on exit 1; give each
   finding (file:line, test id, severity, message).
8. `uv run coverage run -m pytest -q` — FAIL on any failed or errored test; give the `FAILED`
   lines. It also writes `.coverage` (gitignored), which §3 reads.

Then the engine self-check, only when `features/engine.py` is in the diff (changed or
untracked): `uv run python -m features.engine --self-check`. FAIL on a non-zero exit; give the
last ~20 lines. It proves the old pipeline's as-of-round invariant.

pyscn exits 0 even when it reports findings, and its text summary gives only an
"Architecture NN% compliant" score, not what the violations are. Get them from JSON:

```
uv run pyscn analyze --json --output - --select deps . 2>/dev/null \
  | uv run python -c "import json,sys; v=json.load(sys.stdin)['system']['architecture_analysis']['violations']; [print(x['type'], x['severity'], x['module'], '->', x.get('target',''), x['rule']) for x in v]"
```

Treat any violation of **type `layer`** (a lower package importing a higher one) as FAIL —
the layer rule is the point of the package split. `responsibility` / `cohesion` violations,
clone groups and coupling are WARN with their counts. Dead-code findings > 0 are FAIL.
Pass through any pyscn config warning (e.g. an unknown key in `.pyscn.toml`). pyscn writes
an HTML report under `.pyscn/reports/`; give the path, do not paste it.

## 2. The caller sweep

Scope: the current diff against `HEAD`, plus untracked `.py` files.

1. Collect the changed files:
   - `git diff HEAD --name-only -- "*.py"`
   - `git ls-files --others --exclude-standard -- "*.py"`
     If both are empty, the sweep is "nothing to sweep" and passes.
2. Collect the **names** added or changed:
   - From `git diff HEAD -U0 -- "*.py"`: every added line (`+`) that defines
     `def name`, `async def name`, `class name`, a module-level `NAME = ` / `NAME: T = `
     (UPPER_CASE constant) or a module-level `_name = ` (private). Also every function
     named in a hunk header (`@@ ... @@ def name(`) — that function's body changed.
   - For untracked files: every top-level `def`, `class`, UPPER_CASE constant and `_private`
     name, plus methods (`    def name`).
     Skip dunders (`__init__`, `__all__`, ...) and `main`.
3. For each name, use Grep with pattern `\bname\b` over `**/*.py` (exclude `.venv`), and
   subtract the definition line itself. Classify:
   - **unreferenced** — no other occurrence anywhere.
   - **private-cross-module** — the name starts with a single `_` and appears in a module
     other than the one defining it (an import `from x import _name` or `module._name`).
     A private name that each module **defines for itself** (e.g. `_share` in both
     `features/goals.py` and `features/events.py`) is two names, not a cross-module call.
   - **ok** — referenced, and private names only within their own module.
4. Before reporting an unreferenced name, check the known indirect-use patterns and mark it
   `ok (indirect: <how>)` only if one applies, with the file:line that proves it:
   - pydantic `@computed_field` / validators (used via `model_dump()` / the model);
   - a method invoked through an attribute on another name (`.name(`) — grep `\.name\b`;
   - an entry in a registry dict or list (e.g. `FAMILIES`, `BUCKETS`) or `getattr` string;
   - an `argparse` flag handler reached from `main`;
   - a `test_*` function in `tests/`, which pytest collects by name.
     Otherwise it stays **unreferenced**. Do not guess.

## 3. The coverage sweep

Scope: the source lines the diff adds in the six packages (not `tests/`), against the
`.coverage` data of gate 8. If gate 8 failed, the sweep is "not run: tests failed".

1. Collect the changed source files:
   - `git diff HEAD --name-only -- domain scrapers features analysis ml qa` (`.py` files only)
   - `git ls-files --others --exclude-standard -- domain scrapers features analysis ml qa`
     If both are empty, the sweep is "nothing to sweep" and passes.
2. `uv run coverage report --include=<the files, comma-separated>`. Its `Missing` column lists
   the lines no test ran (ranges like `318-324`).
3. Collect the added lines: from `git diff HEAD -U0 -- <file>`, the `+c,d` part of each hunk
   header gives lines `c` to `c+d-1`; an untracked file adds every line.
4. Each added line that is in `Missing` is either:
   - **by design** — untested on purpose, as root `CLAUDE.md` says: browser code
     (`scrapers/driver.py`, `scrapers/browser_pool.py`, a scraper's Selenium loop), a `main()` /
     `build()` / `build_all()` that only reads and writes files, or a module waiting for plan
     steps P4–P5. Say which.
   - **untested** — anything else: FAIL, because new code ships with its tests.

## 4. Is a stats review due?

1. `git diff HEAD --name-only -- features analysis ml notes tests/features tests/analysis tests/ml`
   and `git ls-files --others --exclude-standard -- <the same paths>`.
2. Any file listed: `stats review DUE` — run `/stats-review` before committing. There is no
   commit while a review is due or says BLOCK (root `CLAUDE.md`, "Conventions"). No file:
   `n/a`. Do not start the `stats-reviewer` agent here.

## 5. Output

First, per-tool detail only for tools that failed or warned (the failing lines, trimmed to
the first ~15). Then the sweep table (name, file:line, verdict) listing only non-`ok` rows,
plus a count of `ok` rows. Then the coverage sweep's untested and by-design lines (file:line
and the code).

End with exactly this summary block, one line each:

```
ruff check        PASS|FAIL  (<n> errors)
ruff format       PASS|FAIL  (<n> files would be reformatted)
mypy              PASS|FAIL  (<n> errors)
complexipy        PASS|FAIL  (<n> functions over threshold)
pyscn             PASS|WARN|FAIL  (<clones> clone groups, <dead> dead code, <arch> layer violations)
deptry            PASS|FAIL  (<n> dependency issues)
bandit            PASS|FAIL  (<n> findings)
pytest            PASS|FAIL  (<n> passed, <f> failed)
engine self-check PASS|FAIL|n/a
caller sweep      PASS|FAIL  (<n> names checked, <u> unreferenced, <p> private cross-module)
coverage sweep    PASS|FAIL|n/a  (<n> added lines, <u> untested, <d> by design)
stats review      DUE|n/a  (<n> files in its scope; DUE: run /stats-review before committing)
```
