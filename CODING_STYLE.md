# Coding style

This guide keeps the code easy to read, follow and change for a human developer who works without an AI coding agent. It covers what no tool checks: names, the shape of a function, blank lines, comments, error handling and tests. The eight quality gates (root `CLAUDE.md`, "Quality gates") check formatting, lint, types, complexity, dead code, dependencies, security and the test run; this guide does not repeat them.

Adopted 2026-10-22.

## 1. Scope

- The guide applies to all new and changed Python code, `tests/` included.
- **A function you change follows the guide as a whole:** fix its one-letter names, its missing blank lines and any other clear readability problem inside it. Leave names that are already clear, and leave everything outside the function. A half-renamed function reads worse than either version.
- Code that nobody changes stays as it is. A clean-up pass over a whole package is a change of its own, never part of a feature.
- **Two kinds of rule.**
  - **Must:** §3.2 (one-letter names, the `_df` suffix), §5 (blank lines), the whole-function scope above, §9 (data, domain rules, missing values), §10 (errors) and the `_private` rule of §11. A Must holds in every case; to change one, change this guide.
  - **Default:** everything else. Follow it unless the result clearly reads worse; then break it, with a comment that says why when the reason is not obvious. In a Default, words like "never" and "only" describe the usual case, not a ban.
- Rules that are not about readability are written once, elsewhere:
  - layers, imports, data paths, dependencies, commits: root `CLAUDE.md`;
  - what a test may and may not do (mechanics only, no network, no real site domains, one test module per source module): root `CLAUDE.md`, "Quality gates";
  - the rules of one package: that package's `CLAUDE.md`;
  - text in `notes/`: `notes/CLAUDE.md`.

## 2. The principle: readability over cleverness

Write for the next person who has to understand, debug or change the code. That person may be you, months from now, without an AI agent.

- Prefer explicit, plain code to compact or clever code. If a slightly longer version is clearly easier to understand, use the longer version.
- Prefer a few named steps to one dense expression when the steps are distinct operations.
- Make important assumptions visible in the code, not hidden in its behaviour.
- Keep complexity in proportion to the problem. No framework for one use case. No inheritance, metaprogramming, custom decorators or dynamic dispatch unless the problem needs them; the library decorators the project already uses (pytest, Hypothesis, pydantic, `dataclass`) are fine.
- Build for the callers that exist now. No parameter, option, callback or extension point that no caller or command uses yet; add it in the change that first needs it.
- The goal is not the fewest lines, the most abstraction or zero repetition. It is the least effort to understand the code and to change it safely.

## 3. Names

### 3.1 What a name says

- Name a variable after the data it holds, not its type or its position: `kickoff`, `home_goals`, `final_table`, not `time`, `value`, `row2` (the `_df` suffix, §3.2, is the one exception).
- Avoid empty names: `data`, `value`, `item`, `result`, `out`, `temp`, `info`, `obj`. A generic name is fine only in a few lines where its meaning is obvious.
- Use the project's words, and the same word for the same thing everywhere: the field names of `notes/FIELDS/` and the terms of `notes/REFERENCE/GLOSSARY.md` (league-season, kickoff, opening odds, HT/FT, comeback, 7+). Don't rename an established concept without a reason.
- When a word has two meanings here, a new name says which one. _Stage_ is a pipeline stage (`1_raw`, `2_row`, `3_multi`) and also a tab on the league page (`League`, `Apertura`).
- The short forms of the project's vocabulary are fine: `ht`, `ft`, `ah`, `ou`, `h2h`, `id`, and `one_x_two` for 1X2. Don't shorten other words to save typing.
- A statistical quantity is named after what it is, not its symbol: `degrees_of_freedom`, `p_value`, `cochran_q`, `tau_squared`. A printed column header or a library's own keyword (scipy's `df=`) keeps its spelling.
- A boolean reads as a yes/no question: `is_comeback`, `has_odds`, `is_rescheduled`.
- A function that does something is named after the action: `scrape_league`, `build`, `write_stage_csv`. A pure function that returns a value may be named after the value: `season_start_year`, `round_positions`. Never `process_data`, `handle` or `do_work`.
- A name never promises more than the code does. A flag `is_first_in_round` that is true for only one of several joint-first matches makes a false promise.
- British spelling, as in the rest of the project: `favourite`, `summarise`, `normalise`. Third-party names keep their own spelling.

### 3.2 Short names

One-letter names are allowed only for:

- `i`, a plain numeric loop index;
- `_`, a value you don't use;
- the variable of a one-line comprehension: `[f"s1_odds_1x2_open_{s}" for s in ("home", "draw", "away")]`.

