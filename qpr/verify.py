"""Verify a value is on a saved page (HTML/text) with context.

Designed to run on locally-saved source files (downloaded via curl or
browser save). Does NOT fetch URLs itself — the human/Hermes is responsible
for opening the URL and saving the page first. This keeps the verifier
deterministic and testable.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class VerificationResult:
    found: bool
    matched_text: str = ""
    context_snippet: str = ""
    warning: str | None = None
    reason: str = ""


def verify_value_on_page(
    page_path: str | Path,
    value: str | float,
    *,
    period_hint: str | None = None,
    allow_pp: bool = False,
) -> VerificationResult:
    """Confirm `value` appears on the saved page text, returning context.

    Tries:
    1. exact match (with percent strip)
    2. "X.X percentage points" phrasing (if allow_pp)
    3. rounding tolerance ±0.1pp (warning, but still found)
    """
    text = Path(page_path).read_text(errors="ignore")
    s = _format_value(value)
    # strip % from search value too (page may have "5.39%" or "5.39")
    s_clean = s.rstrip("%").strip()
    # strip HTML crud for matching
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"\s+", " ", plain)

    # 1. exact match (strict — no trailing-zero stripping for the value)
    for cand in (s, s_clean):
        if cand in plain:
            idx = plain.find(cand)
            return VerificationResult(
                found=True,
                matched_text=cand,
                context_snippet=plain[max(0, idx - 60) : idx + len(cand) + 60],
            )

    # 2. allow "X.X percentage points" phrasing — accept with or without trailing zero
    if allow_pp:
        for cand in (s, s_clean, s.rstrip("0").rstrip(".")):
            if cand and re.search(
                re.escape(cand) + r"\s*(percentage points|percentage point|pp\b)",
                plain, re.IGNORECASE,
            ):
                return VerificationResult(
                    found=True,
                    matched_text=cand + " pp",
                    context_snippet="",
                    warning="matched-as-percentage-points",
                )

    # 3. rounding tolerance: warn but still found
    if "." in s_clean:
        try:
            f = float(s_clean)
            for off in (-0.1, 0.1):
                nearby = f"{f + off:.2f}"
                # also try without trailing zero (e.g. -2.80 → -2.8 to match "-2.8%")
                for cand in (nearby, nearby.rstrip("0").rstrip(".")):
                    if cand and cand in plain:
                        idx = plain.find(cand)
                        return VerificationResult(
                            found=True,
                            matched_text=cand,
                            context_snippet=plain[max(0, idx - 60) : idx + len(cand) + 60],
                            warning=f"rounded match: {s} != {cand} (Δ={off:+.1f})",
                            reason="rounded-match",
                        )
        except ValueError:
            pass

    return VerificationResult(found=False, reason="value-not-in-page")


def _format_value(value: str | float) -> str:
    """Format a numeric value as the string we'd expect to see in page text."""
    if isinstance(value, str):
        return value.strip()
    return f"{value:.2f}"
