"""Grade an E2E test run against a hidden reference sheet.

Compares values cell-by-cell, with the same 0.5pp tolerance as the working
sheet. Also flags any cell that exactly matches a value from the prior
research cycle's notes/agent_sssg_*_results.json — that would be evidence
of leakage from the secluded environment.

Also runs a self-defensibility check that classifies each source URL into
a tier and flags any cell whose only source is broker-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from urllib.parse import urlparse


# Primary sources — defensible on their own
PRIMARY_SOURCE_DOMAINS = {
    # Statistical agencies
    "bps.go.id", "bi.go.id", "bot.or.th", "nesdc.go.th", "bsp.gov.ph",
    "psa.gov.ph", "dosm.gov.my", "bnm.gov.my", "gso.gov.vn", "sbv.gov.vn",
    # Stock exchanges
    "idx.co.id", "set.or.th", "pse.com.ph", "bursamalaysia.com", "hsx.vn",
}

# Respected business publications — defensible
TIER1_NEWS_DOMAINS = {
    # Major news wires
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com",
    # Regional
    "theedgemalaysia.com", "kontan.co.id", "bisnis.com", "nationthailand.com",
    "kaohooninternational.com", "thansettakij.com", "insiderph.com",
    "insideretail.asia", "philstar.com", "mb.com.ph", "gmanetwork.com",
    "businessmirror.com.ph", "vietnambiz.vn", "businessworld.com.ph",
    "business-indonesia.org", "theiconomics.com", "logisticsnews.ph",
    "moomoo.com", "bareksa.com", "paretosaham.com",
    "id.tradingview.com",  # TradingView (Kontan syndicated)
}


def _source_tier(url: str | None) -> int:
    """3 = broker (default), 2 = news, 1 = primary (agency/regulator/company). 0 = no URL."""
    if not url:
        return 0
    host = (urlparse(url).hostname or "").lower().lstrip("www.")
    for d in PRIMARY_SOURCE_DOMAINS:
        if host == d or host.endswith("." + d):
            return 1
    for d in TIER1_NEWS_DOMAINS:
        if host == d or host.endswith("." + d):
            return 2
    # Heuristic: company IR pages (anything with /ir/, /investor/, /press-release/)
    if any(seg in url.lower() for seg in ["/ir/", "/investor/", "/press-release/", "/quarterly-results/"]):
        return 1
    # Common company domains (heuristic — list can grow)
    company_hosts = {
        "mrdiy.com", "mapi.id", "mk.co.th", "cpall.co.th", "cpaxtra.com",
        "homepro.co.th", "acehardware.co.id", "alfamart.co.id",
        "7-eleven.com.ph", "puregold.com.ph", "ecoshop.com.my",
        "bjc.co.th", "centralretail.com", "thegioididong.com",
        "mapaktif.com", "mapbogadiperkasa.com", "fore.coffee",
        "alfamidi.co.id", "99speedmart.com.my", "stockbit.com",
    }
    for d in company_hosts:
        if host == d or host.endswith("." + d):
            return 1
    return 3  # default to broker


def check_self_defensible(e2e: dict[str, tuple[str | float | None, str | None]]) -> list[str]:
    """Return warnings for cells whose only source is Tier 3 (broker)."""
    warnings = []
    for k, (val, src) in e2e.items():
        if val is None or src is None:
            continue
        if _source_tier(src) == 3:
            warnings.append(f"not-defensible: {k} value={val} source={src} (broker only, no primary cross-check)")
    return warnings


@dataclass
class GradeReport:
    cells_total: int = 0
    cells_match: int = 0
    cells_differ: int = 0
    cells_missing: int = 0          # E2E has no value, reference does
    cells_extra: int = 0            # E2E has value, reference doesn't
    cells_with_source: int = 0
    cells_without_source: int = 0
    cells_not_defensible: int = 0   # broker-only
    warnings: list[str] = field(default_factory=list)
    diffs: list[dict] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.cells_match / self.cells_total if self.cells_total else 0.0

    @property
    def source_rate(self) -> float:
        return self.cells_with_source / self.cells_total if self.cells_total else 0.0

    @property
    def defensible_rate(self) -> float:
        with_value = self.cells_total - self.cells_missing
        if with_value == 0:
            return 1.0
        defended = with_value - self.cells_not_defensible
        return defended / with_value


def _to_float(v) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).strip().rstrip("%").strip()
        if "," in s and "." in s:
            s = s.replace(",", "")
        elif "," in s and "." not in s:
            s = s.replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return None


def grade_e2e(
    e2e: dict[str, tuple[str | float | None, str | None]],
    reference: dict[str, tuple[str | float | None, str | None]],
    *,
    tolerance: float = 0.5,
    prior_cycle: dict[str, str] | None = None,
    check_defensibility: bool = True,
) -> GradeReport:
    """Compare E2E results to a reference.

    Args:
        e2e:        {cell_key: (value, source_url)} from the E2E agent
        reference:  {cell_key: (value, source_url)} from the hidden ref
        tolerance:  pp tolerance for SSSG (default 0.5)
        prior_cycle: {cell_key: value} from prior research notes — flags verbatim copies
        check_defensibility: if True, also flag broker-only sources
    """
    r = GradeReport()
    keys = sorted(set(e2e) | set(reference))
    for k in keys:
        r.cells_total += 1
        e_val, e_src = e2e.get(k, (None, None))
        ref_val, _ref_src = reference.get(k, (None, None))

        # source check
        if e_src:
            r.cells_with_source += 1
        else:
            if e_val is not None:
                r.cells_without_source += 1
                r.warnings.append(f"no-source: {k} value={e_val}")

        # value check
        w = _to_float(e_val)
        ref = _to_float(ref_val)
        if w is None and ref is None:
            r.cells_match += 1  # both null is success
        elif w is None:
            r.cells_missing += 1
            r.warnings.append(f"missing-in-e2e: {k} ref={ref_val}")
        elif ref is None:
            r.cells_extra += 1
            r.cells_match += 1  # extra info is fine
        else:
            if abs(w - ref) <= tolerance:
                r.cells_match += 1
            else:
                r.cells_differ += 1
                r.diffs.append({"key": k, "e2e": w, "ref": ref, "diff": abs(w - ref)})

        # leakage check
        if prior_cycle and k in prior_cycle and str(prior_cycle[k]) == str(e_val):
            r.warnings.append(f"verbatim-copy: {k} value={e_val} matches prior cycle")

    # self-defensibility
    if check_defensibility:
        for w in check_self_defensible(e2e):
            r.cells_not_defensible += 1
            r.warnings.append(w)

    return r
