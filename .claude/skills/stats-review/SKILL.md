---
name: stats-review
description: Run the stats-reviewer agent on the current diff when it touches features/, analysis/, ml/, notes/ (not notes/LOG/) or the leak tests (tests/features, tests/analysis, tests/ml). Use once per finished change, before committing — when /check reports `stats review DUE` — or when the user asks for a statistical review.
allowed-tools: Bash(git diff *) Bash(git ls-files *) Bash(git log *) Bash(git status *) Bash(uv run python -m features.engine --self-check) Agent Grep Read
---

# /stats-review — the statistical review of one finished change

This project's real failure mode is statistical leakage, and leaky code passes every gate. For
some leaks the `stats-reviewer` agent is the only guard: on 2026-09-28 a leak planted in
`features/engine.py` passed the engine's self-check, and only the reviewer caught it
(`notes/WORKING/DECISIONS.md` D5). The review is a judgment, not a gate, and it is slow (one
review on 2026-10-22: 7.6 min, 122k tokens). So it runs once per finished change, not after
every edit; `/check` says when it is due.

Run everything from the repo root. Do not fix anything unless the user asks; this skill
reports.

## 1. Scope

1. `git diff HEAD --name-only -- features analysis ml notes ':!notes/LOG' tests/features tests/analysis tests/ml`
2. `git ls-files --others --exclude-standard -- features analysis ml notes ':!notes/LOG' tests/features tests/analysis tests/ml`

If both are empty: `stats review n/a`, and stop. `notes/LOG/` is out of scope: it records
changes and holds no claim to review. The leak tests are in scope because a change
there can weaken the guard without touching the code it guards (2026-10-22: generated cases
whose gaps could not show a leak, found by the reviewer).

## 2. The engine self-check

Only when `features/engine.py` is in the scope list: `uv run python -m features.engine --self-check`.
Capture the exit code and the last ~20 lines. Otherwise the result is `not run: unchanged`.
`/check` runs it too, as a gate; here its output is evidence for the reviewer.

## 3. The review

1. Spawn the `stats-reviewer` agent with: the full
   `git diff HEAD -- features analysis ml notes ':!notes/LOG' tests/features tests/analysis tests/ml`, the
   untracked file list, `git log --oneline -15`, and the self-check's exit code and output
   (or `not run: unchanged`).
2. Relay its report verbatim. Do not re-judge its findings.

## 4. Output

The report, then exactly this line:

```
stats review      OK|BLOCK|n/a  (<n> findings, <v> not verified)
```

A BLOCK means no commit until its findings are fixed, or until the user decides to commit
anyway.
