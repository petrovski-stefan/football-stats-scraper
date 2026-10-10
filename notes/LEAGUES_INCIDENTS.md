# LEAGUES_INCIDENTS — known integrity incidents in the LEAGUES.txt leagues

**Written 2026-09-30, before the multi-country scrape.** Fairness is this project's priority, so this list is fixed in writing before any data exists for these leagues.

## Read this first

**Source.** Everything below comes from Claude's general knowledge (training data up to about mid-2026). None of it was checked against a source, because this project makes no web requests outside `config/LEAGUES.txt`. Treat each entry as a lead to verify, not as a fact. **Before an entry is used to justify dropping a league, verify its dates, seasons and leagues.** Each entry carries a confidence label: high, medium or low.

**Data window.** The catalogue holds the newest 3 seasons per league: 2024-25, 2025-26 and 2026-27 for cross-year leagues, and 2024, 2025 and 2026 for calendar-year leagues. An incident is "in the window" only when the affected matches or standings fall inside those seasons. When the charges came later is irrelevant.

**How this list may be used (agreed 2026-09-30):**

1. Every league here is scraped like any other league.
2. A keep/drop decision about these leagues uses **data-quality checks only**:
   - odds coverage;
   - postponement rate (the out-of-round flag, from round and date);
   - unusual odds movement between the opening and the pre-kickoff 1X2 prices.
3. The decision **never** uses comeback or over-6.5 rates. A league dropped because its outcomes look strange is chosen by its results, and that makes the whole analysis unfair.
4. Record every removal together with the check that triggered it.

The user expects most of the leagues in sections 1 and 2 to be removed after scraping.

---

## 1. Incidents inside the data window — CAREFULLY READ THE DATA

### Turkey — Süper Lig

- **Incident (late 2025):** the Turkish federation found that about 150 of about 570 active referees held betting accounts, and that some of them bet on football matches. About 1,000 players were then referred for betting. Referees and at least one club president were arrested, and lower-league matches (2. Lig, 3. Lig) were paused for about two weeks.
- **Window impact:** the betting activity covered several seasons, including 2024-25 and 2025-26. Referee decisions (cards, penalties) in those seasons are the risk.
- **Confidence:** medium-high for the scandal. Medium for the numbers.

**CAREFULLY READ THE DATA**