Everything else gets a descriptive name, parameters included: `report: Report`, not `r: Report`. The comprehension exception is narrow: it is never a reason to write a dense line.

**A DataFrame's name ends in `_df`:** `matches_df`, `goals_df`, `final_table_df`. The part before `_df` says what the table holds, so never `frame_df` or `table_df`. This covers variables, parameters and dataclass fields; a Series or an array keeps a plain name. `df` alone is allowed only for a parameter of a helper that takes any table, such as the checks in `qa/universal.py`. Column names never change in a rename: they are data.

```python
# Before
for n in range(1, MATCHES_PER_SECTION + 1):
    h = _block(df, "h2h", n, "ht_home_goals")
    a = _block(df, "h2h", n, "ht_away_goals")
    ok = h.notna() & a.notna()

# After
for slot in range(1, MATCHES_PER_SECTION + 1):
    home_goals = _block(matches_df, "h2h", slot, "ht_home_goals")
    away_goals = _block(matches_df, "h2h", slot, "ht_away_goals")
    both_known = home_goals.notna() & away_goals.notna()
```

## 4. Functions

- One function, one job, and a name that says the job.
- Handle bad input and special cases first, with guard clauses and early returns, so the main work is not nested inside them.
- Keep nesting shallow: when the reader has to hold several open conditions to follow a line, flatten a condition or extract a step.
- Extract a helper when it gives a meaningful operation a name, removes real duplication, or lets the caller read as a list of steps. Don't extract only to shorten a function by a few lines, and don't split a simple operation into tiny helpers the reader has to jump between.
- Don't merge two functions only because they look alike. If their meanings differ, they will change apart later.
- Keep pure work apart from input and output. A pure function computes (`derive(row)`, a parser that returns primitives); a thin outer function reads files, drives the browser and writes (`build`, `main`). The pure part is then easy to read and to test.
- Don't change an argument in place unless the function's name says so; return a new value. That includes adding a column to a DataFrame the caller passed in.
- Make a boolean parameter keyword-only (`*, force: bool = False`), so the call reads `force=True`, not a bare `True`.
- Keep the argument list short and related. Several values that always travel together become one frozen dataclass.
- Make the result clear: the docstring says what `None` or an empty result means.

### 4.1 Phases

Order a function the way a reader expects, and use only the phases it needs:

1. check the inputs or preconditions;
2. load or obtain the data;
3. do the main work;
4. check or reconcile the result, when needed;
5. return or write the result.

The usual phases per package:

- scrapers: open → wait → parse → validate → write;
- stage builders in `features/`: load → derive → write;
- runners in `analysis/` and `ml/`: load → compute → print;
- tests: arrange → act → assert.

## 5. Blank lines

Blank lines show the structure of a function. They separate phases; they don't decorate.

- One blank line between two phases of a function.
- Keep the lines of one phase together: several fields read from one row, counters set together.
- A blank line after a guard block (`if not ids: return`), before the work it guards.
- A blank line before and after a loop, `with` or `if` block that is a phase of its own.
- An accumulator stays attached to its loop: no blank line between `total = ...` and the `for` that fills it.
- A comment that introduces a phase gets a blank line above it, and none below.
- One blank line, never two. None directly after a `def`, `if` or `for` line (the formatter removes it anyway).
- Not after every statement: a blank line marks the end of a phase.

Before you finish a function, look at it as a whole and add the missing breaks. A heuristic, not a rule: a function of about six lines or fewer rarely needs one.

From `features/engine.py`, with descriptive names (docstring shortened):

```python
def _h2h_ht_goals_avg(matches_df: pd.DataFrame) -> "pd.Series[Any]":
    """Mean total half-time goals in past meetings of this fixture."""
    total = pd.Series(0.0, index=matches_df.index)
    seen = pd.Series(0.0, index=matches_df.index)
    for slot in range(1, MATCHES_PER_SECTION + 1):
        home_goals = _block(matches_df, "h2h", slot, "ht_home_goals")
        away_goals = _block(matches_df, "h2h", slot, "ht_away_goals")
        both_known = home_goals.notna() & away_goals.notna()

        total += (home_goals.fillna(0) + away_goals.fillna(0)).where(both_known, 0.0)
        seen += both_known.astype(float)

    avg: pd.Series[Any] = pd.Series(
        np.where(seen > 0, total / seen, np.nan), index=matches_df.index
    )
    return avg
```

## 6. Control flow and expressions

