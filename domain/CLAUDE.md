# domain/ — contracts, paths and the derived-stat kernel

Imports nothing internal.

## 1. Stage-1 models hold page values only; derived fields live in later stages

The staged pipeline (`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`, fields in `notes/FIELDS/`) splits every source into three stages. The stage-1 models (`domain/schedule.py:ScheduleRow`, `FinalTableRow`) accept values read from the page and nothing computed: `extra="forbid"` refuses a derived field. A field computed from one row goes in a stage-2 builder (`features/schedule_row.py`); a field that needs other rows goes in a stage-3 builder (`features/schedule_multi.py`). New DOM extraction goes in `scrapers/parsers.py` (see `scrapers/CLAUDE.md` §3).

`stats.py` is the per-match kernel the builders and the detail records share (comeback, 1X2 result, implied and margin-free probabilities). `standings.py` rebuilds a standings table from results. Both are pure.

Field names are column names, and carry the code of the doc that defines them (`s1_`, `s2_`, `s3_`; row keys like `match_id` stay bare): `notes/FIELDS/README.md`. No score strings beside the goal ints; no rounding in stored values.

The old `domain/match.py:Match`, which computed every derived column as a `@computed_field` inside the raw file, was removed on 2026-10-06 (`notes/LOG/MIGRATIONS.md`). The detail model (`match_detail.py`) still works the old way until plan step P4.

## 1a. One clock: Berlin time with its offset

Every stored time is Berlin time with its offset written (`2026-01-31 18:30+01:00`): `domain/clock.py`. **For order and durations use `clock.parse_instant` (UTC); `clock.parse_berlin` is for the date and the weekday only.** Python compares two datetimes of the same zone by their wall clocks and ignores the offset, so on the autumn night 02:30+02:00 and 02:30+01:00 come out equal (`tests/domain/test_clock.py` keeps that trap visible).

## 2. Season labels come in two shapes and are stored verbatim

`2025-2026` for cross-year leagues, `2025` for calendar-year ones. They are **not** normalised into a common form, because an English 2025-2026 season (Aug–May) and a Norwegian 2025 season (Mar–Nov) are different things and writing `2025-2025` would invent a fact.

The consequences below are all real bugs that have been fixed but are easy to reintroduce:

- (a) Never slice a season out of a filename by fixed width — use `domain/paths.py:split_league_season`, since a 9-char assumption turns `norway_eliteserien_2025` into `("norway_elites", "rien_2025")`.
- (b) Labels from the two conventions **never compare equal** even when contemporaneous, so `groupby("season")` splits them and an `isin([...])` season list matches neither. Use `domain/schedule.py:season_start_year` (moved from `domain/match.py` on 2026-10-06) when you mean "which seasons overlap in time".

Sorting is safe as strings (the start year is a fixed-width prefix).
