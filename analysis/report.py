"""Printing shared by the runners, so every runner's output reads the same way."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ValueColumn:
    """One column of a printed table of unit values: the `column` of the unit values of the
    quantity with the label `quantity`, under the header `header`."""

    quantity: str
    column: str
    header: str


def show(title: str, df: pd.DataFrame) -> None:
    """Print one table under a title, floats to 4 decimals."""

    print(f"\n== {title}")
    print(df.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
