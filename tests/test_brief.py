"""Tests for qpr.brief — render SSSG brief with channel memory cheat sheet."""
from pathlib import Path
from qpr.tickers import load_manifest
from qpr.brief import render_sssg_brief

MANIFEST = Path(__file__).parent.parent / "examples" / "tickers.yaml"


def test_render_sssg_brief_contains_each_ticker():
    tickers = load_manifest(MANIFEST)
    sssg = [t for t in tickers if t.sssg_applicable]
    md = render_sssg_brief(
        quarter="2026Q2", tickers=tickers, sssg_tickers=sssg, channel_memory={}
    )
    for t in sssg:
        assert f"{t.exchange}:{t.ticker}" in md, f"missing {t.exchange}:{t.ticker}"
    assert "2026Q2" in md


def test_render_sssg_brief_contains_hard_rules():
    tickers = load_manifest(MANIFEST)
    sssg = [t for t in tickers if t.sssg_applicable]
    md = render_sssg_brief(
        quarter="2026Q2", tickers=tickers, sssg_tickers=sssg, channel_memory={}
    )
    assert "NEVER open, read, query" in md
    assert "SSSG" in md
    assert "Tier 1" in md


def test_render_sssg_brief_includes_channel_memory_cheat_sheet():
    tickers = load_manifest(MANIFEST)
    sssg = [t for t in tickers if t.sssg_applicable]
    memory = {
        "IDX:ACES": {
            "tier_1_channels": [{"domain": "bisnis.com", "source_label": "CGS research"}],
            "tier_2_channels": [],
            "tier_3_channels": [],
            "notes": "Check Bisnis first",
        },
    }
    md = render_sssg_brief(
        quarter="2026Q2", tickers=tickers, sssg_tickers=sssg, channel_memory=memory
    )
    assert "IDX:ACES" in md
    assert "bisnis.com" in md
    assert "CGS research" in md
    assert "Check Bisnis first" in md


def test_render_sssg_brief_falls_back_gracefully_without_memory():
    md = render_sssg_brief(
        quarter="2026Q2", tickers=[], sssg_tickers=[], channel_memory={}
    )
    # Should still produce a valid brief with the fallback message
    assert "Channel memory is empty" in md
    assert "deep research" in md.lower()


def test_render_sssg_brief_omits_metadata_key():
    # _metadata is a file-level key, not a ticker; should not appear in cheat sheet
    tickers = load_manifest(MANIFEST)
    sssg = [t for t in tickers if t.sssg_applicable]
    memory = {
        "_metadata": {"description": "should be skipped"},
        "IDX:ACES": {"tier_1_channels": [{"domain": "bisnis.com", "source_label": "X"}],
                     "tier_2_channels": [], "tier_3_channels": [], "notes": ""},
    }
    md = render_sssg_brief(
        quarter="2026Q2", tickers=tickers, sssg_tickers=sssg, channel_memory=memory
    )
    assert "should be skipped" not in md
    assert "IDX:ACES" in md