- Give a hard condition a name (`both_known = home_goals.notna() & away_goals.notna()`), then test the name.
- Add an intermediate variable when its name explains a step. Don't add one that only repeats an obvious expression.
- No nested conditional expressions (`a if x else b if y else c`): write the branches out.
- When cases behave differently, give each its own explicit branch.
- Don't combine unrelated operations in one statement. Split a pandas chain where the table changes meaning (after a filter, a group-by or a join), and name the new table: `priced_df = matches_df[matches_df["s2_has_odds"]]`. A chain of simple steps on the same table can stay one statement.
- A comprehension is for a plain map or filter: one `for`, at most one `if`, no side effects. Nested loops, several conditions or a long expression go in a normal loop. Never use a comprehension only to fit several lines into one.
- A `lambda` only as a short argument (`key=lambda match: match.kickoff`). A lambda with logic becomes a named function.
- A number someone chose or measured (a threshold, a timeout, a time window) gets a named constant at the top of the module, with a comment that says where it comes from. Tests read such numbers from the code, so they need a name. Plain arithmetic and structural numbers (`0`, `1`, `2` halves, `100` for a percentage) stay inline.

```python
# The first page load of a league can be slow: one took more than the default 20 s on
# 2026-10-06 and loaded within 45 s on the retry. Later clicks keep the default.
FIRST_LOAD_TIMEOUT = 45
```

## 7. Comments and docstrings

A comment explains what the code alone cannot: why.

- **Module docstring.** Every module opens with one: what it does and why it exists. A scraper or a stage builder also says what it reads, what it writes and which `notes/FIELDS/` doc defines its fields. An entry point ends with its command: `Run: uv run python -m features.schedule_row`.
- **Function docstring.** One sentence of plain prose: what the function returns or does, and what `None` or an empty result means (`"""A price or line from the row, None when the page showed none."""`). Add lines only for a rule, a limit or a side effect the reader cannot see. No `Args:` / `Returns:` blocks. A private helper with a clear name needs no docstring.
- **A comment says why, not what:** why this approach, a domain rule, a trap, why the simpler version is wrong. A comment that repeats the next line in English goes.
- **A decision a reader could take for a mistake says it is one, with its date,** in the form the code already uses: `(the user, 2026-10-13)`. **It also names the assumption that makes it right,** so a reader can tell when it stops being right: "kicked off at least 2 h 30 min before this one, so it had surely finished". An ordinary choice needs no such mark.
- **A rule taken from a note cites it,** with the path and the section (`features/CLAUDE.md` §0, `notes/FIELDS/SCHEDULE_2_ROW.md`).
- **A comment describes the code as it is now.** The history of a change goes to `notes/LOG/MIGRATIONS.md`. A date that describes the data stays, because the reader needs it: "files scraped before 2026-09-22 have no such column".
- A banner comment (`# --- Market controls ---`) may group the functions of a long module.
- Change a comment or a docstring in the same change as its code. A wrong comment is worse than none.

## 8. Types and data contracts

- Prefer a precise type. `Any` is for a row of a CSV or a DataFrame (`Mapping[str, Any]`, `dict[str, Any]`), whose columns are defined in `notes/FIELDS/` and `domain/columns.py`.
- `cast` and `# type: ignore[<code>]` are for three cases: a gap in a third-party library, a fake object or a deliberately wrong input in a test, and a fact checked at runtime that the type checker cannot see. Always give the error code, and a comment when the reason is not obvious. Never use them to quiet an error in our own contracts: fix the contract.
- `X | None` only when the value can really be absent, and the docstring says what `None` means. Don't make a value optional to avoid deciding the contract.
- A record with fixed fields is a frozen dataclass (`@dataclass(frozen=True)`), not a dict with fixed keys or a tuple of three or more unnamed values.
- The pydantic models are the contract where page data enters (`domain/schedule.py`). Past them, trust the data until it crosses another boundary that can change it. A CSV write and read is one: it can turn `match_id` into a number, which is why stage files go through `features/stage_io.py`. Don't re-check what a contract already guarantees.
- Related functions return the same shapes.

## 9. Data, domain rules and missing values

- **Each rule has one home. Use it; never re-derive it.**
  - file paths: `domain/paths.py`;
  - times and their order: `domain/clock.py`;
  - per-match facts (comeback, 1X2 result, margin-free probabilities): `domain/stats.py`;
  - column order: `domain/columns.py`;
  - DOM selectors and site hosts: `scrapers/constants.py`.
