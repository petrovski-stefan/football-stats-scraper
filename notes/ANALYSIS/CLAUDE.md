# notes/ANALYSIS/ — results of methods run on the corpus

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

The rule of this group: Claude writes a doc from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

A doc runs again only when the corpus changes (a league is added or removed) or its method changes (the user, 2026-10-19). The corpus line in its header tells which corpus its numbers come from.

## 1. What goes here

- One doc for each method, run on one scope of the data. Example: `SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`.
- The numbers come from a runner in the `analysis/` package. The runner only prints. Claude reads the output and writes the doc (`analysis/CLAUDE.md`).
- Every claim here is exploratory. A test of a claim, with its preregistration, goes to `notes/RECORD/`.
- Concepts with invented numbers go to `notes/REFERENCE/`. Project numbers go here.

## 2. The tree

A path has four parts: source, scope, level and method. Example: `SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`.

### Source

The top folder names the sources of the fields that the runner uses:

| folder | the runner uses fields of |
|---|---|
| `SCHEDULE/` | the schedule (code `s`) |
| `SCHEDULE_DETAIL/` | the schedule and the detail page (codes `s`, `d`) |
| `SCHEDULE_LIVE/` | the schedule and the live page: goals and events (codes `s`, `l`) |
| `SCHEDULE_DETAIL_LIVE/` | all three sources |
| `DETAIL/`, `LIVE/`, `DETAIL_LIVE/` | no schedule fields |

1. The code of each field that the runner uses gives the folder (`notes/FIELDS/README.md`, rules for values, rule 2). The sources are in the fixed order schedule, detail, live.
2. The lineage of a field does not count. Example: live stage 3 makes its aggregates from the detail history rows. But a runner that uses only `s` and `l` fields gives a `SCHEDULE_LIVE` doc.
3. The corpus of a combination is the matches that are in each source that it reads, joined on `match_id`. A match that a source does not have is coverage, not a filter. The corpus line gives the count for each source.
4. The results are in the schedule file. So an analysis of outcomes always includes `SCHEDULE`.
5. A folder without the schedule (`DETAIL/`, `LIVE/`) describes its source, on the matches of that source. The live store also holds history matches that are not in the schedule corpus.
6. Today only the schedule is in the staged pipeline. The other folders start when plan steps P4–P6 (`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`) make their stage-3 files.

### Scope

`WHOLE_CORPUS/` holds runs on every match of the source, with no filter that the analyst chose. `NOT_WHOLE_CORPUS/` comes later: one folder for each named filter, with the same tree inside.

### Level

Inside a scope, there is one folder for each level (the user, 2026-10-18):

| folder | level | its values shrink toward |
|---|---|---|
| `ALL/` | all matches together | — |
| `PER_LEAGUE/` | a league, with its seasons together | all matches |
| `PER_TEAM/` | a team in one league, with its seasons together | its league |

1. A team plays in one league in each season. A team that changes league (promotion or relegation) gives two units, one in each league.
2. Read each level against the level above it: a league against all matches, a team against its league.
3. A folder starts with its first doc.
4. Each doc has the name of its method, for example `SHIN.md`. The same method in two folders gives two docs. Cite a doc by its path.
5. The runner of a doc has the same path in lowercase: `analysis/schedule/whole_corpus/all/shin.py`.

### Slices

A slice divides the matches of a level by season, by stage or by round. A slice is a section in the doc of its level. It never gets a folder.

| level | per season | per stage | per round |
|---|---|---|---|
| `ALL/` | the season cohorts (§5, rule 2) | no | season phase; clusters |
| `PER_LEAGUE/` | league-season | only if the league keeps more than one stage | no |
| `PER_TEAM/` | team-season: the repeat test | no | no |

- **League-season:** does a league change between its seasons by more than noise? Use one test for all leagues.
- **The repeat test:** does the first season of a team predict its second? A claim that a team trait exists needs this test, because a value for one season includes the match that it would predict.
- **Stages:**
  - one after the other (Apertura, then Clausura): compare the stages;
  - side by side (Group A and Group B, East and West): read each group as a small league;
  - a knockout stage (playoffs, finals) is not a slice. Today no league keeps one.
- **Per round** (the user, 2026-10-18):
  - season phase: the round as a share of the season, because leagues play different numbers of rounds;
  - clusters: do comebacks or 7+ matches collect in one round of a league? The league-season and the odds also make clusters, so compare with them.
- **No other slices.** A team plays one match in each round. In groups side by side, the group of a team is its season. In stages one after the other, a team has only part of its season. A league has too few comebacks in each part of a season.
- A breakdown by a variable (a price band, a goal total, home or away) is a section too. It never gets a folder.

### The card

A doc that tells how often comebacks or 7+ matches occur gives the card of its level:

- **Comebacks:** the rate; how often a team is behind at half-time, and how often it then wins; the count against the count that the odds expect.
- **7+:** the rate; the mean goals in each half; the count against the count that the O/U line expects.
- **At `PER_TEAM/`:** give the comebacks in the matches of the team, then the two roles, each at home and away. The team comes back: it is behind at half-time and wins. The team loses a lead: it leads at half-time and loses. Give each value for the team, and against its league. For 7+, use the goals that the team scores and concedes. One team has too few 7+ matches.
- **At `ALL/` and `PER_LEAGUE/`:** split by home team and away team, not by role. Each comeback has one team in each role, so the two role counts are equal by definition.

## 3. Workflow

