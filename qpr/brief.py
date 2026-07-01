"""Render an agent research brief from a ticker manifest + quarter + channel memory."""
from __future__ import annotations
from pathlib import Path
from qpr.tickers import Ticker

TEMPLATE = (Path(__file__).parent / "templates" / "sssg_brief.md").read_text()


def _render_cheat_sheet(channel_memory: dict) -> str:
    if not channel_memory:
        return (
            "### Channel memory is empty\n\n"
            "This is the first cycle. Do deep research for every ticker using the methodology below. "
            "After this cycle, the channels you use will be saved into channel memory and the next "
            "agent will start from there.\n"
        )
    lines = ["| Ticker | Check FIRST (tier 1) | Then (tier 2) | Tier 3 (cross-check) |", "|---|---|---|---|"]
    for ticker, entry in sorted(channel_memory.items()):
        if ticker.startswith("_"):
            continue
        t1 = ", ".join(
            f"{c.get('domain', '')} ({c.get('source_label', '')})"
            for c in entry.get("tier_1_channels", [])
        ) or "—"
        t2 = ", ".join(
            f"{c.get('domain', '')}"
            for c in entry.get("tier_2_channels", [])
        ) or "—"
        t3 = ", ".join(
            f"{c.get('domain', '')}"
            for c in entry.get("tier_3_channels", [])
        ) or "—"
        # Truncate long fields
        if len(t1) > 80:
            t1 = t1[:77] + "..."
        lines.append(f"| **{ticker}** | {t1} | {t2} | {t3} |")
    return "\n".join(lines)


def _render_per_ticker_notes(channel_memory: dict) -> str:
    """Render any per-ticker notes (special handling, scope flags, etc.)."""
    notes = []
    for ticker, entry in sorted(channel_memory.items()):
        if ticker.startswith("_"):
            continue
        n = entry.get("notes", "").strip()
        if n:
            notes.append(f"- **{ticker}**: {n}")
    if not notes:
        return ""
    return "\n\n### Per-ticker notes\n\n" + "\n".join(notes) + "\n"


def render_sssg_brief(
    *,
    quarter: str,
    tickers: list[Ticker],
    sssg_tickers: list[Ticker],
    channel_memory: dict,
) -> str:
    block_lines = []
    for t in sssg_tickers:
        note = f" — {t.notes}" if t.notes else ""
        block_lines.append(f"- **{t.exchange}:{t.ticker}** — {t.company} ({t.subsector}){note}")
    ticker_block = "\n".join(block_lines)
    # "2026Q2" → quarter_short="2", quarter_slug="2026q2"
    q_short = quarter.lower().replace("q", "").replace("20", "")
    quarter_slug = quarter.lower()
    cheat_sheet = _render_cheat_sheet(channel_memory)
    per_ticker_notes = _render_per_ticker_notes(channel_memory)
    return TEMPLATE.replace("{quarter}", quarter)\
                    .replace("{quarter_short}", q_short)\
                    .replace("{quarter_slug}", quarter_slug)\
                    .replace("{ticker_block}", ticker_block)\
                    .replace("{channel_cheat_sheet}", cheat_sheet)\
                    .replace("{per_ticker_notes}", per_ticker_notes)
