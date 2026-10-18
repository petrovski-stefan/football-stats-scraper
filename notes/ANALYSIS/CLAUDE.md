# notes/ANALYSIS/ — results of methods run on the corpus

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

The rule of this group: Claude writes a doc from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

## 1. What goes here

- One doc for each method, run on one scope of the data. Example: `SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`.
- The numbers come from a runner in the `analysis/` package. The runner only prints. Claude reads the output and writes the doc (`analysis/CLAUDE.md`).
- Every claim here is exploratory. A test of a claim, with its preregistration, goes to `notes/RECORD/`.
- Concepts with invented numbers go to `notes/REFERENCE/`. Project numbers go here.

## 2. The tree

The tree has four levels: source, scope, unit and method. Example: `SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`.

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

### Unit

Inside a scope, there is one folder for each unit of the corpus:

| folder | unit |
|---|---|
| `ALL/` | all matches together |
| `PER_SEASON/` | the two season cohorts |
| `PER_CONTINENT/` | continent |
| `PER_COUNTRY/` | country |
| `PER_LEAGUE/` | league, with its seasons together |
| `PER_LEAGUE_SEASON/` | league-season |
| `PER_STAGE/` | stage name (League, Apertura, Clausura, …) |
| `PER_LEAGUE_SEASON_STAGE/` | each stage of each league-season |
| `PER_TEAM_SEASON/` | team in one league-season |

- A unit folder is a unit of the corpus. A breakdown by a variable (a price band, a goal total, a round) is a section inside a doc. It never gets a folder.
- A folder starts with its first doc.
- Each doc has the name of its method, for example `SHIN.md`. The same method in two folders gives two docs. Cite a doc by its path.
- The runner of a doc has the same path in lowercase: `analysis/schedule/whole_corpus/all/shin.py`.

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
  - If a claim stops being true, its row stays, with the run that changed it.
  - The status is `exploratory`, or `tested` with a link to the Record note.
- **Method**, then **Caveats**: the number of looks, data that two sides share, and the assumptions of the yardstick.
- **Runs:** a table with the date, the corpus and the change.

## 5. Honesty rules

1. **Many units, one test.** A doc about many units (leagues, league-seasons, countries, teams) gives one heterogeneity test and Empirical-Bayes-shrunk values (`notes/REFERENCE/STATS_PRIMER.md` §1). It never says that one unit is different because of a test of that unit alone. Per-league testing is Dead in `notes/WORKING/STATE.md`.
2. **Both seasons.** Each claim about all matches tells if it is true in both season cohorts. This is a description, not a replication: both cohorts were seen.
3. **Yardstick first.** A claim "beyond the odds" names its yardstick. It also tests the assumptions of that yardstick: calibration by team strength, by league and by expected total, and its one first-half share.
4. **Audit.** Each number in a doc is in the printed output. Check each correlation for data that both sides share. A difference that a method makes by its construction is not a finding.
5. **Intervals.** The matches of one league-season are not independent. An interval for a mean over matches resamples league-seasons (`analysis/stats.py:cluster_bootstrap_ci`).
6. **Inputs come before kickoff.** A match's own goals, events and in-play odds describe its outcome. They are never an input for that match (`notes/FIELDS/README.md`, the timing rule).
