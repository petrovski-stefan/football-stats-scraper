"""Printing shared by the runners, so every runner's output reads the same way."""

import pandas as pd


def show(title: str, table: pd.DataFrame) -> None:
    """Print one table under a title, floats to 4 decimals."""
    print(f"\n== {title}")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
