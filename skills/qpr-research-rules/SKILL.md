---
name: qpr-research-rules
description: "The 9 hard rules of ACV Capital's quarterly research workflow. Load this skill before any research task. It is the actual IP of the project — these rules were learned over multiple research cycles and encode the methodology that makes the plugin work."
version: 0.1.0
---

# QPR Research Rules

These rules govern every research task in the QPR auto-fill workflow. They come
from the original Q4'25 + Q1'26 research cycle and were refined through 6 rounds
of agent briefs plus grading against a hidden reference sheet (now retired).

**The reference sheet is GONE after the v0.1 release of this plugin.** The rules
below are how we produce self-defensible research without one.

## The 9 Rules

### 1. Reference sheet is a HIDDEN GRADING ARTIFACT
- **Never** read it during research. **Never** copy it.
- It exists only for the E2E test (`docs/E2E.md`) — not in production.
- A "reference" you stumble on is either the E2E GSheet or someone else's data; ignore it.

### 2. Subagents do all research from public sources
- Regulator sites, IR pages, financial reports, respected business news.
- Subagents never see the reference sheet ID (and shouldn't know it exists).

### 3. Every value must come with a specific source URL
- "BPS" or "quarterly earnings presentation" is **NOT** a source.
- The URL must be the actual page where the value appears, not a press release index.
- If the article is paywalled, use the Internet Archive (`web.archive.org/web/*/...`).

### 4. Hermes opens each URL itself
- The subagent returns `(value, URL)`. Hermes (or the verifier) opens the URL
  and confirms the value is on the page before writing.
- The verifier is `qpr.verify.verify_value_on_page` — it accepts ±0.1pp
  rounding tolerance and warns (does not auto-pass) on rounding matches.

### 5. Reference is consulted only at the end for grading
- In production, there is no reference. The preflight check is the substitute:
  it confirms every cell is self-defensible (Tier 1 or Tier 2 source).

### 6. Copy the exact underlying numeric value
- e.g. **32.543**, not "32.5" or "about 33".
- If the source says "approximately 5%" or "nearly 1 percent drop", use the
  exact word and note the approximation in the cell's Notes column.

### 7. 3-layer verification before any write
- **Period**: Q1'26, not FY25, not 1H26, not "the latest quarter". Confirm the
  period of the source value.
- **Metric**: SSSG, not revenue growth, not total sales growth, not new-store
  contribution. Read the source carefully.
- **Scope**: brand-only (Puregold stores, MK restaurants) vs consolidated
  (PGOLD = Puregold + S&R, MAP group = MAPA + MAPB + MAPI). Always note which.

### 8. Tolerance for matching
- 0.5pp for rounded SSSG (e.g. 11.0% vs 11.5% — same underlying).
- 0.05pp for primary-source 2-decimal values (e.g. 4.64% vs 4.60% — different).
- "Both null" is success, not a gap. If the reference and your value are both
  null because the cell genuinely has no public source, that's a match.

### 9. Self-defensible research (the post-reference rule)
- Every cell must be defensible **on its own** without a hidden answer key.
- **Macro** (GDP, FX, private consumption): cite a **primary statistical agency**
  (BPS, NESDC, PSA, DOSM, GSO, BI, BOT) or a major news wire (Reuters, Bloomberg)
  that quoted the agency release. Never a broker summary alone.
- **SSSG**: cite the **company's own quarterly results presentation** or
  **annual report MD&A** when possible; fall back to respected business news
  (Kontan, Bisnis, The Edge, Insider Retail, Kaohoon, InsiderPH); use broker
  research (CGS, Indo Premier, Avrist, UOBKH, KGI) only as a secondary
  cross-check, never as the sole source.
- **Two-source rule** for any value above ±5pp or any value that drives a
  partner-facing claim. One source for "in the ballpark" numbers (e.g.
  0.5–1.5pp SSSG readings) is acceptable if the source is the company's own
  disclosure.
- **Notes column is mandatory** and must flag: period, scope (brand vs
  consolidated), rounding (±0.1pp), and any source-disagreement between
  cross-checks.

## Source tier reference

| Tier | Examples | Self-defensible? |
|---|---|---|
| **Tier 1** | bps.go.id, bi.go.id, nesdc.go.th, mk.co.th (company IR), 7-eleven.com.ph (company IR) | **Yes, alone** |
| **Tier 2** | reuters.com, bisnis.com, kontan.co.id, kaohooninternational.com, theedgemalaysia.com, insiderph.com | **Yes, alone** |
| **Tier 3** | indopremier.com, avrist.com, uobkayhian.com, cgs-international (broker PDFs) | **No — needs Tier 1/2 cross-check** |

## What this means in practice

For an SSSG value of "ACES FY 2025 = -4.2%":
- ✅ `-4.2`, source: `https://bisnis.com/.../aces-fy25`, channel: `tier_1` (Bisnis quoting CGS International, a major broker — but Bisnis itself is tier 2)
- ✅ `-4.2`, source: `https://acehardware.co.id/quarterly/4q25.pdf`, channel: `tier_1` (company IR — best)
- ⚠️ `-4.2`, source: `https://indopremier.com/aces.pdf`, channel: `tier_3` (broker only — needs a Bisnis or company cross-check)
- ❌ `-4.2`, source: "broker report", channel: "tier_3" — no URL, not defensible

## Anti-patterns to avoid

- **Stating revenue growth as SSSG** — they are different. SSSG is same-store
  only; revenue growth includes new stores, FX, and pricing.
- **Using the prior cycle's value as "good enough"** — every quarter is fresh.
  The channel memory helps you find the right source faster; it does not give
  you the answer.
- **Skipping the period check** — Q1 2026 ≠ FY 2025 ≠ 1H 2026. If the source
  says FY 2025, the cell for Q1 2026 is null, not the FY 2025 number.
- **Skipping the scope check** — "PGOLD +5.4%" can mean Puregold stores only or
  consolidated (Puregold + S&R). The reference sheet might use either. Be
  explicit in the Notes column.

## Loading this skill

```yaml
---
name: qpr-research-rules
description: "Always load before any research task. These are the 9 hard rules."
---
```

If an agent has loaded this skill, it should never:
- Open any Google Sheet other than the working sheet it was told to write to.
- Search for "ACES SSSG 2025" and report a number without opening the source.
- Report a value that came from `notes/agent_sssg_r5_*_results.json` or any
  other prior-cycle file (those are the audit trail, not sources).
- Conflate a Tier 3 broker value with a Tier 1/2 source.
