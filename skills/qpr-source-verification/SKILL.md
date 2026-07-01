---
name: qpr-source-verification
description: "How to confirm a value is actually on a saved page. Use qpr.verify to open a saved HTML/text file, search for the value (with ±0.1pp rounding tolerance and percentage-points phrasing), and return context."
version: 0.1.0
---

# QPR Source Verification

When an agent returns a value with a URL, the verifier (Hermes or a separate
subagent) opens the URL, saves the page locally, then calls
`qpr.verify.verify_value_on_page` to confirm the value is on the page.

The verifier is **strict about not auto-passing rounded matches** — it returns
a `warning` field so the human can decide. Tolerance settings:
- 0.5pp for the classify step (matching the working sheet)
- ±0.1pp rounding tolerance in the verifier (warns but does not auto-pass)

## Usage

```python
from qpr.verify import verify_value_on_page

result = verify_value_on_page(
    page_path="saved_pages/bisnis_aces_q1_2026.html",
    value=-4.2,
    period_hint="Q1 2026",
    allow_pp=True,  # accept "X.X percentage points" phrasing
)

if result.found:
    print(f"✓ {result.matched_text}  context: {result.context_snippet}")
    if result.warning:
        print(f"  ⚠ {result.warning}")
else:
    print(f"✗ not found  reason: {result.reason}")
```

## Three match levels

1. **Exact match** — value verbatim on the page (e.g. looking for "-4.2" and
   page has "-4.2%"). No warning.

2. **Percentage-points match** (when `allow_pp=True`) — page says "consumption
   contributed 5.4 percentage points" and we're looking for "5.4". Returns
   `warning="matched-as-percentage-points"`.

3. **Rounded match** — page has "-2.8%" and we're looking for "-2.7%". Returns
   `warning="rounded match: -2.7 != -2.8 (Δ=+0.1)"`. The result `found=True`
   but the warning flags the discrepancy.

If none of these match, returns `found=False, reason="value-not-in-page"`.

## CLI

```bash
python -m qpr verify-results agent1.json agent2.json \
    --pages-dir saved_pages/
```

Loops over each `(value, URL)` pair, finds the matching page file (by domain
in the URL), and prints pass/fail per value.

## Common pitfalls

- **Page has the value but as "5.4" not "5.40"** — the verifier accepts both
  for the same underlying number. If you have a strict value, this is a real
  mismatch, not a rounding.
- **Page has the value but the value is in a JavaScript-rendered element** —
  the saved HTML won't have it. Use `curl` or a headless browser to save the
  page; if the value is only in client-rendered content, the article is not
  a usable source.
- **Page is paywalled** — the Internet Archive has a cached version. Use
  `https://web.archive.org/web/*/original_url` and save that page.
