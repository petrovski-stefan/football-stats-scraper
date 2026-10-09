# scrapers/ — Selenium scraping of nowgoal26

Only this package may write to `data/raw/` and `data/finished/1_raw/`. All DOM selectors live in `scrapers/constants.py`.

**Every navigation goes through `driver.open_page(driver, url)`; never call `driver.get` anywhere else.** `open_page` refuses, before any request, a URL on a host missing from `constants.ROBOTS_DISALLOW` and any path that host's robots.txt disallows. The page's own background loads (its scripts, its `/Ajax/` calls) are not checked: the rule covers the pages we choose to open. The user decided this on 2026-10-02 after a measurement: with those paths blocked as well, the h2h page never rendered and the live page showed 0 goals and 0 events. **Every driver comes from `driver.get_driver()`**, which gives it one `fake-useragent` string (Chrome, desktop) for its whole life. To open a new host, add its robots.txt rules to `ROBOTS_DISALLOW` first.

## 1. Scrape flow (league schedule, first stage)

`schedule.scrape_all()` → `links.get_league_seasons()` loads and validates `config/leagues.json` and returns one job per enabled season (URL, season, league id, `keep`) → `schedule.scrape_league()` opens headless Chrome (`driver.get_driver()`) and renders the page. `schedule._resolve_stages()` matches the page's stage tabs against `keep`. A page without tabs gets one pass and `stage` is `""`. Otherwise there is one pass per kept tab, in page order. Each tab is clicked (`driver.click_stage`). A kept stage missing from the page logs a warning. If the config's shape does not match the page (tabs but nothing kept, or kept stages but no tabs), it logs an error and scrapes nothing. **Per stage pass, the final table is read once first** (`schedule._read_final_table`): the standings are pointed at that stage's sub-table (`driver.sync_standings_to_stage`), the `Total` view is checked (`driver.show_total_standings`) and `parsers.parse_final_table()` reads every team's line. Then the pass iterates its rounds `1..current`, clicking each round span (`driver.click_round`, scoped to the stage; `WebDriverWait`, not `sleep`) and parsing each `div.schedulis` match with `parsers.parse_schedulis_row()`. Rows are validated by the stage-1 models (`domain/schedule.py:ScheduleRow`, `FinalTableRow`) and written by `scrapers/csv_io.py:save_unless_shrinking()` to `data/finished/1_raw/<country>_<league>_<season>_schedule.csv` and `_final_table.csv`, where `<country>` is the config's country and `<league>` the league's name in the page's title, which can leave the country out; a name that already starts with the exact country keeps it once, so `england_championship` but `england_english_premier_league` (`csv_io.league_slug`, 2026-10-08) (column order from `domain.columns.SCHEDULE_RAW_COLUMNS` / `FINAL_TABLE_COLUMNS`). Every field is defined in `notes/fields/schedule_1_raw.md`.

**Choosing what to scrape** (`scrapers/links.py:Selection`, hardened 2026-10-07 for multi-league runs): with no option, the `enabled` seasons of the config; `--leagues "ENG LCH,SCO PR"` (config codes) or `--all` ignore the flags; `--before-year 2026` keeps only seasons that started before 2026; `--list` prints the jobs and opens no page. An unknown code is an error. **A run is safe to leave alone:** one league failing is logged with its traceback and the run goes on (`schedule._run_job`); a league-season already in a stage-1 file is skipped, read from the file's own `s1_league_id` and `s1_season`, not its name (`--force` redoes it); the first page load waits `FIRST_LOAD_TIMEOUT` (45 s; one load took more than 20 s on 2026-10-06); **`WORKERS` (4) league-seasons run at once** (2026-10-08), each in its own Chrome and its own files, and each worker pauses `PAUSE_BETWEEN_JOBS` (12 s since 2026-10-08) between leagues; every log line carries the league-season it comes from (`[ENG LCH 2024-2025]`, the worker thread's name); Ctrl+C drops the jobs not yet started and lets the running ones finish; output is UTF-8, so a run logged to a file holds every league name (the Windows code page cannot write every character a name can hold); the summary lists failures and exits 1 if there were any, so re-running the same command picks up only what is missing. **The scraper knows leagues and seasons, never the research protocol** (the user, 2026-10-07): which seasons are DEV or CONFIRM is decided in the command, not in this package.

