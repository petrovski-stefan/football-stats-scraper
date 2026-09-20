"""A pair of Poisson regressions (home, away) sharing one standardised design matrix.

Extracted because `features/chain.py:Factor1` and `modelling/scoreline.py:_RatePair`
had drifted into near-copies — same constructor, a byte-identical `_design`, the same
`rates`, differing only in where `fit` got its targets from. Two independent copies of
the standardisation step is the dangerous kind of duplication: fixing a scaling bug in
one and not the other would silently change one study's numbers and not the other's.

Standardisation statistics are learned on the fit frame and reused verbatim at predict
time. That direction matters — recomputing means and stds on the test frame would leak
its distribution into the prediction, which is exactly what the leak checks in both
callers exist to catch.

It lives in `features/` rather than `modelling/` so both callers can reach it: the layer
direction allows `modelling -> features`, never the reverse (see CLAUDE.md).
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor


class RatePair:
    """Two Poisson regressions (home, away) sharing a standardised design matrix."""

    def __init__(self, feature_names: list[str], alpha: float = 1.0):
        self.feature_names = feature_names
        self.home = PoissonRegressor(alpha=alpha, max_iter=1000)
        self.away = PoissonRegressor(alpha=alpha, max_iter=1000)
        self.means: pd.Series[Any] | None = None
        self.stds: pd.Series[Any] | None = None

    def _design(self, x: pd.DataFrame, fit: bool = False) -> np.ndarray:
        x = x[self.feature_names].astype(float)
        if fit:
            self.means = x.mean()
            self.stds = x.std().replace(0.0, 1.0)
        assert self.means is not None and self.stds is not None
        return ((x - self.means) / self.stds).fillna(0.0).to_numpy()

    def fit(self, x: pd.DataFrame, y_home: np.ndarray, y_away: np.ndarray) -> "RatePair":
        design = self._design(x, fit=True)
        self.home.fit(design, y_home)
        self.away.fit(design, y_away)
        return self

    def rates(self, x: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        design = self._design(x)
        return self.home.predict(design), self.away.predict(design)
