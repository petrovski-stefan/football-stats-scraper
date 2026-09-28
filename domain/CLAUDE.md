# domain/ — contracts, paths and the derived-stat kernel

Imports nothing internal.

## 1. Derived columns are computed fields

Every derived column — goals splits, results, market flags, date and odds derivations — is a `@computed_field` on `domain/match.py:Match`, computed from `domain/stats.py`. New arithmetic on already-scraped values goes on the model or in `stats.py`; new DOM extraction goes in `scrapers/parsers.py` (see `scrapers/CLAUDE.md` §3). The one exception is `match_index_in_round` (`scrapers/CLAUDE.md` §4).

`stats.py` is shared by the `Match` model and the detail records: per-match derived stats (over2.5, BTTS, comeback, 1X2 result, implied prob) live there, not in the scrapers.

Raw score strings (`ht_score`, `ft_score`) are kept alongside the derived goal ints.

## 2. Season labels come in two shapes and are stored verbatim

`2025-2026` for cross-year leagues, `2025` for calendar-year ones. They are **not** normalised into a common form, because an English 2025-2026 season (Aug–May) and a Norwegian 2025 season (Mar–Nov) are different things and writing `2025-2025` would invent a fact.

The consequences below are all real bugs that have been fixed but are easy to reintroduce:

- (a) Never slice a season out of a filename by fixed width — use `domain/paths.py:split_league_season`, since a 9-char assumption turns `norway_eliteserien_2025` into `("norway_elites", "rien_2025")`.
- (b) Labels from the two conventions **never compare equal** even when contemporaneous, so `groupby("season")` splits them and an `isin([...])` season list matches neither. Use `domain/match.py:season_start_year` when you mean "which seasons overlap in time".

Sorting is safe as strings (the start year is a fixed-width prefix).
