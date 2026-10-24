"""Printing shared by the runners, so every runner's output reads the same way."""

import pandas as pd


def show(title: str, df: pd.DataFrame) -> None:
    """Print one table under a title, floats to 4 decimals."""

    print(f"\n== {title}")
    print(df.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