**The standings are not scraped per round any more** (the user, 2026-10-06): the page's `Round N` table counts by round number, so it can hold results played after a match. Stage 3 rebuilds the table at each kickoff (`features/schedule_multi.py`); the page's final table is only the check.

## 2. DOM facts (nowgoal26)

- Only one round renders at a time (`div.round span[round=N]`); the live round has class `current on`.
- **Stage tabs** (`div.stage span[stage=<id>]`, e.g. League / Group A / Apertura) appear only on multi-stage or single-"League" pages. A single-table page has an empty `div.stage`, and its round spans have no `stage` attribute. The tab on screen has class `on`. Clicking another tab shows that stage's current round.
- **Every round-bearing stage's round spans are in the DOM at once**, each tagged `stage=<id>`, with the inactive stages' spans `display:none`. Each stage has its own `current`. An unscoped `span[round=3]` matches the first stage's round 3. Measured 2026-10-01: Liga MX has Apertura 1–17 and Clausura 1–17 side by side. So round reads and clicks are scoped `span[stage=<id>][round=N]`.
- Each match row carries `@matchid`, `@score`, `span.ht` (half-time), `span.date[data-t]`.
- **`span.date[data-t]` is UTC+8 (China time), with no offset written** (`constants.LEAGUE_PAGE_CLOCK`; verified 2026-10-05 on a winter and a summer EPL kickoff). `parsers.parse_kickoff` converts it to Berlin time; every schedule file before 2026-10-06 stored it unconverted.
- Standings are at `ul#standingList li.standlis`, under a title row `li.title` (R, Team, P, W, D, L, GD, PTS). Each row has eight `span` children in that order, the counts nested inside (`<span><span>26</span></span>`, `<b>85</b>`). The dropdown lists `Total` (`li[data-st-r="0"]`, the table now) and one entry per finished round (`li[data-st-r=N]`); `Round N` counts by round number, whenever a match was played (tested 2026-10-06). The page opens on `Total`. Measured 2026-10-06.
- A first page load once took more than the default 20 s to show the round buttons (2026-10-06); the retry loaded within 45 s.
- **The standings have their own sub-table picker**, `#subStandingBox li[data-s-sub=<stage id>]`. It is keyed by the same id as the stage tab, and `#standingBox[data-st-sub]` shows which sub-table is on screen. **It does not follow the stage tabs and opens on the latest sub-table.** Measured 2026-10-01: Liga MX opens the Apertura schedule beside the Clausura table. Scottish Premiership opens the League schedule beside the 6-team Championship Group (12 teams after the switch). Picking a sub-table resets the round dropdown to "Total". If a stage's sub-table can't be shown, it gets no final table, never another stage's.

## 3. Parsers return primitives

`parsers.parse_schedulis_row()` and `parsers.parse_final_table()` return **only values read from the page**, parsed and nothing computed (stage 1). Where new extraction vs new arithmetic belongs: `domain/CLAUDE.md` §1.

## 4. Row semantics

- Only **finished** matches are emitted — `parsers.parse_schedulis_row()` returns `None` when HT+FT scores don't both parse as `int - int`, so unplayed/live rows are skipped. Unplayed rows belong to `data/scheduled/`, later.
- **`s1_stage` is the clicked tab's name** (`"League"`, `"Group 2"`, `"Clausura"`), or `""` on a page without tabs. All kept stages of a league-season go into one CSV. **Rounds restart at 1 in each stage**, so a round is identified by (`stage`, `round`), never by `round` alone. Downstream code that orders by `round` alone is not safe for a league-season with more than one kept stage: `notes/DECISIONS.md` D7.
- **Position within a round** is a stage-3 field now (`s3_match_index_in_round`, `features/schedule_multi.py:round_positions`), counted over the round's finished matches. The scraper used to assign it over every scheduled row, unplayed ones included; the finished tree holds no unplayed rows (plan Q1).

## 5. Odds

