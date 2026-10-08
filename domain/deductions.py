"""Points deductions: points a league took off a club, which a table rebuilt from results
cannot see.

Stage 3 keeps the points earned on the pitch (option A, the user's decision, 2026-10-07),
so only the final-table check (`qa/final_table.py`) reads this list: a declared deduction
does not fail it. The date, cause and source of each entry are in
`notes/POINTS_DEDUCTIONS.md`. Later (option C) stage 3 applies each one from its date.
"""

# (league id, season, team id) -> the season's total deduction, negative.
POINTS_DEDUCTIONS: dict[tuple[int, str, int], int] = {
    (36, "2023-2024", 31): -8,  # Everton
    (36, "2023-2024", 49): -4,  # Nottingham Forest
    (37, "2024-2025", 51): -2,  # Sheffield United
    (37, "2025-2026", 336): -18,  # Sheffield Wednesday
    (37, "2025-2026", 59): -6,  # Leicester City
    (37, "2025-2026", 18): -2,  # West Bromwich Albion
    (40, "2024-2025", 163): -4,  # Brescia
    (40, "2024-2025", 9206): -4,  # Cosenza
    (6, "2025-2026", 5910): -5,  # Lechia Gdansk
    (150, "2024-2025", 1460): -15,  # Hamilton Academical
    (151, "2024-2025", 78): -15,  # Inverness Caledonian Thistle
    (151, "2024-2025", 1474): -15,  # Dumbarton
    (152, "2024-2025", 11804): -6,  # Bonnyrigg Rose
    (152, "2025-2026", 1474): -5,  # Dumbarton
    (152, "2025-2026", 4939): -15,  # Edinburgh City
    (30, "2024-2025", 5049): -12,  # Adana Demirspor
}


def deducted(league_id: int, season: str) -> dict[int, int]:
    """Each team's total deduction in one league-season, by team id."""
    return {
        team: points
        for (league, label, team), points in POINTS_DEDUCTIONS.items()
        if league == league_id and label == season
    }
