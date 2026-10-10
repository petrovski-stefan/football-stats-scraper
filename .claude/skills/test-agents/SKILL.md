---
name: test-agents
description: Known-answer tests for the three project agents (stats-reviewer, ledger-auditor, dom-prober) and the --holdout hook. Plants a leak, a clean diff and a ledger inconsistency, probes live pages, proves the --holdout block, restores every file it touched, and ends with git status. Run after any change to an agent, hook or settings file.
disable-model-invocation: true
allowed-tools: Read Grep Glob Edit Agent Skill Bash(git status *) Bash(git diff *) Bash(git restore *) Bash(git log *) Bash(sha1sum *) Bash(uv run *) Bash(echo *) PowerShell(Write-Output *)
---

# /test-agents — known-answer tests for agents and hooks

Each test has a fixed expected answer. Report every test as **PASS** or **FAIL** with a short
summary of the actual output. **Do not fix failures**: explain the cause and propose a change.
First written 2026-09-28, from the tests run by hand that day.

Run from the repo root. Never give an agent the expected answer: the prompts below are the
whole prompt.

## Blindness rules

- **Never write an expected answer into `notes/`, any `CLAUDE.md` or `notes/DECISIONS.md`.**
  The agents read those files as their instructions, so an answer placed there turns a
  known-answer test into a reading test. This includes a planted leak's column or line, a
  random match's scores, and which variant or match was drawn.
- Random draws (test 1's variant, test 4's second match) exist only in this session's
  context and in the final summary. Do not write them to a file, not even the scratchpad.
- Two answers are already exposed and stay exposed. The leak in `notes/DECISIONS.md` D5
  (`combined_recent_gf` + FT goals) is therefore **not** in test 1's pool. Match 2789151's
  answer is in `scrapers/CLAUDE.md` §7, so test 4 draws a second, blind match.

## 0. Baseline

Other work may be uncommitted, so "clean" means **identical to the baseline**, not an empty
`git status`. Before planting anything, save this to `<scratchpad>/baseline.txt`:

```
git status --porcelain; git diff | sha1sum
```

Rules for every planted edit:

- Make it with the Edit tool, in **exactly one file**. Never run `sed -i` or any bulk
  rewrite over several files. A no-match `sed -i` still rewrites line endings, and the
  reviewer then correctly reports that file as modified.
- Restore with `git restore <that file>` only, never `git restore .`: the baseline may hold
  the user's own uncommitted work.
- Run tests 1–3 **sequentially**. The reviewer and the auditor both read `notes/STATE.md`, so
  a planted edit that is still live contaminates the next test.

## 1. stats-reviewer — planted leak

1. Draw one variant at random:
   `uv run python -c "import random; print(random.randint(1, 6))"`. Keep the number in
   context only (see the blindness rules).

   | #   | file · function                                 | plant (one Edit)                                                                                                                                                                    | post-match input                                   |
   | --- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
   | 1   | `features/engine.py` · `_h2h_ht_goals_avg`      | in its loop, `h = _block(df, "h2h", n, "ht_home_goals")` → `h = df["ht_home_goals"]`                                                                                                | target row's HT goals instead of the H2H block     |
   | 2   | `features/engine.py` · `_corner_goal_share_gap` | `gh = _block(df, section, n, "ft_home_goals")` → `gh = df["ft_home_goals"]`                                                                                                         | target row's FT goals instead of the history block |
   | 3   | `features/engine.py` · `_market_lines`          | `"implied_over": col("implied_over"),` → `"implied_over": col("implied_over") + col("over_25"),`                                                                                    | derived result flag `over_25`                      |
   | 4   | `features/engine.py` · `_vig_free`              | `"mkt_sup": np.log(p_home / p_away),` → `"mkt_sup": np.log(p_home / p_away) + (df["ft_result"] == "1"),`                                                                            | derived result flag `ft_result`                    |
   | 5   | `features/enrich.py` · `_goal_timing_features`  | after `timing = goal_features.build(merged, store)`, add `timing["away_late_goal_rate"] = timing["away_late_goal_rate"] + merged["ft_away_goals"]`                                  | `ft_away_goals`                                    |
   | 6   | `features/enrich.py` · `_event_features`        | after `built = event_features.build(...)`, add `built["home_yellows_while_leading_avg"] = built["home_yellows_while_leading_avg"] * (1 + merged["is_comeback_home"].astype(float))` | derived result flag `is_comeback_home`             |

   Variant 1's line also appears in `_h2h_ht_nondraw_rate`. Include the neighbouring lines
   in the Edit so it hits `_h2h_ht_goals_avg`. The pair in variants 1 and 2 is subtle on
   purpose: the history column and the leaking column have the same name, and only the
   `_block` wrapper separates them. If a line comes out longer than 100 characters, wrap it
   the way ruff format would. Note the file:line of the plant.

2. Run the `check` skill in full. The engine self-check runs only for variants 1–4. For 5–6
   it is "not run: unchanged", which is correct, because `features/engine.py` did not change.
3. **PASS** only if the stats review is **BLOCK** and a finding cites the planted line
   itself. A BLOCK that rests only on a missing or failing self-check is a FAIL.
   `features.engine --self-check` covers rolling features only and is expected to pass
   every variant, so its result is not part of the verdict.
4. `git restore <that file>`, then confirm the state matches the baseline.
5. Name the drawn variant only in the final summary.