1. Select the method and the folder.
2. Find the kind of each question: definitional, structural or empirical (`notes/REFERENCE/MARKET_COMEBACKS.md` for comebacks). A definitional fact gets no doc.
3. Write or extend the runner in `analysis/`. It prints and writes no file. Its mechanics get tests.
4. Run it.
5. Audit the output (§5).
6. Write the doc from the template (§4).
7. Report to the user, with one line for each claim. The user can strike a claim.
8. A claim goes into `notes/WORKING/STATE.md` only with the user's go.
9. A preregistered test of a claim goes to `notes/RECORD/`. The claim then gets the status `tested`, with a link to that note.

## 4. The doc template

- The title: `# <METHOD> — <scope in words>`.
- The header line of the group, then the STE line.
- A header block:
  - **Scope:** the folder path below `notes/ANALYSIS/`;
  - **Sources:** each source that the runner reads, at stage 3, with the role of its fields: inputs (known before kickoff) and outcome;
  - **Corpus:** the corpus line that the runner prints;
  - **Code:** the command, at the commit that adds or changes the doc;
  - **Kind:** structural or empirical.
- **Question:** one or two lines.
- **Claims:** a table with the columns id (C1, C2, …), claim, number with its interval, n, both seasons, and status.
  - An id never changes.
  - If a claim stops being true, its row stays, with the date and the reason.
  - The status is `exploratory`, or `tested` with a link to the Record note.
- **Method**, then **Caveats**: the number of looks, data that two sides share, and the assumptions of the yardstick.

## 5. Honesty rules

1. **Many units, one test.** A doc about many units (leagues, league-seasons, teams) gives one heterogeneity test and Empirical-Bayes-shrunk values (`notes/REFERENCE/STATS_PRIMER.md` §1). It never says that one unit is different because of a test of that unit alone. Per-league testing is Dead in `notes/WORKING/STATE.md`. A ranked table uses the shrunk values, and it gives the luck line: the top of the table if all units were the same.
2. **Both seasons.** Each claim about all matches tells if it is true in both season cohorts. This is a description, not a replication: both cohorts were seen.
3. **Yardstick first.** A claim "beyond the odds" names its yardstick. It also tests the assumptions of that yardstick: calibration by team strength, by league and by expected total, and its one first-half share.
4. **Audit.** Each number in a doc is in the printed output. Check each correlation for data that both sides share. A difference that a method makes by its construction is not a finding.
5. **Intervals.** The matches of one league-season are not independent. An interval for a mean over matches resamples league-seasons (`analysis/stats.py:cluster_bootstrap_ci`).
6. **Inputs come before kickoff.** A match's own goals, events and in-play odds describe its outcome. They are never an input for that match (`notes/FIELDS/README.md`, the timing rule).
7. **One match, two teams.** A match is in two team units: its home team and its away team. A test at `PER_TEAM/` counts each match one time. Use a model with an effect for each of the two teams.
8. **A repeat can come from the yardstick.** Team strength repeats from one season to the next, and so do league margins (`PER_LEAGUE/SHIN.md`, C1). An error of the yardstick by strength or by league repeats with them, and it looks like a trait. So test the calibration of the yardstick (rule 3) before a repeat test.

## 6. Before a proposal, and the candidate protocol

**Moved from `modelling/CLAUDE.md` on 2026-10-18,** when `modelling/` was deleted. Its run-record rule and its section on `scoreline.py` did not move (`notes/LOG/MIGRATIONS.md`).

### Read first

Before you propose a model, a feature, a filter or a rule, read `notes/WORKING/STATE.md`. The measured failures of the project are in the notes that it points to. Most "new" ideas were tested already.

### The holdout

The 2025-26 season cannot be a holdout. Its outcomes informed many analyses (`notes/RECORD/PREREGISTRATION.md` A9). The `--holdout` mode that opened it was deleted on 2026-10-02. The next confirmatory test needs a new holdout, as A9 tells: a confirmatory set that a dated amendment declares before its scrape starts.

### The candidate protocol

1. Judge a rule by its precision in the top N, with a Wilson interval and the lift. Do not judge it by AUC or by the Brier score. A rule can have a large lift in a small top-N set and an AUC near chance.
2. First, screen each candidate rule against the market price, with no outcomes. A rule that has no relation to the market has no relation to the best known signal.
3. For a history-block feature, do the reliability screen before steps 1 and 2 (`features/CLAUDE.md` §5).
4. Test a claim as `notes/RECORD/PREREGISTRATION.md` tells: a closed family list, the Holm correction, one opening of the holdout, and amendments with dates.

### Screening bars (set 2026-09-28, before use)

The bars were set before any new feature was screened against them. Both screens use no outcomes. Apply both bars mechanically, with no judgement. **A change to a bar needs a dated entry in the amendment log of `notes/RECORD/PREREGISTRATION.md`.**

**The market-orthogonality values are provisional.** Both bars, and how to read "the market price", are open in `notes/WORKING/DECISIONS.md` (D1–D4). Apply them as written until those decisions close. The low bar does not apply to the stake fields S3.11–13 (D8, closed).

- **Reliability** (history-block features only): use the Spearman–Brown value at depth 6, not the raw split-half (A9.4). Kill below 0.10. Otherwise pass, and report the value against the reference table in `features/CLAUDE.md` §5.
- **Market orthogonality:** a bar on the size of the effect, not a significance test. Take |r| between the score of the candidate and the market price before kickoff. Kill below 0.05 (no signal). Kill as redundant above 0.80 (the market already has it). Pass between the two. Report the interval for information only.

### Binding rules

- **Stratify by league. Never test per league.** Pool with Mantel–Haenszel over league-season strata.
- The retry list for the multi-country scrape is closed (`notes/RECORD/RETRY_CANDIDATES_2026-09-23.md`). Do not add claims to it after the data arrives.
- Before you propose a new pre-match comeback feature, read `notes/RECORD/RESULTS.md` and `notes/RECORD/FILTER_RESULTS.md`.
