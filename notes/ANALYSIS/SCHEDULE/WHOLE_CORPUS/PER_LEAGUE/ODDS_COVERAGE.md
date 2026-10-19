# ODDS_COVERAGE — the opening odds of each league

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/PER_LEAGUE`: 73 leagues, each with its seasons together.
- **Sources:** schedule stage 3. Inputs: the market flags S2.11–13, which tell if all cells of a market (S1.16–24) are there. Units: the league (S1.03) and the season (S1.01). For the causes: the stage and the round (S1.04, S1.05), and S3.10. The list of gaps also shows the kickoff and the teams (S1.07, S1.10–11). Outcome: the half-time and full-time goals (S1.12–15), only to find the score of an awarded match.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.per_league.odds_coverage`, at the commit that adds this doc.
- **Kind:** empirical: a fact about the data, not about football.

## Question

Which matches have Bet365's opening prices in all three markets: 1X2, O/U and AH? Which leagues have gaps, and what is the likely cause of each gap?

## Claims

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | All matches but one have all three opening markets. No match has only some of them | 36,237 of 36,238. 72 of 73 leagues and 143 of 144 league-seasons are at 100%. Markets: all three 36,237, none 1 | 36,238 | yes: 17,756 of 17,757 in 2024, 18,481 of 18,481 in 2025 | exploratory |
| C2 | The one match without odds has the score of an awarded match | Cyprus D1 2024-2025, round 3, match 2609242: Apollon Limassol FC against AEL Limassol, 0-0 at half-time, 3-0 at full time. It has no market | 1 match | in 2024 | exploratory |
| C3 | The score of an awarded match does not find one alone | 344 matches go from 0-0 at half-time to 3-0 or 0-3, and 343 of them have all three markets. Of the 2,174 matches that end 3-0 or 0-3, 1 has no odds | 36,238 | not measured | exploratory |

## Leagues below 100%

| league | seasons | matches | all three markets | share |
|---|---|---|---|---|
| cyprus_1_division | both | 364 | 363 | 0.9973 |
| cyprus_1_division | 2024-2025 | 182 | 181 | 0.9945 |

The other 72 leagues have all three markets on each match. The runner prints each league.

## Each gap and its likely cause

| league | season | round | match | kickoff | home | away | half-time | full time | markets | cause |
|---|---|---|---|---|---|---|---|---|---|---|
| cyprus_1_division | 2024-2025 | 3 | 2609242 | 2024-09-15 18:00+02:00 | Apollon Limassol FC | AEL Limassol | 0-0 | 3-0 | none | awarded pattern |

## Matches that end 3-0 or 0-3

| half-time score | matches | all three markets | no odds |
|---|---|---|---|
| 0-0 | 344 | 343 | 1 |
| the full-time score | 169 | 169 | 0 |
| other | 1,661 | 1,661 | 0 |
| any | 2,174 | 2,173 | 1 |

## Method

- **A market is there** when all of its cells are there: the three 1X2 prices (S2.11), the O/U line and its two prices (S2.12), and the AH line and its two prices (S2.13).
- **Coverage:** the share of the matches that have all three markets.
- **The likely cause of a gap:** the first rule that fits, in this order.
  1. The awarded pattern: no market, a 3-0 or 0-3 result, and 0-0 or that result at half-time.
  2. 1X2 only: the 1X2 is there, but the O/U or the AH is not.
  3. Rescheduled: S3.10, a kickoff 5 days or more from the median kickoff of its round.
  4. Stage start: rounds 1 and 2 of the stage.
  5. Stage end: the last round of the stage and the 2 rounds before it.
  6. Isolated: no rule fits.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026.

## Caveats

- **The corpus was chosen on this coverage.** On 2026-10-10, the user removed each league with a gap that was not a proven forfeit (`notes/LOG/MIGRATIONS.md`, 2026-10-10). So C1 comes mostly from that choice. It says nothing about how often Bet365 prices a match in other leagues.
- **The odds are Bet365's alone.** A missing price means that Bet365 did not price the match. Another bookmaker can have priced it (`notes/FIELDS/SCHEDULE_1_RAW.md`, "Missing odds mean Bet365 did not price the match").
- **The award comes from the page, not from the score.** Match 2609242 was on the forfeit list of the project until 2026-10-10. Its detail page shows the one sign of an award found so far: its In-Play odds are missing (`notes/FIELDS/DETAIL_1_RAW.md`, "An awarded match on this page").
- **An award can keep its odds.** If a match is awarded after Bet365 opens its prices, it keeps them. The league removed last on 2026-10-10 had one such forfeit (`notes/LOG/MIGRATIONS.md`, 2026-10-10). The schedule cannot find such a match, because its score is not special (C3).
- **The awarded match stays in the corpus.** Each analysis that needs the odds leaves it out (`analysis/methods/yardstick.py:priced`). An analysis of outcomes alone counts it as a 3-0 that nobody played: 1 match of 36,238.
- **The checks are in `qa.validate`.** It fails a league-season with a market that is only partly there (`qa/odds.py:check_whole_markets`), and one below 99% on all three markets (`qa/odds.py:check_coverage`). This doc describes the coverage. It does not replace the checks.
- **Not in this doc:** the margins and the lines of the markets. The 1X2 margin is in `../ALL/SHIN.md`. The O/U and AH margins and lines go to `ALL/PRICES.md` (`notes/WORKING/PLAN_2026-10-16_ANALYSIS_MIGRATION.md`).
- **Looks:** the coverage of 73 leagues, 144 league-seasons and 2 cohorts; 1 gap; 4 rows of 3-0 and 0-3 results.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run |
