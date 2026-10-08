# POINTS_DEDUCTIONS — teams whose league took points off them

**Found 2026-10-07** by the final-table check (`qa/final_table.py`) on the 52 DEV schedule seasons:
the page's final points minus the points rebuilt from our results. For every team below, P, W, D, L
and goal difference equal the page, so only the points differ. Every amount matches public reports
(sources at the end).

## How the project treats them (the user, 2026-10-07)

- **Now, option A.** Stage 3 keeps the points earned on the pitch (`s3_<side>_pre_ft_total_points`
  and `_rank`). The amounts are declared in `domain/deductions.py`, which only the final-table
  check reads, so a known deduction does not fail QA. An undeclared one still does.
- **Later, option C.** Stage 3 applies each deduction from the date it was announced, so each
  pre-kickoff table matches the official one at that time. The "when" column is kept for that.
- A deduction changes only `points` and `rank` of the full-time total table. Results and goals
  stay as played.
- **Not match-fixing.** None comes from an integrity case (`LEAGUES_INCIDENTS.md`). The causes are
  financial rules, insolvency, unpaid debts and licensing. Turkey 2024-25 is in both notes, by
  coincidence: Adana's points went for licence, walk-off and debt penalties, not the betting case.

## The list (16 teams, 10 league-seasons)

| # | League (id) | Season | Team (id) | Points | When | Cause |
|---|---|---|---|---|---|---|
| 1 | ENG PR (36) | 2023-24 | Everton (31) | −8 | −10 on 17 Nov 2023; +4 on appeal 26 Feb 2024; −2 on 8 Apr 2024 | spending rules (PSR), two charges |
| 2 | ENG PR (36) | 2023-24 | Nottingham Forest (49) | −4 | 18 Mar 2024 | spending rules (PSR) |
| 3 | ENG LCH (37) | 2024-25 | Sheffield United (51) | −2 | announced Apr 2024; counted from round 1 | late payments to other clubs in 2022-23 |
| 4 | ENG LCH (37) | 2025-26 | Sheffield Wednesday (336) | −18 | −12 on 24 Oct 2025; −6 on 1 Dec 2025 | administration; then unpaid wages and tax |
| 5 | ENG LCH (37) | 2025-26 | Leicester City (59) | −6 | 5 Feb 2026 (appeal rejected 8 Apr) | spending rules (PSR), accounts not provided |
| 6 | ENG LCH (37) | 2025-26 | West Bromwich Albion (18) | −2 | 24 Apr 2026 | spending rules (PSR) |
| 7 | ITA D2 (40) | 2024-25 | Brescia (163) | −4 | after the last round (May 2025) | financial irregularities (unpaid wages) |
| 8 | ITA D2 (40) | 2024-25 | Cosenza (9206) | −4 | Sep 2024, around round 4 (appeal rejected 11 Oct) | previous season's financial irregularities |
| 9 | POL PR (6) | 2025-26 | Lechia Gdańsk (5910) | −5 | licence decision before the season; counted from round 1 | financial licence criteria F.03, F.04 |
| 10 | SCO CH (150) | 2024-25 | Hamilton Academical (1460) | −15 | 17 Apr 2025 | unpaid players, licence downgrade |
| 11 | SCO L1 (151) | 2024-25 | Inverness CT (78) | −15 | 22 Oct 2024 | administration |
| 12 | SCO L1 (151) | 2024-25 | Dumbarton (1474) | −15 | Nov 2024 (day not found) | administration |
| 13 | SCO L2 (152) | 2024-25 | Bonnyrigg Rose (11804) | −6 | 12 Nov 2024 | licence downgrade (pitch slope) |
| 14 | SCO L2 (152) | 2025-26 | Dumbarton (1474) | −5 | not found | tied to its 2024 administration (one table note only) |
| 15 | SCO L2 (152) | 2025-26 | Edinburgh City (4939) | −15 | insolvency event 22 Jul 2025, before round 1 | provisional liquidator over an unpaid debt |
| 16 | TUR D1 (30) | 2024-25 | Adana Demirspor (5049) | −12 | −3 licence (date not found); −3 for walking off at Galatasaray 9 Feb 2025; −6 FIFA, late Feb 2025 | licence, walk-off, unpaid fees |

