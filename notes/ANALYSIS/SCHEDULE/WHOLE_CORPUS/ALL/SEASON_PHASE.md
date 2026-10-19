# SEASON_PHASE — comebacks and 7+ matches by the phase of the season

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together, sliced by round (`notes/ANALYSIS/CLAUDE.md` §2, slices: season phase).
- **Sources:** schedule stage 3. Inputs: the stage and round (S1.04–05), the kickoff (S1.07), and the opening 1X2 prices (S1.16–18) and O/U market (S1.19–21, through S2.24) through the odds yardstick. Outcomes: the half-time goals (S1.12–13), the goals (S2.01) and the labels S2.26–29. Units: the league-season (S1.02, S1.01), for the intervals and the league-season reading. The season (S1.01) also gives the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 have both opening markets, and this doc uses them.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.season_phase`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Do comebacks and 7+ matches happen more often at one phase of the season: at the start, in the middle, or at the end? Leagues play different numbers of rounds, so the phase is the round as a share of the rounds of its stage. Then: does the round number itself matter?

## Claims

Each value is a count divided by a count, with a 95% interval over league-seasons. "Against the odds" is the count divided by the count that the odds yardstick expects (O/E). Each p is one test across the phases.

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | Comebacks do not change with the phase of the season | thirds by round: 0.0523 [0.0481, 0.0568], 0.0495 [0.0457, 0.0537], 0.0546 [0.0504, 0.0587]; p = 0.202. Against the league-season p = 0.21, against the odds p = 0.278. Thirds by kickoff order p = 0.369. First 3, middle, last 3 rounds: 0.0468, 0.0528, 0.0527; p = 0.312 | 36,237 | yes, no difference in either: thirds p = 0.119 (2024), 0.709 (2025); first and last rounds p = 0.161, 0.419 | exploratory |
| C2 | Neither link of a comeback changes with the phase | thirds by round, link 1: 0.5963, 0.5863, 0.5902 (p = 0.286). Link 2: 0.0877, 0.0845, 0.0926 (p = 0.229). Against the odds p = 0.171 and 0.222 | 36,237 (21,412 decisive half-times) | yes. Link 1: p = 0.942 (2024), 0.17 (2025). Link 2: p = 0.112, 0.879 | exploratory |
| C3 | 7+ goals do not change with the phase of the season | thirds by round: 0.0214 [0.0181, 0.0249], 0.0226 [0.0197, 0.0258], 0.0232 [0.0201, 0.0266]; p = 0.644. Against the odds: 0.8126, 0.8386, 0.8232; p = 0.934. First 3, middle, last 3 rounds: 0.0188, 0.0225, 0.0255; p = 0.157 | 36,237 | yes, no difference in either: thirds p = 0.224 (2024), 0.309 (2025); first and last rounds p = 0.0749, 0.898 | exploratory |
| C4 | Goals per match increase during a stage. Against the odds, the thirds do not differ | thirds by round: 2.7142 [2.6545, 2.7720], 2.7521 [2.6983, 2.8077], 2.7746 [2.7222, 2.8306]; p = 0.0185 (against the league-season p = 0.0181). First 3, middle, last 3 rounds: 2.6638 [2.5970, 2.7331], 2.7413 [2.6908, 2.7935], 2.8826 [2.8115, 2.9613]; p = 8.73e-08. Against the odds, the thirds: 0.9811, 0.9936, 0.9915; p = 0.218 | 36,237 | yes. Thirds p = 0.0301 (2024), 0.0481 (2025). The last 3 rounds are the highest in both: 2.8929 and 2.8727 | exploratory |
| C5 | In the first 3 rounds of a stage, fewer goals happen than the odds expect | O/E 0.9582 [0.9402, 0.9759] in the first 3 rounds, 0.9903 [0.9838, 0.9966] in the middle, 1.0073 [0.9867, 1.0284] in the last 3; p = 0.00121 | 36,237 (3,569 in the first 3 rounds) | the direction yes: 0.9448 against 0.9878 (2024, p = 0.000592), 0.9712 against 0.9926 (2025, p = 0.328) | exploratory |
| C6 | The round number itself makes no difference beyond luck | 33 round numbers (1 to 33). Comebacks p = 0.215, against the odds p = 0.199. 7+ goals p = 0.127, against the odds p = 0.103. Goals p = 0.758, against the odds p = 0.588 | 33,941 | the round values do not repeat between the cohorts: Spearman r = 0.0225 (comebacks), 0.1897 (7+), −0.0916 (goals), n = 33 | exploratory |

## By third of the stage

The third of the stage by round number. "League-season" is the O/E against the value of the league-season of each match.

| quantity | third | matches | count | raw [95% interval] | league-season | odds [95% interval] |
|---|---|---|---|---|---|---|
| comeback | 1 | 11,720 | 613 | 0.0523 [0.0481, 0.0568] | 1.0037 | 1.2443 [1.1468, 1.3479] |
| | 2 | 12,050 | 597 | 0.0495 [0.0457, 0.0537] | 0.9495 | 1.1866 [1.1031, 1.2735] |
| | 3 | 12,467 | 681 | 0.0546 [0.0504, 0.0587] | 1.0452 | 1.2948 [1.2001, 1.3896] |
| 7+ goals | 1 | 11,720 | 251 | 0.0214 [0.0181, 0.0249] | 0.9558 | 0.8126 [0.7066, 0.9152] |
| | 2 | 12,050 | 272 | 0.0226 [0.0197, 0.0258] | 1.0079 | 0.8386 [0.7519, 0.9271] |
| | 3 | 12,467 | 289 | 0.0232 [0.0201, 0.0266] | 1.0339 | 0.8232 [0.7222, 0.9291] |
| goals per match | 1 | 11,720 | 31,810 | 2.7142 [2.6545, 2.7720] | 0.9879 | 0.9811 [0.9699, 0.9918] |
| | 2 | 12,050 | 33,163 | 2.7521 [2.6983, 2.8077] | 1.0018 | 0.9936 [0.9845, 1.0029] |
| | 3 | 12,467 | 34,591 | 2.7746 [2.7222, 2.8306] | 1.0096 | 0.9915 [0.9791, 1.0035] |

## By first and last rounds

| quantity | rounds | matches | count | raw [95% interval] | league-season | odds [95% interval] |
|---|---|---|---|---|---|---|
| comeback | first 3 | 3,569 | 167 | 0.0468 [0.0400, 0.0542] | 0.8915 | 1.1117 [0.9472, 1.2890] |
| | middle | 29,098 | 1,536 | 0.0528 [0.0501, 0.0557] | 1.0130 | 1.2619 [1.2020, 1.3211] |
| | last 3 | 3,570 | 188 | 0.0527 [0.0460, 0.0593] | 1.0034 | 1.2181 [1.0626, 1.3741] |
| 7+ goals | first 3 | 3,569 | 67 | 0.0188 [0.0143, 0.0235] | 0.8255 | 0.6958 [0.5365, 0.8600] |
| | middle | 29,098 | 654 | 0.0225 [0.0201, 0.0250] | 1.0067 | 0.8421 [0.7798, 0.9063] |
| | last 3 | 3,570 | 91 | 0.0255 [0.0192, 0.0325] | 1.1209 | 0.8173 [0.6263, 1.0161] |
| goals per match | first 3 | 3,569 | 9,507 | 2.6638 [2.5970, 2.7331] | 0.9677 | 0.9582 [0.9402, 0.9759] |
| | middle | 29,098 | 79,766 | 2.7413 [2.6908, 2.7935] | 0.9982 | 0.9903 [0.9838, 0.9966] |
| | last 3 | 3,570 | 10,291 | 2.8826 [2.8115, 2.9613] | 1.0472 | 1.0073 [0.9867, 1.0284] |

## The tests across the phases

Q has 2 degrees of freedom in each row. The dispersion is 1.0000 for each raw comeback, link and 7+ test, and from 0.9750 to 1.0233 for goals. The table leaves out the league-season readings of the links: link 1 p = 0.284, 0.417 and 0.765, link 2 p = 0.285, 0.418 and 0.291.

| quantity | reading | thirds by round | thirds by kickoff | first and last rounds |
|---|---|---|---|---|
| comeback | raw | 0.202 | 0.369 | 0.312 |
| | league-season | 0.21 | 0.367 | 0.271 |
| | odds | 0.278 | 0.467 | 0.265 |
| link 1 | raw | 0.286 | 0.421 | 0.771 |
| | odds | 0.171 | 0.266 | 0.902 |
| link 2 | raw | 0.229 | 0.385 | 0.316 |
| | odds | 0.222 | 0.298 | 0.266 |
| 7+ goals | raw | 0.644 | 0.584 | 0.157 |
| | league-season | 0.644 | 0.581 | 0.148 |
| | odds | 0.934 | 0.677 | 0.316 |
| goals per match | raw | 0.0185 | 0.0112 | 8.73e-08 |
| | league-season | 0.0181 | 0.00934 | 7.63e-08 |
| | odds | 0.218 | 0.216 | 0.00121 |

## The round number

The round numbers with 600 matches or more are 1 to 33: 33,941 matches. Each round number is a unit (`notes/ANALYSIS/CLAUDE.md` §5, rule 1).

| quantity | pooled | Q | p | raw min–max | luck min–max | shrunk min–max | the sd that the test finds at 80% |
|---|---|---|---|---|---|---|---|
| comeback, raw | 0.0520 | 37.9957 | 0.215 | 0.0368–0.0717 | 0.0378–0.0674 | 0.0500–0.0555 | 0.0063 |
| comeback, odds | 1.2376 | 38.5110 | 0.199 | 0.8785–1.7041 | 0.8966–1.6057 | 1.1878–1.3264 | 0.1492 |
| 7+ goals, raw | 0.0225 | 41.2157 | 0.127 | 0.0118–0.0326 | 0.0132–0.0329 | 0.0198–0.0248 | 0.0042 |
| 7+ goals, odds | 0.8247 | 42.4082 | 0.103 | 0.4302–1.1479 | 0.4810–1.2015 | 0.7165–0.9127 | 0.1529 |
| goals per match, raw | 2.7454 | 26.1160 | 0.758 | 2.6269–2.8331 | 2.6367–2.8541 | 2.7454–2.7454 | 0.0474 |
| goals per match, odds | 0.9874 | 29.6118 | 0.588 | 0.9430–1.0180 | 0.9484–1.0265 | 0.9874–0.9874 | 0.0166 |

The league-season readings give p = 0.199 (comebacks), 0.131 (7+ goals) and 0.544 (goals).

## Method

- **The phase:** the round (S1.05) divided by the rounds of its stage. The rounds of a stage are its highest round number in the league-season. Each stage of the corpus starts at round 1 and has no gap in its round numbers (checked 2026-10-19). An Apertura and a Clausura are two stages, so each has its own phase.
- **Thirds by round:** ceil(3 × round / rounds). The thirds are not equal in size, because the rounds of a stage do not divide by 3.
- **Thirds by kickoff order:** the rank of the kickoff (S1.07) in the stage, as a share. A match that was put off counts where it was played. Equal kickoffs take the order of the rows.
- **First and last rounds:** rounds 1 to 3, and the last 3 rounds of the stage. Other rounds are the middle. A stage of 6 rounds has no middle.
- **Three readings of each quantity:**
  - raw: the count divided by its denominator (the matches, or the decisive half-times for link 2);
  - against the league-season: each match expects its denominator times the value of its own league-season, so the league mix of a phase changes nothing;
  - against the odds: each match expects the chance of the odds yardstick (`ALL/ODDS_YARDSTICK.md`). For link 2, it is the chance that the team behind wins, from the half-time score.
- **The test across the phases:** Cochran's Q of the phase values. The variance of each value is the one it would have if all phases had the pooled value: Bernoulli for an event, Poisson for goals, times the dispersion of the matches (`analysis/units.py`).
- **The round number:** each round number with 600 matches or more is a unit (`units.summary_row`): one Q test, the luck line (the median lowest and highest value of 2,000 draws with no difference), the shrunk values, the sd that the test finds with 80% power, and the Spearman r of the round values between the two cohorts.
- **Intervals:** a cluster bootstrap over the 144 league-seasons, with 2,000 resamples (`analysis/stats.py:observed_expected`).
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025 (17,756 matches here). 2025 holds 2025 and 2025-2026 (18,481).

## Caveats

- **Looks:** 3 ways to divide the season × 5 quantities × 3 readings = 45 tests on all matches, 60 more in the two cohorts, and 9 for the round numbers: 114 tests. The readings of one quantity are not independent, so the true count is lower. But C5 (p = 0.00121) is the only test against the odds on all matches with p below 0.05. A Bonferroni correction over 114 tests gives 0.14. So C5 is a lead. A test needs a new holdout (`notes/ANALYSIS/CLAUDE.md` §6).
- **C5 is clear in one cohort only.** 2024 gives p = 0.000592. 2025 has the same direction but p = 0.328.
- **The run does not tell why** goals increase during a stage, or why the odds miss the first rounds.
- **The raw and the league-season readings agree.** Each league-season puts about a third of its matches into each third. So the league mix does not change from one third to the next.
- **The test treats the matches as independent.** The matches of one league-season are not (`notes/ANALYSIS/CLAUDE.md` §5, rule 5). But each league-season is in every phase, so its level adds to each phase about equally. The league-season reading takes it out.
- **The yardstick's assumptions** (`ALL/ODDS_YARDSTICK.md`): one first-half share for all matches, and goals that are Poisson and independent. Over all matches, the odds expect slightly more goals than happen: O/E 0.9888 (its C1). C5 reads the first rounds against the middle, so this level does not make C5.
- **The round number mixes leagues.** Round 30 is near the end of a league of 30 rounds and in the middle of a league of 46. So the phase (C1–C5) is the better slice. Round numbers above 33 have fewer than 600 matches, from a few leagues.
- **Clusters in one round** are a different question: `ALL/ROUND_CLUSTERS.md`.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run |
