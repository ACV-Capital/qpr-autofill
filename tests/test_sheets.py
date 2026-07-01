"""Tests for qpr.sheets — gspread wrapper.

We don't hit Google Sheets in unit tests; we test the small pure helpers
(hex → RGB, col letter). Real gspread calls require a service account and
are covered by the E2E test in docs/E2E.md.
"""
import pytest
from qpr.sheets import _hex_to_rgb_dict, _col_letter, CellRef


def test_hex_to_rgb_dict_no_alpha():
    rgb = _hex_to_rgb_dict("FF0000")
    assert rgb == {"red": 1.0, "green": 0.0, "blue": 0.0}


def test_hex_to_rgb_dict_with_hash():
    rgb = _hex_to_rgb_dict("#FF0000")
    assert rgb == {"red": 1.0, "green": 0.0, "blue": 0.0}


def test_hex_to_rgb_dict_with_alpha():
    rgb = _hex_to_rgb_dict("00FF0000")  # AARRGGBB: red
    assert rgb == {"red": 1.0, "green": 0.0, "blue": 0.0}


def test_hex_to_rgb_dict_arbitrary_color():
    rgb = _hex_to_rgb_dict("DBE5F1")
    assert abs(rgb["red"] - 0xDB / 255) < 0.01
    assert abs(rgb["green"] - 0xE5 / 255) < 0.01
    assert abs(rgb["blue"] - 0xF1 / 255) < 0.01


def test_hex_to_rgb_dict_invalid_raises():
    with pytest.raises(ValueError):
        _hex_to_rgb_dict("FF00")
    with pytest.raises(ValueError):
        _hex_to_rgb_dict("GGGGGG")


def test_col_letter_basic():
    assert _col_letter(1) == "A"
    assert _col_letter(26) == "Z"
    assert _col_letter(27) == "AA"
    assert _col_letter(52) == "AZ"
    assert _col_letter(53) == "BA"
    assert _col_letter(702) == "ZZ"
    assert _col_letter(703) == "AAA"


def test_cell_ref_is_frozen():
    ref = CellRef(sheet_id="abc", sheet_name="Sheet1", cell="B5")
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        ref.cell = "B6"