| League | 2026-2027 | 2025-2026 | 2024-2025 |
|---|---|---|---|
| Turkey Super Lig (TUR D1) | [link](https://football.nowgoal26.com/league/2026-2027/30) | [link](https://football.nowgoal26.com/league/2025-2026/30) | [link](https://football.nowgoal26.com/league/2024-2025/30) |

### China — Super League, Jia League, Yi League

- **Incident:** a multi-year anti-corruption crackdown led to a 2024 announcement. About 128 matches were found fixed across the professional tiers, and about 43 people were banned for life. Clubs were given **points deductions that apply to a later season**.
- **Window impact:** as far as I know, the fixed matches themselves are mostly from seasons before 2024. The points deductions land inside the window, and they distort standings positions no matter what happened on the pitch. **Uncertain:** whether the deductions apply to 2025, to 2026, or to both, and which clubs they hit. Verify this first.
- **Confidence:** high for the crackdown and the bans. Medium to low for the numbers and the affected season.

**CAREFULLY READ THE DATA**

| League | 2026 | 2025 | 2024 |
|---|---|---|---|
| Chinese Super League (CHA CSL) | [link](https://football.nowgoal26.com/league/2026/60) | [link](https://football.nowgoal26.com/league/2025/60) | [link](https://football.nowgoal26.com/league/2024/60) |
| Chinese FA Jia League (CHA D1) | [link](https://football.nowgoal26.com/league/2026/61) | [link](https://football.nowgoal26.com/league/2025/61) | [link](https://football.nowgoal26.com/league/2024/61) |
| Chinese FA Yi League (CHA D2) | [link](https://football.nowgoal26.com/league/2026/686) | [link](https://football.nowgoal26.com/league/2025/686) | [link](https://football.nowgoal26.com/league/2024/686) |

---

## 2. Watch list — all Australian leagues (user decision, 2026-09-30)

No known incident falls inside the data window. The user decided to examine **every** Australian league very carefully anyway, for these reasons:

- **Known cases just before the window:**
  - **Victorian Premier League (likely the "VIC Premier League" below, now NPL Victoria):** in 2013, Southern Stars FC fixed matches for a betting syndicate with overseas links. Players and the coach were charged. Confidence: high.
- **Structural risk:**
  - Kick-off times suit Asian betting markets, so these leagues draw large international betting volume for their low profile.
  - Most of the leagues are semi-professional.
  - Markets are thin.
  - Some entries are tier 3–5 or regional.

**CAREFULLY READ THE DATA**

| League | newest | middle | oldest |
|---|---|---|---|
| NSW Premier League (AUS NSW) | [2026](https://football.nowgoal26.com/league/2026/616) | [2025](https://football.nowgoal26.com/league/2025/616) | [2024](https://football.nowgoal26.com/league/2024/616) |
| VIC Premier League (AUS VPL) | [2026](https://football.nowgoal26.com/league/2026/436) | [2025](https://football.nowgoal26.com/league/2025/436) | [2024](https://football.nowgoal26.com/league/2024/436) |
| Victorian State League Division 1 (Aus VD1) | [2026](https://football.nowgoal26.com/league/2026/1073) | [2025](https://football.nowgoal26.com/league/2025/1073) | [2024](https://football.nowgoal26.com/league/2024/1073) |
| National Premier Leagues Western Australia (WAUS D1) | [2026](https://football.nowgoal26.com/league/2026/481) | [2025](https://football.nowgoal26.com/league/2025/481) | [2024](https://football.nowgoal26.com/league/2024/481) |

---

## 3. Incidents just before the data window (no links)

These matches fall outside the scraped seasons. They show that the risk is real in these leagues. They do not taint the data.

| League(s) in LEAGUES.txt | Incident | Confidence |
|---|---|---|
| Brazil: Serie A, Serie B | 2023, "Operação Penalidade Máxima": players were paid to get yellow cards or concede penalties in 2022–23 national and state-championship matches, and many were banned. In 2025, Flamengo's Bruno Henrique was charged over a yellow card in a 2023 Serie A match. | high |
| England: Premier League | Lucas Paquetá was charged by the FA in 2024 over yellow cards in 2022-23. **He was cleared in 2025**, so no fixing was proven. | high |

## 4. Older incidents (structural risk only)

These are long before the data window. They say something about a league's history, and nothing about the scraped seasons.

| League(s) in LEAGUES.txt | Year | Incident | Confidence |
|---|---|---|---|
| Spain: La Liga 2 and lower tiers | 2019 | "Operación Oikos": arrests over fixed second-tier and lower-tier matches | high |
| Spain: La Liga | 2014 | Osasuna club officials paid opponents (2013-14 matches), with convictions in 2020 | high |
| Portugal: Liga Portugal 2 | 2016 | Second-tier fixing investigation linked to Asian betting | medium |
| Greece: Super League, National B | 2011 | "Koriopolis" fixing scandal | high |
| Belgium: Pro League, Second Division | 2018 | "Operation Clean Hands": referees, agents, and a relegation match | high |
| Czech Republic: top tiers | 2020 | Referee corruption case involving a federation vice-president | high |
| Finland: Veikkausliga | 2011 | Wilson Raj Perumal's fixing ring (convictions in Finland) | high |
| Albania: Super League | 2018 | Skënderbeu banned from UEFA competition for fixing | high |
| Estonia: Meistriliiga | 2014 | Players banned for fixing | medium |
| Ireland: First Division | 2017 | Athlone Town players banned for fixing | medium-high |
| Ukraine: Premier League | 2018 | Police investigation into fixed matches in the top tiers | medium |
| Cyprus: 1 Division | 2010s | Repeated UEFA suspicious-betting alerts | medium |
| Malta: Premier League | 2010s | Several players banned for fixing | medium |
| South Korea: K League | 2011 | Fixing scandal with dozens of players banned | high |
| Vietnam: V.League | 2014 | Ninh Bình players convicted of fixing | medium-high |
| Thailand: Thai League | 2017 | Referees arrested over fixing | medium |
| Indonesia: top tiers | 2018–19 | A police anti-fixing task force arrested federation officials and others | medium-high |
| Ghana: Premier League | 2018 | "Number 12" undercover exposé of referee and official bribery; the federation was dissolved | high |
| South Africa: Premier Soccer League | 2004 | Referees arrested over fixing | medium |

## 5. Every other league in LEAGUES.txt

Claude knows of no incident in any other league in the file. **The absence of a known case is not evidence of clean data.** The outcome-blind checks in "Read this first" apply to every league. The leagues on this page simply get them first and most carefully.