- **Odds come in three flavours, one pass each.** The schedule odds column is a single three-cell widget (`ROW_ODDS_CELLS`) whose meaning depends on the header selectbox, so `driver.switch_odds_type(driver, kind)` clicks `li[type='...']` and the choice persists across round clicks. `scrapers/constants.py:ODDS_TYPES` maps our name to the DOM type and the header label it must show afterwards: `1x2` → `O` (home/draw/away), `ah` → `L` (home/**line**/away), `ou` → `T` (over/**line**/under). `scrapers/schedule.py` scrapes 1X2 first, then loops the secondary types and switches back.
- The switch is verified, not assumed — it returns `False` if the header label never changes, and a repaint guard waits for the first row's odds to actually change.
- **A market the match does not carry keeps the previous market's numbers after the switch** (found 2026-10-08: 97 rows in 8 league-seasons stored their 1X2 prices as O/U and AH, one stored its AH as 1X2; never a whole round). `schedule.drop_stale_odds` empties every market whose three cells repeat another market's. Files scraped before that day still hold such rows until they are re-scraped.
- Missing odds parse to `None`, and every odds field on `domain/schedule.py:ScheduleRow` is nullable (stage 2 turns that into `s2_has_odds` / `s2_has_ou_odds` / `s2_has_ah_odds`).
- **The schedule's odds are the opening prices** (`s1_odds_<market>_open_*`): its O/U and AH equal Bet365's "Initial" row on the detail page for the reference match.
- **For AH and O/U the informative column is the line, not the price.** nowgoal moves the handicap/goal line and holds both prices near 1.90, so `s1_odds_ah_open_line` and `s1_odds_ou_open_line` carry the signal and `s2_implied_over` / `s2_implied_ah_home` are only the tilt around it.
- `parse_line()` handles split quarter-lines, where nowgoal hangs one minus sign off whichever half it reaches first so the sign belongs to the whole expression (`0/-0.5` → -0.25, `-1/1.5` → -1.25).
- **Positive `ah_line` means the home side is favoured and gives the handicap — the opposite sign to football-data.co.uk's `AHh`**, so any comparison against that source has to flip one of them.

## 6. Detail enrichment (second stage)

`scrapers/detail.py` scrapes each finished match's detail page (`https://live11.nowgoal26.com/match/h2h-<match_id>` — same id as the schedule row) into **one wide feature row** per match.

- `scrape_match_detail(driver, match_id)` is **mode-agnostic** (a future prediction mode can feed upcoming ids).
- `enrich_finished(limit)` reads ids from `data/raw/*.csv` and is **resumable** — it skips ids already in `data/raw/<league>_detail.csv` and appends incrementally.
- It runs a **`ThreadPoolExecutor` of `WORKERS = 3`**, each thread holding its own Chrome for the whole run (a Selenium session is not thread-safe to share); a lock serialises the CSV appends.
- Detail is ~1 page render **per match** (heavy: ~380/season) — always run it resumable, not from scratch.
- The scraper writes **nothing but that detail file**. Joining it to the base CSV is `features/enrich.py` (see `features/CLAUDE.md`).

`scrapers/detail_parsers.py` parses each section:

