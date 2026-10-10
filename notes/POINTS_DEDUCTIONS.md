# POINTS_DEDUCTIONS — teams whose league took points off them

**Found 2026-10-07** by the final-table check (`qa/final_table.py`) on the 52 DEV schedule seasons:
the page's final points minus the points rebuilt from our results. For every team below, P, W, D, L
and goal difference equal the page, so only the points differ. Every amount matches public reports
(sources at the end). Two more were found on 2026-10-08, and sixteen more on 2026-10-09 in the full
scrape. The entries of leagues removed from the project on 2026-10-10 (four, five, two, then three more) were
taken out, and the rest renumbered.

## How the project treats them (the user, 2026-10-07)

- **Now, option A.** Stage 3 keeps the points earned on the pitch (`s3_<side>_pre_ft_total_points`
  and `_rank`). The amounts are declared in `domain/deductions.py`, which only the final-table
  check reads, so a known deduction does not fail QA. An undeclared one still does.
- **Later, option C.** Stage 3 applies each deduction from the date it was announced, so each
  pre-kickoff table matches the official one at that time. The "when" column is kept for that.
- A deduction changes only `points` and `rank` of the full-time total table. Results and goals
  stay as played.
- **Each entry belongs to one stage** (2026-10-09). The page shows the Apertura and Clausura tables
  apart, so a deduction is declared for the stage whose table carries it. A league without stage
  tabs has the one stage "League".
- **Causes:** financial rules, insolvency, unpaid debts or wages, licensing and crowd
  trouble. None is match-fixing: the one such entry left with its league on 2026-10-10. Turkey
  2024-25 is in both notes, by coincidence: Adana's points went for licence, walk-off and debt
  penalties, not the betting case.

## The list (18 teams, 13 league-seasons)

| # | League (id) | Season | Team (id) | Points | When | Cause |
|---|---|---|---|---|---|---|
| 1 | ITA D2 (40) | 2024-25 | Brescia (163) | −4 | after the last round (May 2025) | financial irregularities (unpaid wages) |
| 2 | ITA D2 (40) | 2024-25 | Cosenza (9206) | −4 | Sep 2024, around round 4 (appeal rejected 11 Oct) | previous season's financial irregularities |
| 3 | POL PR (6) | 2025-26 | Lechia Gdańsk (5910) | −5 | licence decision before the season; counted from round 1 | financial licence criteria F.03, F.04 |
| 4 | SCO CH (150) | 2024-25 | Hamilton Academical (1460) | −15 | 17 Apr 2025 | unpaid players, licence downgrade |
| 5 | SCO L1 (151) | 2024-25 | Inverness CT (78) | −15 | 22 Oct 2024 | administration |
| 6 | SCO L1 (151) | 2024-25 | Dumbarton (1474) | −15 | Nov 2024 (day not found) | administration |
| 7 | SCO L2 (152) | 2024-25 | Bonnyrigg Rose (11804) | −6 | 12 Nov 2024 | licence downgrade (pitch slope) |
| 8 | SCO L2 (152) | 2025-26 | Dumbarton (1474) | −5 | not found | tied to its 2024 administration (one table note only) |
| 9 | SCO L2 (152) | 2025-26 | Edinburgh City (4939) | −15 | insolvency event 22 Jul 2025, before round 1 | provisional liquidator over an unpaid debt |
| 10 | TUR D1 (30) | 2024-25 | Adana Demirspor (5049) | −12 | −3 licence (date not found); −3 for walking off at Galatasaray 9 Feb 2025; −6 FIFA, late Feb 2025 | licence, walk-off, unpaid fees |
| 11 | HOL D2 (17) | 2024-25 | Vitesse (246) | −39 | −6 on 23 Sep 2024 (of 12, the other 6 suspended); −21 on 28 Nov 2024; −3 on 11 Apr 2025; −9 on 22 Apr 2025 | licensing: late and inaccurate financial filings, then takeover information withheld |
| 12 | HOL D2 (17) | 2025-26 | Vitesse (246) | −12 | before round 1; appeal rejected, published 9 Jul 2025 | the −3 of 11 Apr 2025 and −9 of 22 Apr 2025 (licensing), moved into 2025-26 by the appeal ruling |
| 13 | AUS NSW (616) | 2025 | Sydney Olympic (7630) | −3 | 30 Apr 2025 | compliance breaches in the 2025 application process (Football NSW) |
| 14 | AUS NSW (616) | 2025 | Western Sydney Wanderers AM (20722) | −3 | 30 Apr 2025 | as #13 |
| 15 | VEN D1 (391) | 2025, Clausura | Portuguesa (4788) | −3 | 4 Jul 2025, the Clausura's first day | missed debt-payment deadlines |
| 16 | URU D1 (240) | 2025, Apertura | Cerro (2506) | −1 | after round 13 (day not found) | its supporters caused the abandonment of its round-13 match |
| 17 | URU D1 (240) | 2025, Clausura | Nacional (2817) | −3 | during the Clausura (day not found); upheld by CAS | crowd violence at the Torneo Intermedio final |
| 18 | FIN D2 (212) | 2025 | PK-35 Vantaa (2594) | −2 | not found | league licence criteria not met |

