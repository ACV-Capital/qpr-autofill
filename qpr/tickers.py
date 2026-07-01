"""Canonical SEA-5 retail ticker manifest loader."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass(frozen=True)
class Ticker:
    exchange: str   # IDX, SET, KLSE, PSE, HSX, SGX
    ticker: str
    company: str
    subsector: str
    sssg_applicable: bool  # True only for retail/F&B chains
    notes: str = ""


def load_manifest(path: str | Path) -> list[Ticker]:
    """Load the SEA-5 retail ticker manifest from a YAML file."""
    data = yaml.safe_load(Path(path).read_text())
    return [Ticker(**row) for row in data]
