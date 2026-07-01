"""Tests for qpr.verify — confirm a value is on a saved page."""
from pathlib import Path
from qpr.verify import verify_value_on_page, VerificationResult

FIX = Path(__file__).parent / "fixtures" / "sample_page.html"


def test_verify_finds_value():
    res = verify_value_on_page(FIX, "5.39", period_hint="Q4 2025")
    assert res.found is True
    assert res.matched_text == "5.39"
    assert res.context_snippet  # non-empty


def test_verify_handles_pct_and_pp():
    # 5.4 appears verbatim in "5.4 percentage points" — should be exact match
    res = verify_value_on_page(FIX, "5.4", allow_pp=True)
    assert res.found is True
    assert res.matched_text == "5.4"
    # No warning when the value appears verbatim
    assert res.warning is None


def test_verify_pp_match_when_value_not_verbatim():
    # If the page has "5.4 percentage points" but we're looking for "5.40",
    # that's not a verbatim match for "5.40" but the rounding+pp combo should match.
    res = verify_value_on_page(FIX, "5.40", allow_pp=True)
    # 5.40 is not on the page; 5.4 is. Without pp logic this would not-found.
    assert res.found is True
    assert res.warning is not None


def test_verify_returns_not_found():
    res = verify_value_on_page(FIX, "99.99")
    assert res.found is False
    assert res.reason == "value-not-in-page"


def test_verify_warns_on_loose_rounding_match():
    # -2.8 is on the page; looking for -2.7 should match via rounding tolerance (±0.1)
    res = verify_value_on_page(FIX, "-2.7", period_hint="FY 2025")
    assert res.found is True
    assert res.warning is not None
    assert "rounded" in res.warning
    assert res.matched_text == "-2.8"


def test_verify_no_match_outside_rounding_tolerance():
    # -2.8 is on the page; looking for -3.0 is outside ±0.1 tolerance
    res = verify_value_on_page(FIX, "-3.0", period_hint="FY 2025")
    assert res.found is False
    assert res.reason == "value-not-in-page"


def test_verify_finds_sssg_value():
    res = verify_value_on_page(FIX, "-4.2")
    assert res.found is True
    assert "ACES" in res.context_snippet
