# LEVELS — at which level the differences between matches sit

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together, divided into the levels of `notes/ANALYSIS/CLAUDE.md` §2: the league, the league-season, the round and the team.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 prices (S1.16–18) and the opening O/U line and prices (S1.19–21), through S2.24 and the odds yardstick (`ALL/ODDS_YARDSTICK.md`). Units: the league (S1.02), the season (S1.01), the stage and the round (S1.04–05), and the teams (S1.08–09). The season also gives the season cohort. Outcomes: the half-time and full-time goals (S1.12–15), and S2.01, S2.26 and S2.29.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 have both opening markets: 73 leagues, 144 league-seasons, 4,606 rounds and 2,227 team-seasons (72,474 team-matches).
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.levels`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Matches differ in comebacks, in 7+ goals and in goals. Where do these differences sit: in the league, in the season of a league, in the round, in the team, or in the match itself? How much of each do the opening prices carry?

## Claims

"Share" is the share of the variance of one match (or one team-match) that the differences between the parts of a level make (Method). Each p comes from 200 shuffles of the parts inside their unit. Its smallest value is 0.00498. "Found" is the share that the test finds at p < 0.05 in 80% of simulated corpora.

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | Without the odds, the largest differences sit at the league | league, raw: goals per match share 0.0282 (sd 10.24% of 2.7476), 7+ 0.0061 (51.78%), link 1 0.0056 (6.24%), comeback 0.0012 (14.76%); each p 0.00498. League-season inside its league: goals 0.0019 (p 0.00995); every other p 0.129 or more. Round inside its league-season: every raw p 0.109 or more | 73 leagues, 144 league-seasons, 4,606 rounds | not measured: the cohort tables read the odds | exploratory |
| C2 | The odds carry the differences of the leagues and of the league-seasons | against the odds: league p from 0.124 to 0.313, shares from 0.0001 to 0.0004; league-season p from 0.274 to 0.652. The odds carry 0.0470 of the variance of a match's goals, 0.0111 of 7+, 0.0108 of link 1 and 0.0011 of a comeback | 36,237 matches | yes, but for link 1 in 2025: league p from 0.104 to 0.716 (2024), and from 0.333 to 0.612 (2025); link 1 in 2025 p 0.0199, share 0.0014 | exploratory |
| C3 | Beyond the odds, the variance of a comeback sits in the match. No level holds a share that its test can find | beyond the odds: league 0.0001, league-season 0.0001, round 0.0002, team-season 0 (comes back, loses a lead). The tests find 0.0010 (league), 0.0019 (league-season), 0.0066 (round), 0.0025 and 0.0026 (team-season) | 36,237 matches; 72,474 team-matches | yes: in each cohort, each comeback p is 0.234 or more | exploratory |
| C4 | The differences between the teams of a league-season are in the prices | raw, then against the odds: behind at half-time 0.0260 (p 0.00498), then 0.0014 (p 0.0896); behind, then wins 0.0307 (p 0.00498), then 0 (p 0.746); goals scored 0.0715, then 0 (p 0.493); goals conceded 0.0483, then 0 (p 0.627). The odds carry 0.1193 of the variance of a team's goals | 2,227 team-seasons | yes: against the odds, each team-season p in the cohorts is 0.0697 or more | exploratory |
| C5 | Against the odds, only the round shows a sign: for goals and 7+, in the 2024 cohort only | round: goals per match p 0.0249 (share 0.0056), 7+ p 0.0149 (share 0.0078). `ALL/ROUND_CLUSTERS.md` reads them | 4,606 rounds | no: p 0.00498 for both in 2024; 0.682 (goals) and 0.602 (7+) in 2025 | exploratory |
| C6 | Against the odds, the comeback values of the team-seasons vary less than shuffled team-matches make them | comes back: Q 1960.5 against 2095.6 (sd 58.3) in the shuffles | 2,227 team-seasons | clear in 2025 only: 957.9 against 1060.5 (sd 41.2); 2024: 1002.6 against 1024.7 (sd 40.5) | exploratory |

## The levels, raw and against the odds

"sd / pooled" is the spread of the raw part values, as a share of the pooled value. The last column is the share that the test against the odds finds at 80%.

| quantity | level | raw: sd / pooled | raw: share | raw: p | odds: share | odds: p | found |
|---|---|---|---|---|---|---|---|
| comeback | league | 0.1476 | 0.0012 | 0.00498 | 0.0001 | 0.313 | 0.0010 |
| | league-season | 0.0539 | 0.0002 | 0.388 | 0.0001 | 0.418 | 0.0019 |
| | round | 0 | 0 | 0.517 | 0.0002 | 0.478 | 0.0066 |
| link 1: a team is behind at half-time | league | 0.0624 | 0.0056 | 0.00498 | 0.0004 | 0.124 | 0.0010 |
| | league-season | 0.0185 | 0.0005 | 0.264 | 0.0002 | 0.388 | 0.0019 |
| | round | 0 | 0 | 0.886 | 0 | 0.821 | 0.0069 |
| link 2: the team behind wins | league | 0.1192 | 0.0014 | 0.0199 | 0.0004 | 0.264 | 0.0028 |
| | league-season | 0.0315 | 0.0001 | 0.443 | 0.0004 | 0.403 | 0.0053 |
| | round | 0.1217 | 0.0014 | 0.363 | 0 | 0.607 | 0.0190 |
| 7+ goals | league | 0.5178 | 0.0061 | 0.00498 | 0.0004 | 0.174 | 0.0015 |
| | league-season | 0.1379 | 0.0004 | 0.129 | 0.0004 | 0.274 | 0.0026 |
| | round | 0.2756 | 0.0018 | 0.109 | 0.0078 | 0.0149 | 0.0087 |
| goals per match | league | 0.1024 | 0.0282 | 0.00498 | 0.0004 | 0.134 | 0.0010 |
| | league-season | 0.0265 | 0.0019 | 0.00995 | 0 | 0.652 | 0.0019 |
| | round | 0.0149 | 0.0006 | 0.423 | 0.0056 | 0.0249 | 0.0059 |
| comes back | team-season | 0 | 0 | 0.662 | 0 | 0.975 | 0.0025 |
| loses a lead | team-season | 0.2243 | 0.0013 | 0.0746 | 0 | 0.647 | 0.0026 |
| behind at half-time | team-season | 0.2488 | 0.0260 | 0.00498 | 0.0014 | 0.0896 | 0.0026 |
| behind, then wins | team-season | 0.5633 | 0.0307 | 0.00498 | 0 | 0.746 | 0.0134 |
| goals scored | team-season | 0.2379 | 0.0715 | 0.00498 | 0 | 0.493 | 0.0023 |
| goals conceded | team-season | 0.1956 | 0.0483 | 0.00498 | 0 | 0.627 | 0.0023 |

## The share that the odds carry

| rows | quantity | counted | variance | odds share |
|---|---|---|---|---|
| match | comeback | 36,237 | 0.0495 | 0.0011 |
| | link 1: a team is behind at half-time | 36,237 | 0.2417 | 0.0108 |
| | link 2: the team behind wins | 21,412 | 0.0805 | 0.0699 |
| | 7+ goals | 36,237 | 0.0219 | 0.0111 |
| | goals per match | 36,237 | 2.8123 | 0.0470 |
| team | comes back | 72,474 | 0.0254 | 0.0035 |
| | loses a lead | 72,474 | 0.0254 | 0.0035 |
| | behind at half-time | 72,474 | 0.2082 | 0.0562 |
| | behind, then wins | 21,412 | 0.0805 | 0.0699 |
| | goals scored | 72,474 | 1.4952 | 0.1193 |
| | goals conceded | 72,474 | 1.4952 | 0.1193 |

## Against the odds, in each season cohort

A league has one season in each cohort, so the cohorts have no league-season level. Each cell is the p, then the share.

| quantity | league 2024 | league 2025 | round 2024 | round 2025 |
|---|---|---|---|---|
| comeback | 0.418, 0.0001 | 0.333, 0.0003 | 0.443, 0.0005 | 0.418, 0.0006 |
| link 1 | 0.716, 0 | 0.0199, 0.0014 | 0.682, 0 | 0.781, 0 |
| link 2 | 0.174, 0.0019 | 0.612, 0 | 0.841, 0 | 0.249, 0.0084 |
| 7+ goals | 0.104, 0.0013 | 0.567, 0 | 0.00498, 0.0164 | 0.602, 0 |
| goals per match | 0.169, 0.0005 | 0.572, 0 | 0.00498, 0.0129 | 0.682, 0 |

| quantity | team-season 2024 | team-season 2025 |
|---|---|---|
| comes back | 0.692, 0 | 1, 0 |
| loses a lead | 0.92, 0 | 0.234, 0.0011 |
| behind at half-time | 0.308, 0.0008 | 0.0697, 0.0020 |
| behind, then wins | 0.851, 0 | 0.363, 0.0021 |
| goals scored | 0.443, 0 | 0.527, 0 |
| goals conceded | 0.841, 0 | 0.294, 0.0006 |

## Method

- **The yardstick:** `ALL/ODDS_YARDSTICK.md`, on the 36,237 matches with both opening markets.
- **The levels:** the parts of each level are tested around the level above them (`analysis/units.py:level_row`). The leagues are tested around all matches. The league-seasons are tested around their league. The rounds and the team-seasons are tested around their league-season.
  - A round is one round of one stage of a league-season (`analysis/corpus.py:round_key`).
  - A team-season is a team in one league-season, with two rows for each match, one for each team (`analysis/card.py:team_yardstick_rows`).
- **Why team-seasons:** the team of `PER_TEAM/` is a team in one league, with its seasons together. Its value then also holds the league-season. A team-season is inside one league-season, so the levels nest. Whether a team trait continues is the repeat test of `PER_TEAM/` (no repeat).
- **Two readings:** raw (the count divided by its denominator), and against the odds (the count divided by the count that the yardstick expects). The match quantities are those of the card (`analysis/card.py:ODDS_CARD`). The team quantities are those of the team card (`analysis/schedule/whole_corpus/all/levels.py:TEAM_QUANTITIES`).
- **The test:** Cochran's Q of the parts around the precision-weighted mean of their unit, summed over the units (`analysis/units.py:within_tested`). The variance of a part is that of its kind at the value of its unit, times the dispersion of the matches. A part that expects nothing, or that is in a unit with no events, leaves the test.
- **The shuffles** (`analysis/units.py:permuted_qs`): 200 times, each match takes the part of a random match of its unit. Each part keeps its size. The outcomes and the expected values stay together. The p is (1 + the shuffles with a Q at least the real Q) / 201.
- **Why shuffles, and not the chi-square p:** the dispersion is measured around each part. For goals, small parts make it too low, by about 1 divided by the matches of a part. Then Q is too large. The rounds (about 8 matches each) give a shuffled mean of 5120.6 against 4,462 df. The team-seasons (about 33 rows each) give 2153.0 against 2,083 df for goals scored. The shuffles have the same bias as the real Q, so their p is correct. For a 0/1 outcome, the means stay near the df (comeback, round: 4489.5 against 4,462).
- **The spread τ:** (Q − the mean of the shuffles) divided by the scale of the method of moments (DerSimonian–Laird). τ is 0 when Q is below the mean.
- **Share** (`analysis/units.py:variance_share`): τ² × the mean of the squared expected values, divided by the variance of the observed values, over the rows that count (the expected value above 0). For a raw rate, the expected value is 1, or the denominator.
- **Found:** the τ that the test finds at p < 0.05 in 80% of simulated corpora, under the normal random-effects model (`analysis/stats.py:detectable_tau`), turned into a share in the same way.
- **The odds share** (`analysis/schedule/whole_corpus/all/levels.py:odds_share`): 1 − the summed squared error / the summed squared distance from the mean. The fit is the yardstick's expected value times the pooled O/E.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025 (17,756 matches). 2025 holds 2025 and 2025-2026 (18,481).

## Caveats

- **A small share is not a small difference.** A 0/1 event with the chance 0.05 has a variance of about 0.05 for each match. The leagues spread the raw comeback rate by 14.76%, but they make only 0.0012 of that variance. Read the share with the sd / pooled.
- **The shares come from separate tests.** Each level has its own test around the level above it, so the shares do not add up exactly. The league value holds about half of the league-season variance, because most leagues have two seasons. For raw goals, that is about half of 0.0019, against 0.0282.
- **The odds share of link 2 reads the half-time score.** The completion chance of the yardstick starts from the half-time score, which is an outcome of the match. So 0.0699 is not a share known before kickoff.
- **"Found" uses a normal model.** For rare events in small parts (the rounds), the true power is lower.
- **Rule 7: one match, two team rows.** The two rows of a match have opposite roles. The shuffles move rows, not matches.
- **Rule 8: calibration first.** `PER_TEAM/ODDS_YARDSTICK.md` shows that the comeback O/E does not change with the strength of the team. So a yardstick error by strength cannot make a team level.
- **C6 repeats `PER_TEAM/ODDS_YARDSTICK.md` C6** at the team-season, with shuffles in place of draws of outcomes. This doc does not explain it either.
- **Looks:** 40 tests on all matches, 32 in the cohorts, and 11 odds shares. 52 of the tests are against the odds. Below p = 0.05 against the odds: the round on all matches (C5, 2 tests), the round in 2024 (2 tests), and link 1 at the league in 2025. At p = 0.05, 52 tests give about 2.6 by chance. The 2024 round tests share their data with C5.
- **Not profit.** A level with more comebacks than the yardstick does not show value. The value needs the HT/FT prices, and nowgoal does not show them.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run |
