"""Reading a fixture's history blocks, shared by the goal and event feature builders.

Both `features/goals.py` and `features/events.py` answer the same question about a
fixture — "which matches are in this side's recent form, and which team in each of them is
the subject?" — before diverging on what they measure. That resolution lives here so the
two cannot disagree about which history matches count.

The history blocks are the `<section>_last<n>_*` columns written by
`scrapers/detail_parsers.py:flatten_history`, where `last1` is the most recent match and
every field is already oriented to the section's subject team.
"""

from collections.abc import Callable, Sequence
from typing import Any

import pandas as pd

from domain import scope

SECTIONS = ("home", "away", "h2h")
# Cell values that mean "the subject played at home" once stringified by pandas.
_TRUTHY = ("true", "1", "1.0")


def cell(detail_df: pd.DataFrame, column: str, row: int) -> str:
    """A history-block cell as a clean string; "" when the column or value is absent.

    Trailing ".0" is stripped because pandas reads an integer column with any gap in it as
    float, which turns a match id into "2789133.0" and breaks every lookup keyed on it.
    """

    if column not in detail_df.columns:
        return ""

    raw_value = detail_df[column].iloc[row]
    if raw_value is None or pd.isna(raw_value):
        return ""

    text = str(raw_value).strip()

    return text[:-2] if text.endswith(".0") else text


def subject_is_home(detail_df: pd.DataFrame, prefix: str, row: int) -> bool | None:
    """Whether the section's subject team played at home in that history match.

    None when the venue is unknown, which makes the match unusable: "for" and "against" then
    have no orientation, and a guess would invert half the rows."""

    raw = cell(detail_df, f"{prefix}is_home", row)
    if raw == "":
        return None

    return raw.lower() in _TRUTHY


def match_key(detail_df: pd.DataFrame, prefix: str, row: int) -> str | None:
    """The referenced match's id, or None when it is missing or out of scope.

    Out of scope: a friendly (no minute data) or a pre-2023 page (truncated event lists), both
    found by measurement (`domain/scope.py`)."""

    match_id = cell(detail_df, f"{prefix}match_id", row)
    if not match_id:
        return None
    if not scope.in_scope(
        cell(detail_df, f"{prefix}league", row), cell(detail_df, f"{prefix}date", row)
    ):
        return None

    return match_id


def score_matches(detail_df: pd.DataFrame, prefix: str, row: int, home: int, away: int) -> bool:
    """Do `home`-`away` reproduce the score the history block records for that match?

    True when the block has no score to check. Both builders need it: two of four goals found
    give a wrong scoreline, not a missing one, for goal timings and card states alike."""

    stored_home = cell(detail_df, f"{prefix}ft_home_goals", row)
    stored_away = cell(detail_df, f"{prefix}ft_away_goals", row)
    if stored_home == "" or stored_away == "":
        return True

    return (home, away) == (int(stored_home), int(stored_away))


# --- The shared build shape ---------------------------------------------------
# `features/goals.py` and `features/events.py` produce the same *structure* — per-section
# numeric aggregates plus one lossless timeline string per history match — and differ only
# in what they read out of a match. Keeping the structure here means a change to the shape
# (a new section, a different depth) cannot land in one module and not the other.


def feature_names(suffixes: Sequence[str]) -> list[str]:
    """`<section>_<suffix>` for every section, in order."""

    return [f"{section}_{suffix}" for section in SECTIONS for suffix in suffixes]


def timeline_names(field: str, depth: int) -> list[str]:
    """`<section>_last<n>_<field>` for every section and depth, in order."""

    names: list[str] = []
    for section in SECTIONS:
        names.extend(f"{section}_last{slot}_{field}" for slot in range(1, depth + 1))

    return names


def build_frame[T](
    detail_df: pd.DataFrame,
    depth: int,
    suffixes: Sequence[str],
    timelines: Sequence[tuple[str, Callable[[T | None], str]]],
    resolve: Callable[[str, int], T | None],
    rates: Callable[[list[T | None]], dict[str, float]],
) -> pd.DataFrame:
    """One row per fixture: every section's aggregates, then every timeline.

    One resolution per history match feeds every output, so a timeline is non-empty exactly
    when its match fed the aggregate, and the event kinds cannot drift apart on what counted.

    Args:
        timelines: a `(column field, renderer)` pair per string to emit: one for goals, one per
            kind for events, so a red card is not buried among substitutions.
        resolve: `(prefix, row)` to one history match's contents from the subject team's view,
            None when unusable.
    """

    built: dict[str, Any] = {}
    for section in SECTIONS:
        per_row = _resolve_section(detail_df, section, depth, resolve)
        built.update(_aggregates(section, suffixes, [rates(blocks) for blocks in per_row]))
        for field, render in timelines:
            built.update(_timelines(section, depth, field, per_row, render))

    return pd.DataFrame(built, index=detail_df.index)


def _resolve_section[T](
    detail_df: pd.DataFrame, section: str, depth: int, resolve: Callable[[str, int], T | None]
) -> list[list[T | None]]:
    """For each fixture row, that section's `depth` history matches, oldest slot last.

    A match that `resolve` finds unusable is None."""

    per_row: list[list[T | None]] = []
    for row in range(len(detail_df)):
        per_row.append([resolve(f"{section}_last{slot}_", row) for slot in range(1, depth + 1)])

    return per_row


def _aggregates(
    section: str, suffixes: Sequence[str], stats: list[dict[str, float]]
) -> dict[str, Any]:
    """One column `<section>_<suffix>` per suffix, from each fixture row's rates."""

    columns: dict[str, Any] = {}
    for suffix in suffixes:
        columns[f"{section}_{suffix}"] = [row_rates[suffix] for row_rates in stats]

    return columns


def _timelines[T](
    section: str,
    depth: int,
    field: str,
    per_row: list[list[T | None]],
    render: Callable[[T | None], str],
) -> dict[str, Any]:
    """One column `<section>_last<slot>_<field>` per slot, each history match rendered."""

    columns: dict[str, Any] = {}
    for slot in range(1, depth + 1):
        columns[f"{section}_last{slot}_{field}"] = [render(blocks[slot - 1]) for blocks in per_row]

    return columns
