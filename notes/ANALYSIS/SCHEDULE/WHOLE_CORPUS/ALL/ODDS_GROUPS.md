# ODDS_GROUPS — comebacks and 7+ matches on the same opening prices

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together, divided by their opening prices.
- **Sources:** schedule stage 3. Inputs: the nine opening prices (S1.16–24), the market chances S2.17 and S2.19, and the odds yardstick, which reads S1.16–19 and S2.24 (`ALL/ODDS_YARDSTICK.md`). Outcomes: the comeback label (S2.26) and the goals (S2.01). Also the league name (S1.03), the league-season (S1.02, S1.01) and the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 have all three opening markets, and this doc uses them.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.odds_groups`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Matches with the same opening prices form a group. Do comebacks or 7+ matches collect in some groups more than the prices expect? If so, a price set would mark a kind of match that the market prices wrong.

## Claims

The null gives each match the chance that the odds yardstick gives it, times one factor, so that the chances add up to the observed count. Under this null, the prices tell all that they can. Each "null" number is the mean of 1,000 draws from it, with the 95% range of the draws.

| id | claim | number [95% range] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | Comebacks do not collect on the same 1X2 prices | groups with 2 or more comebacks: 276 against a null of 275.1 [246, 304], p = 0.485. With 3 or more: 66 against 65.3 [51, 81], p = 0.470. The most surprising group is not more surprising than chance: p = 0.122 | 36,237 in 9,094 groups | not measured | exploratory |
| C2 | On all 9 prices the same, more groups have 2 comebacks than the null expects. No group has 3 | 15 groups against a null of 7.7 [3, 13], p = 0.010. With 3 or more: 0 against 0.39 | 36,237 in 34,270 groups (1,622 have 2 or more matches) | not measured | exploratory, a lead (Caveats) |
| C3 | Comebacks do not change from group to group on near prices after the yardstick | AH line and O/U line: Q p = 0.172 over 60 groups, the test finds an sd of 0.170 in O/E at 80% power. 1X2 chances to 0.05 and O/U line: p = 0.595 over 79 groups, 0.190. Shrunk O/E 1.148–1.313 and 1.239 | 33,325 and 29,233 | the group values do not agree between the cohorts: r = 0.009 (n = 60) and 0.039 (n = 79) | exploratory |
| C4 | The groups with the most comebacks in one cohort have the level of all groups in the other cohort | AH line and O/U line: the top fifth (O/E 1.812 and 1.803) reads 1.272 and 1.279 in the other cohort, against 1.257 and 1.237 for all groups. 1X2 chances and O/U line: 1.922 and 1.702 read 1.200 and 1.203, against 1.239 and 1.235 | 52 and 64 groups | is the test | exploratory |
| C5 | In the coarse groups, the most surprising group has more comebacks than chance gives. Both sit at an O/U line of 1.75 | AH line 0.25 and O/U line 1.75: 9 comebacks against 2.25 expected (tail p 0.0006); against the most surprising group of each draw p = 0.028. Home chance 0.40, away chance 0.25 and O/U line 1.75: 5 against 0.67 (tail p 0.0006), p = 0.046 | 67 and 20 matches | not measured | exploratory |
| C6 | 7+ matches do not collect on any of the four kinds of the same prices | the counts of groups with 2 or more and 3 or more: p from 0.215 to 1.0. The most surprising group: p from 0.106 to 0.797. Q p = 0.582 (58 groups) and 0.333 (64 groups). The top fifth of one cohort reads 0.704 to 0.821 in the other, against 0.783 to 0.817 for all | 36,237 | the group values do not agree between the cohorts: r = −0.059 and 0.083 | exploratory |

## The groups

| grouping | groups | groups of 2+ matches | matches in them | largest group |
|---|---|---|---|---|
| exact 1X2 prices | 9,094 | 5,440 | 32,583 | 66 |
| exact 9 prices | 34,270 | 1,622 | 3,589 | 23 |
| AH line and O/U line | 194 | 174 | 36,217 | 2,130 |
| 1X2 chances to 0.05 and O/U line | 418 | 349 | 36,168 | 1,227 |

## Against the null

The p is the share of draws at least as extreme as the data, one-sided. "Smallest tail p" belongs to the most surprising group: the Poisson chance of at least its count, if its expected count is right.

| grouping | statistic | comebacks: observed | null [95% range] | p | 7+: observed | null [95% range] | p |
|---|---|---|---|---|---|---|---|
| exact 1X2 prices | 2 or more | 276 | 275.1 [246, 304] | 0.485 | 61 | 64.3 [49, 79] | 0.684 |
| | 3 or more | 66 | 65.3 [51, 81] | 0.470 | 8 | 7.8 [3, 13] | 0.526 |
| | smallest tail p | 0.0004 | 0.0015 [0.0001, 0.0040] | 0.122 | 0.0017 | 0.0011 [0.0001, 0.0035] | 0.797 |
| exact 9 prices | 2 or more | 15 | 7.7 [3, 13] | 0.010 | 1 | 1.9 [0, 5] | 0.860 |
| | 3 or more | 0 | 0.39 [0, 2] | 1.0 | 0 | 0.10 [0, 1] | 1.0 |
| | smallest tail p | 0.0023 | 0.0043 [0.0010, 0.0079] | 0.064 | 0.0005 | 0.0028 [0.0002, 0.0051] | 0.106 |
| AH line and O/U line | 2 or more | 98 | 95.0 [89, 101] | 0.225 | 93 | 91.8 [84, 99] | 0.432 |
| | 3 or more | 82 | 82.9 [77, 89] | 0.674 | 79 | 75.7 [69, 82] | 0.215 |
| | smallest tail p | 0.0006 | 0.0122 [0.0005, 0.0377] | 0.028 | 0.0057 | 0.0128 [0.0006, 0.0406] | 0.318 |
| 1X2 chances to 0.05 and O/U line | 2 or more | 161 | 163.3 [153, 173] | 0.710 | 129 | 132.6 [122, 144] | 0.781 |
| | 3 or more | 133 | 131.0 [122, 140] | 0.386 | 97 | 98.5 [90, 108] | 0.651 |
| | smallest tail p | 0.0006 | 0.0075 [0.0004, 0.0254] | 0.046 | 0.0023 | 0.0073 [0.0003, 0.0233] | 0.232 |

## The 15 groups of C2

Each of the 15 groups has 2 comebacks. 11 groups hold matches of 2 leagues, and 4 hold matches of 3 leagues. 4 groups hold matches of Australian state leagues: the 3 groups of 3 or 4 matches with only Australian leagues, and 1 group with 2 Australian leagues and the UAE Pro League. Each of the other 11 groups pairs two leagues of different countries, or England's League 1 and League 2. The expected comebacks of a group are from 0.07 to 0.33.

## Across the groups, and from one cohort to the other

Only the groups with 5 or more expected events are in the test across the groups. The exact groups have none. For the carry-over, a group needs 3 or more expected events in each cohort. The top fifth is chosen by O/E in one cohort, then read in the other.

| grouping | quantity | groups | Q | p | sd found at 80% (in O/E) | raw min–max | luck min–max | cohorts r | top fifth, chosen in 2024: O/E then in 2025 (all) | chosen in 2025: O/E then in 2024 (all) |
|---|---|---|---|---|---|---|---|---|---|---|
| AH line and O/U line | comeback | 60 | 69.15 | 0.172 | 0.170 | 0.556–1.999 | 0.521–2.086 | 0.009 | 1.812, then 1.272 (1.257) | 1.803, then 1.279 (1.237) |
| | 7+ goals | 58 | 54.16 | 0.582 | 0.181 | 0.000–1.433 | 0.190–1.564 | −0.059 | 1.431, then 0.704 (0.815) | 1.302, then 0.821 (0.817) |
| 1X2 chances to 0.05 and O/U line | comeback | 79 | 74.39 | 0.595 | 0.190 | 0.694–1.984 | 0.448–2.194 | 0.039 | 1.922, then 1.200 (1.239) | 1.702, then 1.203 (1.235) |
| | 7+ goals | 64 | 67.29 | 0.333 | 0.207 | 0.145–1.815 | 0.165–1.640 | 0.083 | 1.249, then 0.752 (0.805) | 1.416, then 0.747 (0.783) |

The pooled O/E is 1.2427 and 1.2391 for comebacks, 0.8145 and 0.8175 for 7+ goals. It is the yardstick's known gap (`ALL/ODDS_YARDSTICK.md`, C2 and C7), not a finding of this doc.

## Method

- **Four groupings.** A group holds the matches with equal values in each of its columns:
  - exact 1X2 prices: the three opening 1X2 prices (S1.16–18);
  - exact 9 prices: the 1X2, O/U and AH opening prices and lines (S1.16–24);
  - AH line and O/U line (S1.22, S1.19);
  - 1X2 chances to 0.05 and O/U line: the home and away chances with the margin taken out proportionally (S2.17, S2.19), each rounded to the nearest 0.05, and the O/U line.
- **The null.** Each match gets the yardstick's chance (`m_cb` for a comeback, `m_seven` for 7+), times one factor so that the chances add up to the observed count. Each draw gives each match its event with that chance.
- **Against the null.** For the data and for each of 1,000 draws: the groups with 2 or more events, the groups with 3 or more, and the smallest tail p of a group with an event. The p is the share of draws with at least as many groups, or with a tail p at least as small, with 1 added to the count and to the draws.
- **Across the groups.** The groups with 5 or more expected events (the yardstick's chances, not scaled) are units (`analysis/units.py:summary_row`): one Q test of their O/E, the luck line, the shrunk values, the sd that the test finds with 80% power, and the Spearman r of the group values between the two cohorts.
- **Carry-over.** The groups with 3 or more expected events in each cohort. The fifth with the highest O/E in one cohort is read in the other cohort, against all of these groups in that cohort.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026.

## Caveats

- **Looks:** 4 groupings × 2 outcomes × 3 statistics = 24 tests against the null, 4 tests across the groups and 8 reads of the carry-over: 36 looks. C2's p = 0.010 is the smallest. A Bonferroni correction over 36 looks gives 0.36. So C2 is a lead, not a finding. A test needs a new holdout (`notes/ANALYSIS/CLAUDE.md` §6).
- **The null has one factor for all matches, but the yardstick's error is not the same everywhere.** The comeback excess is largest at low expected goals (`ALL/ODDS_YARDSTICK.md`, C6). The matches of one group share their prices, so they share any error of the yardstick at those prices. This adds groups with 2 events and very surprising groups, with no price clustering. It can be part of C2 and C5.
- **C5 is at the low lines.** Both groups sit at an O/U line of 1.75, where the yardstick expects too few comebacks (C6 of `ALL/ODDS_YARDSTICK.md`). The two groups can share matches, so they are not two findings. The test across the groups (C3) does not find a spread.
- **C2 is in the smallest groups.** A group of 2 to 4 matches with 2 comebacks has a tail p from 0.002 to 0.043. 4 of its 15 groups hold Australian state leagues, which share price sets. Most of the others pair two matches from different countries. The run does not tell if a shared price set means a shared kind of match.
- **Shared data:** the null and the groups both come from the opening prices. The group values of the two cohorts come from different matches.
- **Power:** the test across the groups finds an sd of about 0.17–0.19 in O/E for comebacks and 0.18–0.21 for 7+ goals. A smaller spread between price groups can exist.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run |