**For option C, still missing:** the exact day for #12, #14 and Adana's licence step.

## Adding one

When the final-table check fails on points alone, confirm the deduction in public reports, then
add its total to `domain/deductions.py` and its row, date and source here.

## Sources

- Everton: [CBS, appeal](https://www.cbssports.com/soccer/news/evertons-punishment-for-premier-league-financial-rules-violations-reduced-from-10-to-six-points-on-appeal), [second deduction](https://www.pressreader.com/nigeria/the-guardian-nigeria/20240409/282050512093897)
- Nottingham Forest: [Eurosport](https://www.eurosport.com/football/premier-league/2023-2024/nottingham-forest-deducted-four-points-for-breaching-premier-league-profitability-and-sustainability_sto10068528/story.shtml)
- Sheffield United: [Insider Sport](https://insidersport.com/2024/04/12/sheffield-utd-points-deduction/)
- Sheffield Wednesday: [beIN, 12 points](https://www.beinsports.com/en-au/football/championship/articles/wednesday-punished-after-filing-for-administration-2025-10-24)
- Leicester: [Premier League statement](https://www.premierleague.com/en/news/4581043/premier-league-statement-leicester-city-05-february-2026), [appeal](https://prod.beinsports.com/en-au/football/championship/articles/leicester-fails-appeal-against-six-point-deduction-2026-04-08)
- West Brom: [Sky Sports](https://www.skysports.com/football/news/12040/13535990/west-brom-handed-immediate-two-point-deduction-in-championship-for-breaching-efl-financial-rules)
- Brescia: [Football Italia](https://football-italia.net/late-points-deduction-could-save-sampdoria/)
- Cosenza: [Total Italian Football](https://www.total-italianfootball.com/news/418156809734/serie-b-matchday-4-talking-points-pisa-joint-leaders-sampdoria-still-winless-cosenza-deducted-four-points), [Tuttosport, appeal](https://www.tuttosport.com/news/calcio/serie-b/cosenza/2024/10/11-133980995/cosenza_penalizzazione_confermata_i_dettagli_sul_ricorso_respinto)
- Lechia Gdańsk: [Soccerway](https://pl.soccerway.com/wiadomosci/pi-ka-nozna-pko-bp-ekstraklasa-oficjalnie-lechia-z-licencja-na-nowy-sezon-i-piecioma-ujemnymi-punktami/S6rV9Qsf), [club statement](https://lechia.pl/en/lechia-gdansk-statement-5/)
- Hamilton: [The Scotsman](https://www.scotsman.com/sport/football/scottish-championship/scottish-football-club-docked-15-points-and-stare-relegation-in-face-after-multiple-rule-breaches-5089852)
- Inverness: [Insider](https://www.insider.co.uk/news/inverness-caley-thistle-confirm-administration-33950268)
- Dumbarton 2024-25: [STV](https://news.stv.tv/sport/dumbarton-deducted-15-points-after-club-placed-into-administration)
- Bonnyrigg Rose: [SPFL statement](https://spfl.co.uk/news/spfl-statement-bonnyrigg-rose-fc)
- Dumbarton 2025-26: [Sky Sports table](https://www.skysports.com/football/edinburgh-city-vs-dumbarton/table/532102)
- Edinburgh City: [SPFL statement](https://spfl.co.uk/news/spfl-statement-edinburgh-city-50695), [STV, appeal](https://news.stv.tv/sport/edinburgh-city-launch-appeal-against-15-point-deduction)
- Adana Demirspor: [Wikipedia](https://en.wikipedia.org/wiki/2024%E2%80%9325_Adana_Demirspor_season), [beIN](https://www.beinsports.com/en-us/soccer/sper-lig/articles-video/minus-2-points-how-adana-are-bending-reality-in-the-super-lig-2025-04-25?c=us)
