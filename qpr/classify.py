"""Cell-level comparison between working and reference values."""
from __future__ import annotations
from enum import Enum


class Status(str, Enum):
    MATCH = "match"
    DIFFER = "differ"
    MISSING = "missing"   # working null, ref has value
    EXTRA = "extra"       # working has value, ref null


DEFAULT_TOLERANCE = 0.5  # 0.5pp for rounded SSSG, 0.05pp for primary 2-decimal


def classify(
    working: float | int | str | None,
    reference: float | int | str | None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Status:
    """Compare two SSSG-style percentage values.

    - both None → MATCH (correctly null in both)
    - working None, ref has value → MISSING (need to research)
    - working has value, ref None → EXTRA (we found something the ref didn't)
    - both have values, |w - r| <= tolerance → MATCH
    - otherwise → DIFFER (real public-source disagreement)
    """
    w = _to_float(working)
    r = _to_float(reference)

    if w is None and r is None:
        return Status.MATCH
    if w is None:
        return Status.MISSING
    if r is None:
        return Status.EXTRA
    if abs(w - r) <= tolerance:
        return Status.MATCH
    return Status.DIFFER


def _to_float(v) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        # accept "5.4", "5.4%", " 5.4 ", "5,4" (European), or "1,234.5"
        s = str(v).strip().rstrip("%").strip()
        # If both "," and "." are present, assume "," is thousands sep
        if "," in s and "." in s:
            s = s.replace(",", "")
        elif "," in s and "." not in s:
            # European: "5,4" → "5.4"
            s = s.replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return None
