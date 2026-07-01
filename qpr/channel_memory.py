"""Per-ticker channel memory — the 'try this first' list for each cycle."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date
from urllib.parse import urlparse


def load_memory(path: str | Path) -> dict:
    """Load the channel memory JSON file."""
    return json.loads(Path(path).read_text())


def save_memory(memory: dict, path: str | Path) -> None:
    """Write the channel memory JSON file."""
    Path(path).write_text(json.dumps(memory, indent=2))


def get_channels_for(
    memory: dict,
    ticker: str,
    *,
    tiers: tuple[int, ...] = (1, 2, 3),
) -> list[dict]:
    """Return the channels for a ticker, sorted by tier ascending then by success_count descending."""
    entry = memory.get(ticker)
    if not entry:
        return []
    all_channels = (
        entry.get("tier_1_channels", []) +
        entry.get("tier_2_channels", []) +
        entry.get("tier_3_channels", [])
    )
    filtered = [c for c in all_channels if c.get("tier", 3) in tiers]
    return sorted(filtered, key=lambda c: (c.get("tier", 3), -c.get("success_count", 0)))


def _domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower().lstrip("www.")


def _ensure_entry(memory: dict, ticker: str) -> dict:
    return memory.setdefault(
        ticker,
        {"metric": "sssg", "tier_1_channels": [], "tier_2_channels": [], "tier_3_channels": [], "notes": ""},
    )


def _find_existing(entry: dict, domain: str) -> tuple[dict | None, str | None]:
    """Find an existing channel entry by domain. Returns (entry, tier_key) or (None, None)."""
    for tier_key in ("tier_1_channels", "tier_2_channels", "tier_3_channels"):
        for c in entry[tier_key]:
            if c["domain"] == domain:
                return c, tier_key
    return None, None


def update_after_cycle(
    memory: dict,
    cycle_results: dict[str, dict],
    *,
    ticker_failed_domains: dict[str, list[str]] | None = None,
    today: str | None = None,
) -> dict:
    """Update memory based on a completed cycle's results.

    For each (ticker, value) result:
    - If the URL's domain is in the existing memory → increment success_count, update last_used
    - If new → add to tier_3_channels (will be promoted after 1 more success)
    For each (ticker, domain) in ticker_failed_domains → bump consecutive_failures, demote if ≥2

    Returns the updated memory (also mutates in place).
    """
    today = today or date.today().isoformat()
    ticker_failed_domains = ticker_failed_domains or {}

    for ticker, result in cycle_results.items():
        url = result.get("url")
        if not url:
            continue
        domain = _domain(url)
        entry = _ensure_entry(memory, ticker)
        existing, _tier_key = _find_existing(entry, domain)
        if existing:
            existing["success_count"] = existing.get("success_count", 0) + 1
            existing["last_used"] = today
            existing["last_successful"] = True
            existing["consecutive_failures"] = 0
            existing["source_label"] = result.get("source_label", existing.get("source_label", ""))
            # promote tier_3 → tier_2 after 1 successful use
            if existing.get("tier") == 3:
                entry["tier_3_channels"] = [c for c in entry["tier_3_channels"] if c["domain"] != domain]
                existing["tier"] = 2
                if not any(c["domain"] == domain for c in entry["tier_2_channels"]):
                    entry["tier_2_channels"].append(existing)
        else:
            entry["tier_3_channels"].append({
                "domain": domain,
                "tier": 3,
                "last_used": today,
                "last_successful": True,
                "success_count": 1,
                "consecutive_failures": 0,
                "source_label": result.get("source_label", ""),
            })

    # demote channels that failed this cycle
    for ticker, domains in ticker_failed_domains.items():
        entry = memory.get(ticker)
        if not entry:
            continue
        for domain in domains:
            existing, tier_key = _find_existing(entry, domain)
            if not existing or tier_key == "tier_3_channels":
                continue
            existing["consecutive_failures"] = existing.get("consecutive_failures", 0) + 1
            existing["last_successful"] = False
            if existing["consecutive_failures"] >= 2:
                # demote to tier_3
                entry[tier_key] = [c for c in entry[tier_key] if c["domain"] != domain]
                existing["tier"] = 3
                entry["tier_3_channels"].append(existing)
    return memory
