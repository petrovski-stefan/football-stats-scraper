"""Points deductions: points a league took off a club, which a table rebuilt from results
cannot see.

Stage 3 keeps the points earned on the pitch (option A, the user's decision, 2026-10-07),
so only the final-table check (`qa/final_table.py`) reads this list: a declared deduction
does not fail it. The date, cause and source of each entry are in
`notes/REFERENCE/POINTS_DEDUCTIONS.md`. Later (option C) stage 3 applies each one from its date.

An entry belongs to one stage, because the page shows each stage's table on its own: an
Apertura deduction is not in the Clausura table. A league without stage tabs has the one
stage "League".
"""

# (league id, season, stage, team id) -> the stage's total deduction, negative.
POINTS_DEDUCTIONS: dict[tuple[int, str, str, int], int] = {
    (40, "2024-2025", "League", 163): -4,  # Brescia
    (40, "2024-2025", "League", 9206): -4,  # Cosenza
    (6, "2025-2026", "League", 5910): -5,  # Lechia Gdansk
    (150, "2024-2025", "League", 1460): -15,  # Hamilton Academical
    (151, "2024-2025", "League", 78): -15,  # Inverness Caledonian Thistle
    (151, "2024-2025", "League", 1474): -15,  # Dumbarton
    (152, "2024-2025", "League", 11804): -6,  # Bonnyrigg Rose
    (152, "2025-2026", "League", 1474): -5,  # Dumbarton
    (152, "2025-2026", "League", 4939): -15,  # Edinburgh City
    (30, "2024-2025", "League", 5049): -12,  # Adana Demirspor
    (17, "2024-2025", "League", 246): -39,  # Vitesse
    (17, "2025-2026", "League", 246): -12,  # Vitesse
    (616, "2025", "League", 7630): -3,  # Sydney Olympic
    (616, "2025", "League", 20722): -3,  # Western Sydney Wanderers (academy side)
    (391, "2025", "Clausura", 4788): -3,  # Portuguesa
    (240, "2025", "Apertura", 2506): -1,  # Cerro
    (240, "2025", "Clausura", 2817): -3,  # Nacional
    (212, "2025", "League", 2594): -2,  # PK-35 Vantaa
}

# Where the page's final table applies less than the official total above, the amount it
# does apply, under the same key. Only the final-table check reads it; the official total
# stays the entry above. Empty since 2026-10-10: its one entry (the user's exception of that
# day) left the project with its league.
PAGE_TOTALS: dict[tuple[int, str, str, int], int] = {}


def _stage_entries(
    table: dict[tuple[int, str, str, int], int], league_id: int, season: str, stage: str
) -> dict[int, int]:
    return {
        team: points
        for (league, label, part, team), points in table.items()
        if league == league_id and label == season and part == stage
    }


def deducted(league_id: int, season: str, stage: str) -> dict[int, int]:
    """Each team's official total deduction in one stage of a league-season, by team id."""

    return _stage_entries(POINTS_DEDUCTIONS, league_id, season, stage)


def on_page(league_id: int, season: str, stage: str) -> dict[int, int]:
    """Each team's deduction as the page's final table applies it, by team id: the official
    total, or the page's own figure where `PAGE_TOTALS` holds one."""

    return deducted(league_id, season, stage) | _stage_entries(
        PAGE_TOTALS, league_id, season, stage
    )
