from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def sample_csv_path() -> Path:
    return Path("examples/sample_data/l2_sample.csv")
