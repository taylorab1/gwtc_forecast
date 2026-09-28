from __future__ import annotations

from typing import Mapping, Protocol

import numpy as np


class PopulationModel(Protocol):
    name: str

    def log_prob(
        self,
        samples: Mapping[str, np.ndarray],
        hyperparameters: Mapping[str, float],
    ) -> np.ndarray:
        """Return the normalized log population density for each sample."""