- **Missing is not failed.** A value the page did not show, such as the odds of an unpriced match, is `None`, or NaN in a DataFrame. Convert between the two at one boundary, in one helper (`features/schedule_row.py:_number`). A failure, such as a page that did not render or a file that does not parse, raises.
- Never fill a missing value with a plausible default (0, `""`, a mean) unless its field doc says so.
- **A function that reads other rows states which rows:** its time window and the rule behind it. A wrong window leaks a result into a row, and that leak passes every gate (`features/CLAUDE.md` §0).
- Don't change the meaning of an existing field or flag. A new meaning is a new field (`notes/FIELDS/`).
- Keep parsing, validation, the domain rule and the writing in separate steps, not in one opaque block.
- No hidden dependence on the order of calls or on module-level mutable state. One exception: a resource that worker threads share, such as the browser pool `_POOL` in `scrapers/detail.py` and `scrapers/goals.py`. It is one module-level object, and the run's entry function opens and closes it with `with`.

## 10. Errors

- Raise a specific exception (`ValueError`, `FileNotFoundError`, `KeyError`) with a message that names the input: the file, the league-season, the match id, the column.
- Re-raise with `raise NewError(...) from exc`, so the cause stays visible.
- Validate where outside data enters (the page: the parsers and the stage-1 models; the config: `scrapers/links.py`; a stage file: `features/stage_io.py`), and trust it inside.
- `except Exception` is allowed in two cases. Around one job of a batch run (one league-season, one match): it logs the traceback (`logger.exception`), records the failure and lets the run go on, and the run exits non-zero at the end (`scrapers/schedule.py:_run_job`). Or to add context and re-raise at once. In both cases a comment says why. Cleanup needs no catch: use `finally` or `with`.
- Never catch an exception to hide it, and never return an empty or zero result for an operation that failed.
- A failing QA check is a finding about the data. Don't soften the check to make it pass (`qa/CLAUDE.md` §2).

## 11. Imports and module boundaries

- Absolute imports, in the layer direction of root `CLAUDE.md`, "Architecture". That a function can be imported does not mean the import belongs in this layer.
- A `_private` name stays in its module. If another module needs it, make it public in the module where it belongs, which may not be the module it is in now.
- No wildcard imports.
- Reuse an existing shared helper. Don't create a new shared module only to avoid a few repeated lines.

## 12. Tests

Tests follow every rule above. What a test may and may not do is in root `CLAUDE.md`, "Quality gates".

- **Name a test as a sentence about the behaviour:** `test_comeback_fields_agree_with_the_kernel`. A property test usually starts with `test_any_` and states its rule for every input: `test_any_three_prices_give_three_chances_that_sum_to_one`.
- One behaviour or invariant per test. Several asserts are fine when together they check that one behaviour.
- **Arrange, act, assert,** with a blank line between them when the test is longer than a few lines.
- Small, explicit test data: a builder with overrides (`_row(ht, ft, **overrides)`), not a chain of fixtures the reader has to trace.
- A value that matters says why: `"2026-01-31 18:30+01:00",  # a Saturday in Berlin`. A constant the project chose is read from the code, not restated.
- Work the expected value out by hand or from an independent rule, never by running the code under test again.
- **Test the edges no gate sees:** a time window at its exact cut-off and just past it (`tests/domain/test_scope.py`), and a value that can be missing, with it missing (`None`, or NaN in a DataFrame). A wrong edge leaks a result into a row; a wrong fill breaks §9. The window is read from the code, like any project constant.
- In a loop over cases, the assert message names the case: `assert ..., (ht, ft)`.
- Hypothesis: keep the strategies small and named at the top of the module (`_PRICES`). Never weaken a property to make it pass.

## 13. Changing existing code

Before:

- Read the function, its callers and its tests.
- Look for an existing helper or home for the rule (§9).

During:

- Change only what the task needs: no refactor, rename or reformat outside the functions you change (§1).
- Tests ship in the same change (root `CLAUDE.md`).
- Update the comments and docstrings the change makes wrong.

After:

- Read each changed file as a whole, not only the diff, for readability as well as correctness.
- Remove what the change left unused: dead branches, variables, debug prints, stale comments.

## 14. Checklist

- [ ] Names say what the data is, in the project's words. One-letter names only `i`, `_` and a one-line comprehension; a DataFrame's name ends in `_df` (`df` alone only in an any-table helper).
- [ ] Each function has one job, its guards first, its phases separated by one blank line.
- [ ] No dense expression where named steps read better.
- [ ] Comments say why; docstrings say what comes back and what `None` means; none is stale.
- [ ] Each rule comes from its home (§9); missing values and failures are handled on purpose.
- [ ] Errors are specific and name the input; no broad `except` outside the two cases of §10.
- [ ] Tests read as sentences, follow arrange / act / assert, and work out their expected values independently.
- [ ] No unrelated change rode along.
- [ ] Each changed file was read as a whole.
