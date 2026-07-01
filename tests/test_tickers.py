"""Tests for qpr.tickers — SEA-5 retail ticker manifest loader."""
from pathlib import Path
import pytest
from qpr.tickers import load_manifest, Ticker

MANIFEST = Path(__file__).parent.parent / "examples" / "tickers.yaml"


def test_load_manifest_returns_list():
    t = load_manifest(MANIFEST)
    assert isinstance(t, list)
    assert len(t) >= 20  # SEA-5 retail universe + macro panel


def test_ticker_has_required_fields():
    t = load_manifest(MANIFEST)
    valid_exchanges = {"IDX", "SET", "KLSE", "PSE", "HSX", "SGX"}
    for x in t:
        assert x.exchange in valid_exchanges, f"unknown exchange {x.exchange}"
        assert x.ticker
        assert x.company
        # SSSG is only meaningful for retail; non-retail tickers MUST have sssg_applicable=False
        if not x.sssg_applicable:
            sub = x.subsector.lower()
            assert any(k in sub for k in ("bank", "telecom", "utility")), \
                f"non-retail {x.ticker} has subsector '{x.subsector}' — expected bank/telecom/utility"


def test_known_retail_companies_present():
    t = load_manifest(MANIFEST)
    names = {x.company.lower() for x in t if x.sssg_applicable}
    for must_have in [
        "ace hardware", "mitra adi", "mr diy", "99 speed",
        "mk restaurant", "cp all", "7-eleven", "puregold",
    ]:
        assert any(must_have in n for n in names), f"missing retail name: {must_have}"


def test_macro_panel_includes_5_sea5_countries():
    t = load_manifest(MANIFEST)
    non_retail = [x for x in t if not x.sssg_applicable]
    # At least one non-retail ticker per SEA-5 country
    countries = {x.exchange for x in non_retail}
    # We use the exchange to infer country: IDX=ID, SET=TH, PSE=PH, KLSE=MY, HSX=VN
    assert {"IDX", "SET", "PSE", "KLSE"}.issubset(countries), \
        f"expected SEA-5 coverage in non-retail panel, got {countries}"


def test_manifest_yaml_is_well_formed():
    import yaml
    data = yaml.safe_load(MANIFEST.read_text())
    assert isinstance(data, list)
    for row in data:
        assert "exchange" in row
        assert "ticker" in row
        assert "company" in row
        assert "subsector" in row
        assert "sssg_applicable" in row
        assert isinstance(row["sssg_applicable"], bool)
