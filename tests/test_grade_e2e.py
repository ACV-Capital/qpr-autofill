"""Tests for qpr.grade_e2e — E2E grader with leakage and self-defensible check."""
import pytest
from qpr.grade_e2e import grade_e2e, _source_tier, check_self_defensible, GradeReport


def test_grade_counts_matches():
    fake_e2e = {
        "IDX:ACES Q1 2026": ("4.3", "https://bisnis.com/aces"),
        "IDX:AMRT Q1 2026": ("6.2", "https://infonasional.com/amrt"),
        "IDX:MIDI Q1 2026": ("4.6", "https://avrist.com/retailers"),  # 0.04 diff
    }
    fake_ref = {
        "IDX:ACES Q1 2026": ("2.9", "https://ref.com/aces"),
        "IDX:AMRT Q1 2026": ("3.33", "https://ref.com/amrt"),
        "IDX:MIDI Q1 2026": ("4.64", "https://ref.com/midi"),
    }
    report = grade_e2e(fake_e2e, fake_ref, tolerance=0.5)
    assert isinstance(report, GradeReport)
    assert report.cells_total == 3
    assert report.cells_with_source == 3
    assert report.cells_differ == 2  # ACES, AMRT
    assert report.cells_match == 1  # MIDI


def test_grade_flags_missing_sources():
    fake_e2e = {
        "IDX:ACES Q1 2026": ("4.3", None),  # NO URL
    }
    fake_ref = {"IDX:ACES Q1 2026": ("2.9", "https://ref.com/aces")}
    report = grade_e2e(fake_e2e, fake_ref)
    assert report.cells_without_source == 1
    assert any("no-source" in w for w in report.warnings)


def test_grade_flags_verbatim_copy():
    fake_e2e = {"IDX:ACES Q1 2026": ("4.3", "https://bisnis.com/aces")}
    fake_ref = {"IDX:ACES Q1 2026": ("2.9", "https://ref.com/aces")}
    prior_cycle_results = {"IDX:ACES Q1 2026": "4.3"}  # exact match
    report = grade_e2e(fake_e2e, fake_ref, prior_cycle=prior_cycle_results)
    assert any("verbatim-copy" in w for w in report.warnings)


def test_grade_both_null_is_match():
    report = grade_e2e(
        {"X:FOO Q1 2026": (None, None)},
        {"X:FOO Q1 2026": (None, None)},
    )
    assert report.cells_match == 1
    assert report.cells_differ == 0


def test_grade_working_null_ref_value_is_missing():
    report = grade_e2e(
        {"X:FOO Q1 2026": (None, None)},
        {"X:FOO Q1 2026": ("5.0", "https://ref.com")},
    )
    assert report.cells_missing == 1


def test_grade_extra_value_is_match():
    report = grade_e2e(
        {"X:FOO Q1 2026": ("5.0", "https://e2e.com")},
        {"X:FOO Q1 2026": (None, None)},
    )
    assert report.cells_extra == 1
    assert report.cells_match == 1  # extra counts as match


# Self-defensibility
def test_grade_flags_broker_only_source():
    fake_e2e = {
        "IDX:ACES Q1 2026": ("4.3", "https://indopremier.com/aces.pdf"),  # broker only
    }
    fake_ref = {}
    report = grade_e2e(fake_e2e, fake_ref, check_defensibility=True)
    assert report.cells_not_defensible == 1
    assert any("not-defensible" in w for w in report.warnings)


def test_grade_passes_primary_source():
    fake_e2e = {
        "IDX:ACES Q1 2026": ("4.3", "https://www.acehardware.co.id/quarterly/1q26.pdf"),
    }
    fake_ref = {}
    report = grade_e2e(fake_e2e, fake_ref, check_defensibility=True)
    assert report.cells_not_defensible == 0


def test_grade_passes_respected_news_source():
    fake_e2e = {
        "IDX:ACES Q1 2026": ("4.3", "https://www.reuters.com/aces-q1"),
    }
    fake_ref = {}
    report = grade_e2e(fake_e2e, fake_ref, check_defensibility=True)
    assert report.cells_not_defensible == 0


def test_grade_can_disable_defensibility_check():
    fake_e2e = {
        "IDX:ACES Q1 2026": ("4.3", "https://indopremier.com/aces.pdf"),  # broker only
    }
    fake_ref = {}
    report = grade_e2e(fake_e2e, fake_ref, check_defensibility=False)
    assert report.cells_not_defensible == 0


# Source tier classification
def test_source_tier_primary():
    assert _source_tier("https://www.bps.go.id/pressrelease/2026.html") == 1
    assert _source_tier("https://bisnis.com/article") == 2  # news
    assert _source_tier("https://indopremier.com/something") == 3  # broker default
    assert _source_tier("https://www.acehardware.co.id/quarterly") == 1  # company IR
    assert _source_tier(None) == 0


def test_source_tier_reuters():
    assert _source_tier("https://reuters.com/.../indonesia-gdp") == 2


def test_check_self_defensible_returns_list():
    warnings = check_self_defensible({
        "X:Y": ("1.0", "https://broker.com/x"),
    })
    assert len(warnings) == 1
    assert "not-defensible" in warnings[0]


def test_pass_rate_property():
    report = GradeReport(cells_match=8, cells_total=10)
    assert report.pass_rate == 0.8
