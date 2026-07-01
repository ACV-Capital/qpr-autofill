"""Tests for qpr.classify — cell-level match/differ/missing/extra logic."""
import pytest
from qpr.classify import classify, Status


def test_both_null_is_match():
    assert classify(None, None) == Status.MATCH


def test_exact_match():
    assert classify(4.1, 4.1) == Status.MATCH


def test_within_tolerance_is_match():
    # 0.5pp for rounded SSSG
    assert classify(-13.0, -12.6) == Status.MATCH
    # 0.05pp for primary 2-decimal
    assert classify(4.64, 4.60) == Status.MATCH
    # 0.4pp rounding diff
    assert classify(11.0, 11.5) == Status.MATCH


def test_differ_real_disagreement():
    assert classify(-4.2, -2.19) == Status.DIFFER


def test_working_null_ref_has_value_is_missing():
    assert classify(None, 5.4) == Status.MISSING


def test_working_value_ref_null_is_extra():
    assert classify(5.4, None) == Status.EXTRA


def test_differ_within_tolerance_can_be_overridden():
    assert classify(-13.0, -12.6, tolerance=0.0) == Status.DIFFER


def test_handles_string_values_with_percent():
    assert classify("5.4%", "5.40") == Status.MATCH
    assert classify(" -4.2 ", "-4.20") == Status.MATCH


def test_handles_string_values_with_comma_decimal():
    # European decimal format
    assert classify("5,4", "5.4") == Status.MATCH


def test_unparseable_string_is_treated_as_missing():
    assert classify("N/A", "5.0") == Status.MISSING


def test_unparseable_both_sides_is_match():
    assert classify("N/A", "") == Status.MATCH


def test_int_values_work():
    assert classify(5, 5) == Status.MATCH
    assert classify(5, 6) == Status.DIFFER
