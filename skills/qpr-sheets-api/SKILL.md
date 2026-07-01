---
name: qpr-sheets-api
description: "How to read from and write to the working Google Sheet for the QPR auto-fill workflow. Use the qpr.sheets Python module — never raw gspread — so the rest of the CLI can be consistent across agents."
version: 0.1.0
---

# QPR Sheets API

The QPR plugin uses a thin wrapper around `gspread` in `qpr.sheets`. Always
use this wrapper — never raw gspread — so the rest of the CLI is consistent.

## Setup

The Google service account JSON must be available at the path in
`GOOGLE_APPLICATION_CREDENTIALS`. For the working sheet (the one the agent
writes to), the SA needs `editor` permission.

For the E2E test (separate GSheet), the SA is in
`~/Documents/Projects/qpr-autofill-e2e/secrets/service-account.json`.

## Common operations

```python
from qpr.sheets import read_sheet, write_cell, set_color, CellRef

# Read all cells from a tab
sheet = read_sheet(sheet_id, tab_name)  # returns {cell_ref: value}

# Write one cell
ref = CellRef(sheet_id=sheet_id, sheet_name="Sheet1", cell="B5")
write_cell(ref, -4.2)

# Color a cell (hex like 'FFDBE5F1' or 'FF0000')
set_color(ref, "FFDBE5F1")
```

## Standard cell layout (working sheet)

The QPR working sheet has a consistent column structure (Phase D will encode
this; for now, agents are told the layout in their brief). Typical layout:

- **Column A**: blank
- **Column B**: category label (e.g. "Real GDP Growth (YoY %)")
- **Column C**: country/ticker
- **Columns D-H**: quarters (Q1'25, Q2'25, Q3'25, Q4'25, Q1'26)
- **Column I** (and beyond): Source URL
- **Column J**: Notes (period, scope, rounding)

For SSSG:
- **Column B**: company name
- **Column C**: ticker
- **Column D**: Q4'25 SSSG
- **Column E**: Q4'25 source
- **Column F**: Q1'26 SSSG
- **Column G**: Q1'26 source
- **Column H**: Notes

## Color coding (the visual grading language)

| Color | Hex | Meaning |
|---|---|---|
| White (default) | FFFFFF | Match within tolerance (or both null) |
| Orange | FFFCE4D6 | Differ (real public-source disagreement) |
| Red | FFFFCCCC | Missing — you didn't find a value, the reference has one |
| Green | FFE2EFDA | Extra — you found a value the reference didn't |
| Blue | FFD9E1F2 | Not yet reviewed |

**Always** set the color after writing the value, so the human reader can
see at a glance which cells are done.

## What NOT to do

- **Don't** read the reference sheet (the production one or the E2E one).
- **Don't** write to any GSheet other than the working one specified in your brief.
- **Don't** write a value without a URL in the source column.
- **Don't** write a value to an SSSG cell that came from revenue growth or
  total sales growth — that's a metric mismatch.
