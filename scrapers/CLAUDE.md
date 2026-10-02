# scrapers/ — Selenium scraping of nowgoal26

Only this package may write to `data/raw/`. All DOM selectors live in `scrapers/constants.py`.

## 1. Scrape flow (league schedule, first stage)

`schedule.scrape_all()` → `links.get_league_seasons()` loads and validates `config/leagues.json` and returns one job per enabled season (URL, season, league id, `keep`) → `schedule.scrape_league()` opens headless Chrome (`driver.get_driver()`) and renders the page. `schedule._resolve_stages()` matches the page's stage tabs against `keep`. A page without tabs gets one pass and `stage` is `""`. Otherwise there is one pass per kept tab, in page order. Each tab is clicked (`driver.click_stage`), and the standings are pointed at that stage (`driver.sync_standings_to_stage`). A kept stage missing from the page logs a warning. If the config's shape does not match the page (tabs but nothing kept, or kept stages but no tabs), it logs an error and scrapes nothing. Each pass iterates its rounds `1..current`. For each round it clicks the round span (`driver.click_round`, scoped to the stage) and syncs the standings dropdown to the same round (`driver.sync_standings_to_round`) — both use `WebDriverWait`, not `sleep`. It parses `driver.page_source` with BeautifulSoup: `parsers.parse_standings()` builds a `{team_id: rank}` map, `parsers.parse_schedulis_row()` extracts each `div.schedulis` match. Teams are matched to standings **by team id** (`toTeam('<id>')`), not by name. Rows are validated by the `Match` model (`schedule._validate`) and written by `scrapers/csv_io.py:save_df_to_csv()` (column order from `domain.columns.ORDERED_DF_COLUMNS`).

## 2. DOM facts (nowgoal26)

- Only one round renders at a time (`div.round span[round=N]`); the live round has class `current on`.
- **Stage tabs** (`div.stage span[stage=<id>]`, e.g. League / Group A / Apertura) appear only on multi-stage or single-"League" pages. A single-table page has an empty `div.stage`, and its round spans have no `stage` attribute. The tab on screen has class `on`. Clicking another tab shows that stage's current round.
- **Every round-bearing stage's round spans are in the DOM at once**, each tagged `stage=<id>`, with the inactive stages' spans `display:none`. Each stage has its own `current`. An unscoped `span[round=3]` matches the first stage's round 3. Measured 2026-10-01: Liga MX has Apertura 1–17 and Clausura 1–17 side by side. So round reads and clicks are scoped `span[stage=<id>][round=N]`.
- Each match row carries `@matchid`, `@score`, `span.ht` (half-time), `span.date[data-t]`.
- Standings are at `ul#standingList li.standlis` with a per-round dropdown `li[data-st-r=N]`.
- **The standings have their own sub-table picker**, `#subStandingBox li[data-s-sub=<stage id>]`. It is keyed by the same id as the stage tab, and `#standingBox[data-st-sub]` shows which sub-table is on screen. **It does not follow the stage tabs and opens on the latest sub-table.** Measured 2026-10-01: Liga MX opens the Apertura schedule beside the Clausura table. Scottish Premiership opens the League schedule beside the 6-team Championship Group (12 teams after the switch). Picking a sub-table resets the round dropdown to "Total". If a stage's sub-table can't be shown, its positions are written empty, never taken from another table.

## 3. Parsers return primitives

`parsers.parse_schedulis_row()` returns **only scraped primitives** — no derived values. Where new extraction vs new arithmetic belongs: `domain/CLAUDE.md` §1.

## 4. Row semantics

- Only **finished** matches are emitted — `parsers.parse_schedulis_row()` returns `None` when HT+FT scores don't both parse as `int - int`, so unplayed/live rows are skipped.
- Standings positions are cumulative **as of the round being scraped** (dropdown synced per round), and come from **that stage's own table**: a group's table, or the Apertura table for an Apertura match.
- **`stage` is the clicked tab's name** (`"League"`, `"Group 2"`, `"Clausura"`), or `""` on a page without tabs. All kept stages of a league-season go into one CSV. **Rounds restart at 1 in each stage**, so a round is identified by (`stage`, `round`), never by `round` alone. Downstream code that orders by `round` alone is not safe for a league-season with more than one kept stage: `notes/DECISIONS.md` D7.
- **Position within a round.** `match_index_in_round` is 1..`matches_in_round`, ordered by kickoff datetime then home name then away name (`domain/match.py:round_sort_key`). It is assigned in `scrapers/schedule.py:_order_round` over **every scheduled match in the round including unplayed ones**, then only finished rows are written — so `matches_in_round` can exceed the row count for a partially-played round, and the position cannot be recomputed downstream (unplayed rows never reach the CSV). This is the one derived column that cannot be a `@computed_field` on `Match`, because it depends on the round's other rows. For reading it correctly, see `round_position` in `features/CLAUDE.md`.

## 5. Odds

- **Odds come in three flavours, one pass each.** The schedule odds column is a single three-cell widget (`ROW_ODDS_CELLS`) whose meaning depends on the header selectbox, so `driver.switch_odds_type(driver, kind)` clicks `li[type='...']` and the choice persists across round clicks. `scrapers/constants.py:ODDS_TYPES` maps our name to the DOM type and the header label it must show afterwards: `1x2` → `O` (home/draw/away), `ah` → `L` (home/**line**/away), `ou` → `T` (over/**line**/under). `scrapers/schedule.py` scrapes 1X2 first, then loops the secondary types and switches back.
- The switch is verified, not assumed — it returns `False` if the header label never changes, and a repaint guard waits for the first row's odds to actually change.
- Missing odds parse to `None` (`has_odds` / `has_ou_odds` / `has_ah_odds` = False); all odds fields on `Match` are nullable.
- **For AH and O/U the informative column is the line, not the price.** nowgoal moves the handicap/goal line and holds both prices near 1.90, so `ah_line` and `ou_line` carry the signal and `implied_over` / `implied_ah_home` are only the tilt around it.
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

`scrapers/goals.py` scrapes each match's **live** page (`https://live11.nowgoal26.com/match/live-<match_id>`) — a *different* page from the h2h detail page, same match id. One render fills two stores: `data/raw/goals.csv` (`domain/goal.py`, one row per goal) and `data/raw/events.csv` (`domain/event.py`, yellow/red cards and substitutions).

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

- **`data/raw/goals_done.csv` is the resume key, not `goals.csv`.** A 0-0 match produces zero goal rows, so deriving "already scraped" from the goal store would re-fetch every goalless match on every run, forever. The attempt log records one row per *attempted* match with its goal count.
- **`goals_done.csv` and `events_done.csv` are separate**, which is what let the events store be added to a corpus already fully scraped for goals: such a match is fetched exactly once more, writes only the store it is missing, and is then done for both.

### The work list

The union of the corpus and the history blocks, **deduplicated across leagues before any fetch**. History rows carry the referenced match's own id and league id in the `index` and `name` attributes (`HIST_MATCH_ID_ATTR` / `HIST_LEAGUE_ID_ATTR`); these are flattened into `*_lastN_match_id` / `*_lastN_league_id`. **Detail files scraped before 2026-09-22 have neither column**, so `scrapers.goals` finds no history ids until detail is re-scraped. Measured scale: 17.8 references per match, ~14 still new by the twentieth page, 48% already corpus matches.
