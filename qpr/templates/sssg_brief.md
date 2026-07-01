# SSSG Brief — {quarter}

You are researching **SSSG (same-store sales growth)** for the following SEA-5 retail companies for the quarter **{quarter}**:

{ticker_block}

## THE HARD RULES (read first)

1. **NEVER open, read, query, or reference** any reference Google Sheet. There is no reference in production. The reference is only consulted once at plugin-release time during the E2E.
2. Find all values via public web search + direct PDF fetch only.
3. Every cell you write MUST have a specific public source URL.
4. The metric is **SSSG** (same-store sales growth, YoY %). NOT revenue growth, NOT total sales growth.
5. Confirm period: {quarter}, not the prior quarter or full year.
6. Confirm scope: brand-only vs consolidated — note which one you used.
7. Two-source cross-check for any value >±5pp or partner-facing.
8. Every cell must be self-defensible (Tier 1 or Tier 2 source). Tier 3 (broker only) is not enough.

## CHANNEL MEMORY — start here, fall back to deep research

**This is the most important section.** In prior cycles, we found that each retailer's SSSG reliably appears at a small set of known channels. **Check those first.** If a known channel returns the value, you can verify and write in 2-3 minutes. Only do fresh deep research when the known channels come up empty for this quarter.

{channel_cheat_sheet}
{per_ticker_notes}
### If a known channel returns nothing

- The company may have stopped publishing there — try `site:<domain> <ticker> {quarter}` search
- Article may be paywalled or moved — try `web.archive.org/web/*/<domain>/...`
- If still nothing: deep-research methodology (below) — primary disclosure first, then respected business news, then broker cross-check

## Deep research methodology (when channel memory is empty)

1. Company IR / press release (e.g. investor.acehardware.co.id)
2. SET / IDX / PSE / KLSE / HSX regulatory disclosure
3. Quarterly results presentation PDF (often has a "Same Store Sales" slide)
4. Annual report MD&A section
5. Respected business news (Reuters, Kontan, Bisnis, The Edge, Insider Retail)
6. Broker research from major houses (CGS, Indo Premier, Avrist, KGI, UOBKH) — **cross-check only, not primary**

## Source tier reference

- **Tier 1** = primary statistical agency, regulator, or company IR — defensible on its own
- **Tier 2** = major news wire (Reuters, Bloomberg) or respected regional business pub — defensible
- **Tier 3** = broker research — **not defensible without a Tier 1/2 cross-check**

## Output format

Write to `notes/agent_sssg_{quarter_slug}_<your_assignment>_results.json` with the following structure (note: the literal JSON below is just an example, fill in the actual values):

```
{
  "agent": "<your_id>",
  "quarter": "{quarter}",
  "results": {
    "TICKER": {
      "company": "...",
      "sssg_yoy_pct": <number or null>,
      "sssg_source": "<url or null>",
      "channel_used": "tier_1 | tier_2 | tier_3 | deep_research",
      "notes": "..."
    }
  }
}
```

The `channel_used` field is required — it tells the post-cycle refresher which channels to credit in the memory.

## When you finish

1. Write JSON
2. Print a summary table showing: ticker | value | source domain | channel_used
3. Stop. Hermes will verify each URL, run `qpr preflight` for self-defensibility, then write to the working sheet.
