---
name: check
description: Run the seven quality gates (ruff check, ruff format --check, mypy, complexipy, pyscn, deptry, pytest), the manual caller sweep over the current diff that the tools miss, and — when the diff touches features/, modelling/, analysis/ or notes/ — the self-checks and the stats-reviewer agent. Use after any code change, before committing.
allowed-tools: Bash(uv run ruff *) Bash(uv run mypy *) Bash(uv run complexipy *) Bash(uv run pyscn *) Bash(uv run deptry *) Bash(uv run pytest *) Bash(git diff *) Bash(git ls-files *) Bash(git status *) Bash(git log *) Bash(uv run python -m features.engine --self-check) Bash(uv run python -m modelling.scoreline --self-check --leak-check) Agent Grep Read
---

# /check — seven gates plus the caller sweep

Root `CLAUDE.md` ("Quality gates") requires all seven tools on every change **and** a caller
sweep by hand, because ruff and mypy pass clean on unused functions, unreferenced constants
and private names called across modules, and pyscn's dead-code detector misses
unreferenced definitions too (`notes/LOG/MIGRATIONS.md`). This skill does both.

Run everything from the repo root. Do not fix anything unless the user asks; this skill
reports.

## 1. The seven tools, in this order

Run each one even if an earlier one fails. Capture exit code and the failing lines.

1. `uv run ruff check`
2. `uv run ruff format --check`
3. `uv run mypy .`
4. `uv run complexipy . --failed`
5. `uv run pyscn analyze .`
6. `uv run deptry .`
7. `uv run pytest -q` — FAIL on any failed or errored test; give the `FAILED` lines.

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

## 3. Statistical review

1. `git diff HEAD --name-only -- features modelling analysis notes` and
   `git ls-files --others --exclude-standard -- features modelling analysis notes`.
   If both are empty: `stats review n/a`, skip the rest of this section.
2. Self-checks, each only when its file is in that list (changed or untracked). Capture the
   exit code and the last ~20 lines of output:
   - `features/engine.py` → `uv run python -m features.engine --self-check`
   - `modelling/scoreline.py` → `uv run python -m modelling.scoreline --self-check --leak-check`
3. Spawn the `stats-reviewer` agent with: the full `git diff HEAD -- features modelling analysis notes`,
   the untracked file list, `git log --oneline -15`, and each self-check's exit code and
   output — or `not run: unchanged` for each file not in the list.
4. Relay its report verbatim under "Statistical review". Do not re-judge its findings.

## 4. Output

First, per-tool detail only for tools that failed or warned (the failing lines, trimmed to
the first ~15). Then the sweep table (name, file:line, verdict) listing only non-`ok` rows,
plus a count of `ok` rows. Then the statistical review, if §3 ran.

End with exactly this summary block, one line each:

```
ruff check        PASS|FAIL  (<n> errors)
ruff format       PASS|FAIL  (<n> files would be reformatted)
mypy              PASS|FAIL  (<n> errors)
complexipy        PASS|FAIL  (<n> functions over threshold)
pyscn             PASS|WARN|FAIL  (<clones> clone groups, <dead> dead code, <arch> layer violations)
deptry            PASS|FAIL  (<n> dependency issues)
pytest            PASS|FAIL  (<n> passed, <f> failed)
caller sweep      PASS|FAIL  (<n> names checked, <u> unreferenced, <p> private cross-module)
stats review      OK|BLOCK|n/a  (<n> findings, <v> not verified)
```