## 2. stats-reviewer — clean diff

1. In `features/engine.py`, add one comment line (e.g. `# Vig-free market probabilities
follow.`) directly above `def _vig_free`. Change nothing else.
2. Run the `check` skill in full.
3. **PASS** only if the stats review is `## stats-reviewer — OK` with Findings `No findings.`
   A "Not verified" line about some _other_ file means the baseline was dirtied: report it.
4. `git restore features/engine.py`, then confirm the state matches the baseline.

## 3. ledger-auditor — planted inconsistency

1. Pick one row of the **Ledger** table in `notes/STATE.md` that is **not** mentioned under
   "Conflicts (listed, not resolved)". Read its cited source section and confirm the key
   number matches there. Then change one key number in the STATE row only. Used so far:
   2026-09-28 "Out-of-round matches suppress comebacks" (0.98× → 0.68×) and "Leader's 2H
   red card → completion" (17.65% → 27.65%). Vary the row between runs.
2. Spawn `ledger-auditor` with the prompt `Scope: full`, and nothing else. Do not name the
   row.
3. **PASS** if the report lists that row with verdict **source wins**. Other rows it
   reports are pre-existing issues (see `notes/DECISIONS.md` D6): list their count, do not
   judge them.
4. `git restore notes/STATE.md`, then confirm the state matches the baseline.

## 4. dom-prober — two live pages

Needs a network connection and a local Chrome. If a page fails to load, report that part as
FAIL (environment) and do not guess. The prompt template for both parts:

> "Which event icons appear on the live page of EPL 2025-26 match id `<id>` (`<home>` vs
> `<away>`, `<date>`)? For every event row give minute (with stoppage), side, icon filename
> and the kind the parser maps it to. Run the project's goal and event parsers on the same
> page and compare them with the raw DOM rows. Use the running score as an oracle. Report
> the number of pages you loaded."

Nothing else goes in the prompt: no score, no mention of any CSV.

**4a. Match 2789151 (Chelsea vs Fulham, 2025-08-30). Not blind:** its answer is in
`scrapers/CLAUDE.md` §7, which the prober reads first. It stays as a regression check.
**PASS** if it reports:

- exactly **one `1.png` Goal at 45+8'** (home, running score 1-0);
- exactly **one `7.png` Penalty Scored at 56'** (home, 2-0);
- final score **2-0**, and both parsers matching the DOM;
- its page count.

Measured 2026-09-28: 17 rows, made up of 2 goals, 9 subs, 4 yellows and 2 `14.png` VAR rows
(23', 52'). A different row count is a WARN to explain, not a FAIL, unless it touches the
goals.

**4b. A random match. This one is blind.**

1. Draw it from the schedule-page CSV (it prints to context only):
   ```
   uv run python -c "import csv,random; r=[x for x in csv.DictReader(open('data/archived/raw/english_premier_league_2025-2026.csv',encoding='utf-8')) if x['match_id']!='2789151' and x['ft_score'].replace(' ','')!='0-0']; x=random.choice(r); print(x['match_id'],x['date'],x['home_team_name'],'|',x['away_team_name'],'HT',x['ht_score'],'FT',x['ft_score'])"
   ```
   A 0-0 is excluded because it has no goal rows to check.
2. Confirm that nothing the prober reads mentions the match. Grep `notes/`, every
   `**/CLAUDE.md` and `scrapers/` for the match id, and for the fixture written as
   `<home>[^|\n]{0,15}<away>`. On any hit, draw again.
3. Take the expected answer **only from that CSV's `ht_score` and `ft_score`**. Never use
   `data/archived/raw/goals.csv`: it is the output of the parser under test, so it cannot be its
   oracle.
4. Spawn the prober with the template, filled in for this match.
5. **PASS** if the prober's goal rows (the parser output, checked against its DOM rows)
   reproduce **both scores with the right sides**. Count each side's goals with base
   minute ≤ 45, stoppage included (45+x' is first half), and each side's goals overall.
   Those counts must equal `ht_score` and `ft_score` respectively. A goal on the wrong
   side, a missing goal or an extra goal is a FAIL. An own goal counts for the side whose
   score advanced.
6. Name the drawn match and its scores only in the final summary.

## 5. --holdout hook proof

1. Bash: `echo hook-probe --holdout`. Expected: **blocked** by `block-holdout.sh`, with the
   message naming the hook shell and bash version.
2. PowerShell: `Write-Output "hook-probe --holdout"`. Expected: **blocked** the same way.
3. Control: Bash `echo hook-probe`. Expected: **allowed**, prints `hook-probe`.

**PASS** only if all three match. If step 1 or 2 runs and prints the text, the hook failed
open (usually bash missing from PATH). Report it as FAIL: root `CLAUDE.md` says the hook
fails open.

The hook greps the whole tool call, so **any** Bash or PowerShell command whose text
contains the flag is blocked, including a script that only mentions it in a string. Edit
this skill with the Edit tool, not a shell script.

## 6. Output

A table with columns #, test, PASS/FAIL, and actual output (1–2 lines each). Then list the
draws: test 1's variant (number, file:line) and test 4b's match (id, teams, HT/FT). Then an
explanation and proposed change for each FAIL. Then run `git status --short`, diff
`git status --porcelain; git diff | sha1sum` against the baseline, and say
**identical to baseline** or list what differs.
