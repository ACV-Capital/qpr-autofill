"""gspread wrapper for the working sheet.

Lazy-imports gspread so the rest of the package can be used without it for
unit testing. All operations are no-ops if the SA key is missing — the caller
is expected to set `GOOGLE_APPLICATION_CREDENTIALS` to a valid service-account
JSON before calling.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CellRef:
    sheet_id: str
    sheet_name: str
    cell: str  # e.g. "B5"


def _get_client():
    """Return a gspread client, or raise a clear error if not configured."""
    try:
        import gspread  # noqa: F401
        from google.oauth2.service_account import Credentials
    except ImportError as e:
        raise RuntimeError(
            "gspread + google-auth required. Install with: pip install gspread google-auth"
        ) from e

    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
    if not Path(sa_path).exists():
        raise RuntimeError(
            f"Service account JSON not found at {sa_path}. "
            f"Set GOOGLE_APPLICATION_CREDENTIALS env var or place the file at service-account.json."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(sa_path, scopes=scopes)
    return gspread.authorize(creds)


def read_sheet(sheet_id: str, tab_name: str | None = None) -> dict[str, Any]:
    """Read all cells from a sheet, returning {cell_ref: value}.

    Lazy — opens the sheet on first call.
    """
    client = _get_client()
    sh = client.open_by_key(sheet_id)
    ws = sh.worksheet(tab_name) if tab_name else sh.sheet1
    records = ws.get_all_values()  # list[list[str]]
    result = {}
    for r, row in enumerate(records, start=1):
        for c, val in enumerate(row, start=1):
            if val != "":
                result[f"{_col_letter(c)}{r}"] = val
    return result


def write_cell(ref: CellRef, value: Any) -> None:
    """Write a single value to a cell."""
    client = _get_client()
    sh = client.open_by_key(ref.sheet_id)
    ws = sh.worksheet(ref.sheet_name)
    ws.update_acell(ref.cell, str(value))


def set_color(ref: CellRef, hex_color: str) -> None:
    """Set a cell's background fill color (hex like 'FFDBE5F1')."""
    client = _get_client()
    sh = client.open_by_key(ref.sheet_id)
    ws = sh.worksheet(ref.sheet_name)
    # gspread update_cells with format
    ws.format(ref.cell, {"backgroundColor": _hex_to_rgb_dict(hex_color)})


def _hex_to_rgb_dict(hex_color: str) -> dict[str, float]:
    """Convert 'RRGGBB' or 'AARRGGBB' hex to {red, green, blue} 0-1 dict."""
    s = hex_color.lstrip("#")
    if len(s) == 8:  # AARRGGBB
        s = s[2:]
    if len(s) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    return {
        "red": int(s[0:2], 16) / 255.0,
        "green": int(s[2:4], 16) / 255.0,
        "blue": int(s[4:6], 16) / 255.0,
    }


def _col_letter(n: int) -> str:
    s = ""
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s
