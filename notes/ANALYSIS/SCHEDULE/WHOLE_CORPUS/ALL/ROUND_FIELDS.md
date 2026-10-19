# ROUND_FIELDS — how often each value of the round so far occurs

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together.
- **Sources:** schedule stage 3. The round-so-far fields S3.14–20 (`notes/FIELDS/SCHEDULE_3_MULTI.md` §A2), all known before kickoff. For C4–C5: the opening O/U line (S1.19), the goals (S2.01, outcome), and the odds yardstick, which reads S1.16–19 and S2.24 (`ALL/ODDS_YARDSTICK.md`). The season (S1.01) gives the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. C4 uses the 36,237 with an opening O/U line, and C5 the 36,237 with both opening markets.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.round_fields`, at the commit that adds this doc.
- **Kind:** empirical: how often the values occur. The direction of C4 is structural (Caveats).

## Question

How often does each count of the round so far take each value? How often do the two averages have a value? And where does S3.19 − S3.20 sit when a round goes as the opening lines expect?

## Claims

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | Most matches see no rare event earlier in their round | S3.17 is 1 or more for 0.1466 of matches, 2 or more for 0.0206, and never above 3. S3.15 is 1 or more for 0.1115, S3.16 for 0.0502 | 36,238 | yes: S3.17 1 or more for 0.1445 (2024) and 0.1487 (2025) | exploratory |
| C2 | A third of matches kick off before any match of their round has finished | S3.14 is 0 for 0.3291 of matches. Its mean is 2.4348, its largest value 11 | 36,238 | yes: 0.3235 and 0.3344 | exploratory |
| C3 | Both teams scored in at least one earlier match of the round for more than half of the matches. Each match with a finished round-mate has the two averages | S3.18 is 1 or more for 0.5614. S3.19 and S3.20 have a value for 0.6709, the share with S3.14 1 or more. 0 rows have a finished round-mate and empty averages | 36,238 | yes: S3.18 1 or more for 0.5621 and 0.5607 | exploratory |
| C4 | A match scores more goals than its opening O/U line, so S3.19 − S3.20 is above 0 when a round goes as priced | goals minus the line: 0.1260 on average, 0.2198 at a line of 2, 0.0097 at 3.5. S3.19 − S3.20: mean 0.1244, median 0.0833 | 36,237 matches with a line; 24,313 with averages | yes for S3.19 − S3.20: mean 0.1010 (2024), 0.1472 (2025) | exploratory |
| C5 | The opening O/U line ranks matches like the yardstick's expected goals, but sits below them | correlation 0.9818. The expected goals are 0.1570 above the line on average | 36,237 | not measured | exploratory |

## The counts

| field | share 0 | share 1+ | share 2+ | share 3+ | mean | largest |
|---|---|---|---|---|---|---|
| S3.14 finished | 0.3291 | 0.6709 | 0.5254 | 0.4146 | 2.4348 | 11 |
| S3.15 comebacks | 0.8885 | 0.1115 | 0.0112 | 0.0010 | 0.1237 | 3 |
| S3.16 7+ goals | 0.9498 | 0.0502 | 0.0021 | 0.0001 | 0.0524 | 3 |
| S3.17 rare events | 0.8534 | 0.1466 | 0.0206 | 0.0020 | 0.1692 | 3 |
| S3.18 both teams scored | 0.4386 | 0.5614 | 0.3571 | 0.2114 | 1.3056 | 9 |

Per season cohort, share 1+: S3.14 0.6765 and 0.6656, S3.15 0.1111 and 0.1118, S3.16 0.0485 and 0.0519, S3.17 0.1445 and 0.1487, S3.18 0.5621 and 0.5607 (2024, then 2025). The cohorts hold 17,757 and 18,481 matches.

## The averages

| field | with a value | share | mean | p25 | median | p75 |
|---|---|---|---|---|---|---|
| S3.19 average goals | 24,313 | 0.6709 | 2.7283 | 2.0000 | 2.6667 | 3.3333 |
| S3.20 average O/U line | 24,313 | 0.6709 | 2.6039 | 2.3333 | 2.5625 | 2.8125 |
| S3.19 − S3.20 | 24,313 | 0.6709 | 0.1244 | −0.5000 | 0.0833 | 0.7500 |

## Goals against the opening line

| opening O/U line | matches | goals minus line |
|---|---|---|
| all | 36,237 | 0.1260 |
| 2 | 2,639 | 0.2198 |
| 2.25 | 7,900 | 0.1554 |
| 2.5 | 9,246 | 0.1290 |
| 2.75 | 7,541 | 0.1067 |
| 3 | 4,792 | 0.1091 |
| 3.25 | 2,409 | 0.0472 |
| 3.5 | 1,083 | 0.0097 |

Lines with fewer than 500 matches get no row of their own.

## Method

- **The counts and the averages** are the stage-3 values (`features/schedule_multi.py`), read as they are. A share is over all matches of the corpus, or of a cohort.
- **The 24,313 matches with averages** are 0.6709 of the 36,238 (12,012 in 2024, 12,301 in 2025).
- **Goals minus the line:** the goals of a match (S2.01) minus its opening O/U line (S1.19), over every match with a line, then per line.
- **The line against the yardstick:** the Pearson correlation of the opening line with the yardstick's expected goals (`m_goals`), and the mean of their difference, over the matches with both opening markets.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026.

## Caveats

- **The direction of C4 and C5 is structural.** An Asian O/U line is the market's 50/50 point, not its expected goals. Goals are skewed to the right, so under the goal model the fair line sits below the expected goals: the yardstick's own expected goals are 0.1570 above the line (C5). The size in C4 is empirical. It is a little less than the model gives, as `ALL/ODDS_YARDSTICK.md` C1 also finds (the prices expect slightly more goals than happen).
- **C5 shares its data.** The yardstick is fitted to the O/U price at that same line, so a high correlation is close to sure by construction. It shows only that the line alone carries most of what the yardstick knows about goals.
- **The counts are not independent.** A round's matches see the same finished round-mates, so the rows of one round share their values.
- **What the fields mean, and their checks,** are in `notes/FIELDS/SCHEDULE_3_MULTI.md` §A2. The logic is tested by pytest on toy data (`tests/features/test_schedule_multi.py`, with the stage-3 leak test), and `qa.validate` checks the rules between the counts (`qa/stages.py:check_round_fields`).
- **Looks:** 5 counts and 3 averages for all matches and for each of 2 cohorts; 8 rows of goals against the line; 1 comparison with the yardstick.
