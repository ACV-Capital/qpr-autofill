"""Tests for qpr.channel_memory — per-ticker source memory with success/failure tracking."""
from pathlib import Path
import json
import pytest
from qpr.channel_memory import (
    load_memory, save_memory, get_channels_for, update_after_cycle,
)

MEMORY = Path(__file__).parent.parent / "qpr" / "data" / "channel_memory.json"


def test_load_memory_returns_dict():
    m = load_memory(MEMORY)
    assert isinstance(m, dict)
    assert "IDX:ACES" in m
    assert "macro:Indonesia" in m


def test_get_channels_for_tier_order():
    m = load_memory(MEMORY)
    channels = get_channels_for(m, "IDX:ACES", tiers=[1, 2, 3])
    tiers = [c["tier"] for c in channels]
    assert tiers == sorted(tiers)  # tier 1 before tier 2 before tier 3


def test_get_channels_for_specific_tiers():
    m = load_memory(MEMORY)
    only_1 = get_channels_for(m, "IDX:ACES", tiers=[1])
    assert all(c["tier"] == 1 for c in only_1)


def test_get_channels_for_unknown_ticker_returns_empty():
    m = load_memory(MEMORY)
    assert get_channels_for(m, "ZZZ:FAKE") == []


def test_get_channels_for_macro():
    m = load_memory(MEMORY)
    channels = get_channels_for(m, "macro:Indonesia", tiers=[1, 2, 3])
    assert len(channels) > 0
    assert any(c["domain"] == "bps.go.id" for c in channels)


def test_update_after_cycle_increments_success():
    m = load_memory(MEMORY)
    initial = next(c for c in m["IDX:ACES"]["tier_1_channels"] if c["domain"] == "bisnis.com")["success_count"]
    update_after_cycle(
        m,
        {"IDX:ACES": {"value": "-4.2", "url": "https://bisnis.com/.../aces-q2-2026", "channel_used": "tier_1"}},
    )
    after = next(c for c in m["IDX:ACES"]["tier_1_channels"] if c["domain"] == "bisnis.com")["success_count"]
    assert after == initial + 1


def test_update_after_cycle_resets_consecutive_failures():
    m = load_memory(MEMORY)
    ch = next(c for c in m["IDX:ACES"]["tier_1_channels"] if c["domain"] == "bisnis.com")
    ch["consecutive_failures"] = 1
    update_after_cycle(
        m,
        {"IDX:ACES": {"value": "-4.2", "url": "https://bisnis.com/.../aces-q2-2026"}},
    )
    assert ch["consecutive_failures"] == 0
    assert ch["last_successful"] is True


def test_update_after_cycle_demotes_failing_channel():
    m = {
        "IDX:TEST": {
            "metric": "sssg",
            "tier_1_channels": [
                {"domain": "fail.com", "tier": 1, "success_count": 0, "consecutive_failures": 1, "last_successful": False},
            ],
            "tier_2_channels": [],
            "tier_3_channels": [],
            "notes": "",
        }
    }
    update_after_cycle(
        m,
        {"IDX:TEST": {"value": "1.0", "url": "https://other.com/.../x"}},
        ticker_failed_domains={"IDX:TEST": ["fail.com"]},
    )
    # fail.com should now be in tier_3
    assert "fail.com" not in [c["domain"] for c in m["IDX:TEST"]["tier_1_channels"]]
    assert any(c["domain"] == "fail.com" for c in m["IDX:TEST"]["tier_3_channels"])


def test_update_after_cycle_adds_new_channel_to_tier3():
    m = {"IDX:NEW": {"metric": "sssg", "tier_1_channels": [], "tier_2_channels": [], "tier_3_channels": [], "notes": ""}}
    update_after_cycle(
        m,
        {"IDX:NEW": {"value": "5.0", "url": "https://brand-new-domain.com/.../x"}},
    )
    assert any(c["domain"] == "brand-new-domain.com" for c in m["IDX:NEW"]["tier_3_channels"])


def test_update_after_cycle_promotes_tier3_to_tier2_on_success():
    m = {"IDX:PROMO": {
        "metric": "sssg",
        "tier_1_channels": [],
        "tier_2_channels": [],
        "tier_3_channels": [
            {"domain": "rising.com", "tier": 3, "success_count": 0, "consecutive_failures": 0, "last_successful": False},
        ],
        "notes": "",
    }}
    update_after_cycle(
        m,
        {"IDX:PROMO": {"value": "5.0", "url": "https://rising.com/.../x"}},
    )
    # Should be promoted to tier_2
    assert any(c["domain"] == "rising.com" for c in m["IDX:PROMO"]["tier_2_channels"])
    assert not any(c["domain"] == "rising.com" for c in m["IDX:PROMO"]["tier_3_channels"])


def test_save_and_load_roundtrip(tmp_path):
    p = tmp_path / "mem.json"
    m = {"IDX:TEST": {"metric": "sssg", "tier_1_channels": [], "tier_2_channels": [], "tier_3_channels": [], "notes": "hello"}}
    save_memory(m, p)
    loaded = load_memory(p)
    assert loaded["IDX:TEST"]["notes"] == "hello"