**#11 and #12 overlap.** The page's 2024-25 table counts all 39 points, the 12 of April 2025
included, and its 2025-26 table counts those 12 again. The KNVB appeal ruling (published 9 Jul 2025)
puts the 12 in 2025-26; whether the official 2024-25 table kept them is not clear. It matters for
option C only.

**For option C, still missing:** the exact day for #6, #8, Adana's licence step (#10), #16, #17
and #18.

## Adding one

When the final-table check fails on points alone, confirm the deduction in public reports, then
add its total to `domain/deductions.py`, under the stage whose table carries it, and its row, date
and source here.

## Sources

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
- Vitesse: [bet365 news, 6 points](https://news.bet365.nl/nl-nl/article/opnieuw-puntenstraf-voor-vitesse-mindering-van-zes-punten/2024092314334079686), [KNVB, 21 points](https://www.knvb.nl/nieuws/betaald-voetbal/keuken-kampioen-divisie/69921/licentiecommissie-legt-vitesse-straf-op-van-21), [FCUpdate, 3 points](https://www.fcupdate.nl/voetbalnieuws/2025/04/vitesse-nieuws-vitesse-krijgt-opnieuw-drie-punten-in-mindering), [FCUpdate, 9 points](https://www.fcupdate.nl/voetbalnieuws/2025/04/vitesse-krijgt-opnieuw-forse-puntenstraf-van-knvb), [bet365 news, every penalty](https://news.bet365.nl/nl-nl/article/boetes-en-puntenaftrek-alle-straffen-van-vitesse/2025042214352516103)
- Vitesse 2025-26: [VI](https://www.vi.nl/nieuws/vitesse-begint-met-twaalf-minpunten-aan-seizoen-202526), [KNVB, appeal](https://www.knvb.nl/node/70767)
- Sydney Olympic, Western Sydney Wanderers: [Football NSW](https://footballnsw.com.au/2025/04/30/clubs-sanctioned-for-compliance-breaches-of-the-2025-application-process/), [Greek Herald](https://greekherald.com.au/?p=177014)
- Portuguesa: [Wikipedia, 2025 Liga FUTVE table note](https://en.wikipedia.org/wiki/2025_Liga_FUTVE) (it cites La Vinotinto, 4 Jul 2025)
- Cerro and Nacional: [RSSSF, Uruguay 2025](https://rsssf.org/tablesu/uru2025.html), [El Observador](https://www.elobservador.com.uy/futbol/cuando-los-hinchas-pierden-partidos-los-puntos-que-le-han-quitado-nacional-penarol-y-otros-equipos-violencia-sus-tribunas-este-siglo-n6022096). Cerro's has this one source only.
- PK-35 Vantaa: [Wikipedia, 2025 Ykkösliiga table note](https://en.wikipedia.org/wiki/2025_Ykk%C3%B6sliiga)