- `parse_odds_1x2` — Bet365-or-first 1X2, initial+live; the 1X2 cells are `td[data-e="1"]`.
- The H2H widget tables `tr[id^='tr1_'/'tr2_'/'tr3_']` (v1=home recent, v2=away recent, v3=H2H). The score span class is indexed per table, so match on prefix `span[class^='fscore']`. Each row is 15 cells — league/date/teams/score/**corner**/1X2 odds.
- Those rows feed two outputs: **aggregates** (`aggregate_recent`/`aggregate_h2h` → `*_recent_*`, `h2h_*`) and **per-match column blocks** (`flatten_history` → `home_lastN_*`/`away_lastN_*`/`h2h_lastN_*`, last1 = most recent, `N` up to `domain.columns.MATCHES_PER_SECTION`, oriented to the section's subject team).
- Plus best-effort strength/guess/standings/fixtures.

Aggregate/odds fields are validated by `domain/match_detail.py:MatchDetail`; the per-match blocks are merged in as plain data. Full column order (incl. generated per-match names) comes from `domain.columns.DETAIL_ORDERED_COLUMNS` / `domain.columns.per_match_columns()`.

## 7. Live-page events: goals, cards, substitutions (fourth stage)

`scrapers/goals.py` scrapes each match's **live** page (`https://live11.nowgoal26.com/match/live-<match_id>`) — a _different_ page from the h2h detail page, same match id. One render fills two stores: `data/raw/goals.csv` (`domain/goal.py`, one row per goal) and `data/raw/events.csv` (`domain/event.py`, yellow/red cards and substitutions).

### Goals are identified by the running score, never by the icon

Measured on live pages 2026-09-22: an open-play goal carries `1.png` (alt "Goal") but a penalty carries `7.png` (alt "Penalty Scored"), so an icon whitelist silently drops every penalty. Chelsea 2-0 Fulham (match 2789151, re-measured 2026-09-28) shows both: a `1.png` Goal at 45+8' and a `7.png` Penalty Scored at 56' — an icon whitelist would keep the first and drop the second, recording 1-0. Pogon 0-3 Lech shows the running score jumping 0-1 to 0-3 for the same reason.

The running score is strictly better: goal and penalty rows both carry it, VAR rows ("Goal Disallowed", "Goal awarded") never do, and it identifies the scoring side by which number advanced — which also handles own goals without knowing their icon. The icon's `alt` is still stored as `kind`, but is never used to decide whether a row is a goal.

Confirmed rather than assumed: measured on 12 live pages 2026-09-23, the page carries exactly eight event types, and **exactly the three score-carrying ones are goals** — `1.png` Goal, `7.png` Penalty Scored and `8.png` Own Goal — against `3.png` Yellow Card, `2.png` Red Card, `11.png` Substitution and `14.png` VAR, none of which ever carry a running score.

`minute` and `stoppage` are stored as separate fields; why is in `qa/CLAUDE.md` §4.

### The event row: five cells, minute in the middle

`td[0]` home content, `td[1]` home icon, `td[2]` `b.score` minute, `td[3]` away icon, `td[4]` away content. Two things follow, both in `scrapers/live_rows.py`, which both parsers share so they cannot drift:

- **Side comes from which half of the row is populated**, not from where the name falls in the row text (a home event reads "Chukwueze S. 4 - 5 78'", an away one "90+4' Cherki R.").
- **The event's icon is the one beside the minute**, not the first `<img>` in the row. Taking the first image names the same substitution "Sub in" on one side and "Substitution" on the other, purely because the content cell precedes the icon cell on one side and follows it on the other. That artefact is what made an early probe report 47 "Sub in" and 43 "Substitution" events.

A substitution is **one** row: `11.png` in the icon cell, with `4.png`/`5.png` marking the two players inside the content cell.

Side is not how a goal is attributed — a goal is attributed by which running score advanced, and an **own goal** is exactly the case where the two disagree, since it renders on the scorer's side but credits the opponent.

### Player names: stored for events, not for goals

Deliberate. A goal de-duplicates exactly on its running score, which is unique within a match. A card has no such key, and two players on the same side can be booked in the same minute, so collapsing on (minute, side, kind) alone would silently merge them. The names make the de-duplication key exact.

### The store is global, not per league-season

A fixture's history references cup ties, European games and other leagues, so a referenced match belongs to no single league-season file — and the dedupe that makes the scrape affordable only works across all of them. The key is the nowgoal match id. `domain/paths.py:goals_path()` / `goals_done_path()` own both filenames; this is the one documented exception to the `<league>_<season>_*` naming scheme.

### Two attempt logs are the resume key

- **`data/raw/goals_done.csv` is the resume key, not `goals.csv`.** A 0-0 match produces zero goal rows, so deriving "already scraped" from the goal store would re-fetch every goalless match on every run, forever. The attempt log records one row per _attempted_ match with its goal count.
- **`goals_done.csv` and `events_done.csv` are separate**, which is what let the events store be added to a corpus already fully scraped for goals: such a match is fetched exactly once more, writes only the store it is missing, and is then done for both.

### The work list

The union of the corpus and the history blocks, **deduplicated across leagues before any fetch**. History rows carry the referenced match's own id and league id in the `index` and `name` attributes (`HIST_MATCH_ID_ATTR` / `HIST_LEAGUE_ID_ATTR`); these are flattened into `*_lastN_match_id` / `*_lastN_league_id`. **Detail files scraped before 2026-09-22 have neither column**, so `scrapers.goals` finds no history ids until detail is re-scraped. Measured scale: 17.8 references per match, ~14 still new by the twentieth page, 48% already corpus matches.
