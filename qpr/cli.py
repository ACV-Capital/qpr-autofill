"""CLI entry point for the QPR (Quarterly Research) auto-fill package.

Subcommands:
- run-quarter <YYYYQn>     Render briefs (SSSG + macro) with channel memory
- verify-results <json>...  Verify URLs in agent result JSONs against saved pages
- preflight --sheet-id X    Run self-defensibility check on a working sheet
- write-sheet --sheet-id X  Write verified values to a working sheet
- update-channel-memory     Update the channel memory from a working sheet
- grade <working> <ref>     Compare two sheets cell-by-cell
- grade-e2e                 Grade an E2E test run against a reference
- e2e-run                   Spawn a fresh subagent in a secluded environment
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import date


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "examples" / "tickers.yaml"
DEFAULT_MEMORY = REPO_ROOT / "qpr" / "data" / "channel_memory.json"


def cmd_run_quarter(args):
    """Render the SSSG + macro briefs for a given quarter."""
    from qpr.tickers import load_manifest
    from qpr.channel_memory import load_memory
    from qpr.brief import render_sssg_brief

    quarter = args.quarter
    tickers = load_manifest(args.manifest)
    sssg_tickers = [t for t in tickers if t.sssg_applicable]

    if args.memory and Path(args.memory).exists():
        memory = load_memory(args.memory)
    else:
        memory = {}

    # SSSG brief
    sssg_md = render_sssg_brief(
        quarter=quarter,
        tickers=tickers,
        sssg_tickers=sssg_tickers,
        channel_memory=memory,
    )
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sssg_path = out_dir / f"AGENT_SSSG_{quarter}_BRIEF.md"
    sssg_path.write_text(sssg_md)
    print(f"Wrote {sssg_path}")

    # Macro brief (basic placeholder — same structure, different agent)
    macro_path = out_dir / f"AGENT_MACRO_{quarter}_BRIEF.md"
    macro_path.write_text(f"""# Macro Brief — {quarter}

You are researching **GDP, FX, and private consumption** for the 5 SEA-5 countries for {quarter}.

## Countries
- Indonesia (BPS, BI)
- Thailand (NESDC, BOT)
- Philippines (PSA)
- Malaysia (DOSM, BNM)
- Vietnam (GSO, SBV)

## Hard rules
1. Cite primary statistical agency (Tier 1) or major news wire (Tier 2)
2. No broker-only sources for macro
3. Each value must have a public URL

## Output
Write to `notes/agent_macro_{quarter.lower()}_results.json` with the structure:
```
{{
  "country": "Indonesia",
  "gdp_real_yoy_pct": <number>,
  "gdp_source": "<url>",
  "private_consumption_yoy_pct": <number>,
  "private_consumption_source": "<url>",
  "fx_avg": <number or null>,
  "fx_source": "<url or null>
}}
```
""")
    print(f"Wrote {macro_path}")

    # Print dispatch instructions
    print()
    print("=" * 60)
    print(f"NEXT: Dispatch 2 subagents with these briefs")
    print(f"  Agent 1 (SSSG): {sssg_path}")
    print(f"  Agent 2 (Macro): {macro_path}")
    print("=" * 60)


def cmd_verify_results(args):
    """Verify URLs in agent result JSONs against saved pages."""
    from qpr.verify import verify_value_on_page

    if not args.pages_dir:
        print("ERROR: --pages-dir is required", file=sys.stderr)
        sys.exit(1)
    pages_dir = Path(args.pages_dir)
    total = 0
    ok = 0
    for json_path in args.results:
        data = json.loads(Path(json_path).read_text())
        for ticker, result in data.get("results", {}).items():
            for key, url in result.items():
                if not key.endswith("_source") or not url:
                    continue
                value_key = key.replace("_source", "_pct")
                value = result.get(value_key)
                if value is None:
                    continue
                total += 1
                # derive page filename from URL
                page_name = url.split("/")[2].replace(".", "_") + ".html"
                page_path = pages_dir / page_name
                if not page_path.exists():
                    # try alternative: search by domain
                    candidates = list(pages_dir.glob(f"*{url.split('/')[2].replace('.', '_')}*"))
                    if candidates:
                        page_path = candidates[0]
                    else:
                        print(f"  [SKIP] {ticker} {value} — no page file for {url}")
                        continue
                res = verify_value_on_page(page_path, str(value))
                if res.found:
                    ok += 1
                    print(f"  [OK]   {ticker} {value} → {res.matched_text}" + (f" ({res.warning})" if res.warning else ""))
                else:
                    print(f"  [FAIL] {ticker} {value} not found in {page_path.name}")
    print(f"\n{ok}/{total} values verified")


def cmd_preflight(args):
    """Run the self-defensibility check on a working sheet."""
    from qpr.grade_e2e import grade_e2e, check_self_defensible
    from qpr.sheets import read_sheet

    sheet = read_sheet(args.sheet_id, args.tab)
    # Assume a layout where column N has the value and column N+1 has the URL
    # For now, we just check defensibility of any URL we can find
    # (A full preflight impl would parse the working sheet structure)
    pairs = {}
    # TODO: parse sheet structure properly
    if not pairs:
        print(f"Loaded {len(sheet)} non-empty cells from {args.sheet_id} (tab: {args.tab or 'default'})")
        print("NOTE: preflight requires a structured sheet layout (value/URL pairs in adjacent columns).")
        print("      For now, run `qpr verify-results` on the agent JSONs to confirm defensibility.")
        return
    warnings = check_self_defensible(pairs)
    if warnings:
        print(f"NOT DEFENSIBLE ({len(warnings)} cells):")
        for w in warnings:
            print(f"  - {w}")
        sys.exit(1)
    print("All cells self-defensible.")


def cmd_update_channel_memory(args):
    """Update the channel memory from a working sheet or offline results JSONs."""
    from qpr.channel_memory import load_memory, save_memory, update_after_cycle
    from qpr.sheets import read_sheet

    if not args.results and not args.sheet_id:
        print("ERROR: either --sheet-id or --results is required", file=sys.stderr)
        sys.exit(1)

    cycle_results: dict[str, dict] = {}
    if args.results:
        for json_path in args.results:
            data = json.loads(Path(json_path).read_text())
            for ticker, result in data.get("results", {}).items():
                url = result.get("sssg_source") or result.get("sssg_yoy_pct_source")
                value = result.get("sssg_yoy_pct") or result.get("sssg_yoy_pct")
                if url:
                    cycle_results[ticker] = {
                        "value": value,
                        "url": url,
                        "channel_used": result.get("channel_used", ""),
                    }

    if args.sheet_id:
        sheet = read_sheet(args.sheet_id, args.tab)
        # TODO: parse the sheet into (ticker, value, url) tuples
        # For now, the offline --results path is the primary workflow.

    if not cycle_results:
        print("No results to process. Pass --results <agent.json>")
        return

    memory = load_memory(args.memory_file)
    update_after_cycle(memory, cycle_results)
    save_memory(memory, args.memory_file)
    print(f"Updated {args.memory_file} with {len(cycle_results)} results")


def cmd_grade(args):
    """Compare two sheets cell-by-cell (working vs reference)."""
    from qpr.sheets import read_sheet
    from qpr.classify import classify, Status

    working = read_sheet(args.working_sheet, args.tab)
    reference = read_sheet(args.ref_sheet, args.tab)
    if not args.col_map:
        # naive: same cell refs
        common = set(working) & set(reference)
    else:
        common = set(args.col_map.split(","))
    counts = {s.value: 0 for s in Status}
    diffs = []
    for k in sorted(common):
        w = _parse(working.get(k))
        r = _parse(reference.get(k))
        s = classify(w, r, tolerance=args.tolerance)
        counts[s.value] += 1
        if s == Status.DIFFER:
            diffs.append((k, w, r))
    print(f"Cells: {sum(counts.values())}")
    for s, n in counts.items():
        print(f"  {s:10s} {n}")
    if diffs:
        print(f"\nDiffs:")
        for k, w, r in diffs:
            print(f"  {k}: working={w} reference={r}")


def cmd_grade_e2e(args):
    """Grade an E2E test run against a reference sheet."""
    from qpr.grade_e2e import grade_e2e
    from qpr.sheets import read_sheet

    e2e = read_sheet(args.e2e_sheet_id, args.tab)
    reference = read_sheet(args.ref_sheet_id, args.tab)

    prior_cycle = None
    if args.prior_cycle_path and Path(args.prior_cycle_path).exists():
        prior_cycle = json.loads(Path(args.prior_cycle_path).read_text())

    report = grade_e2e(
        e2e, reference,
        tolerance=args.tolerance,
        prior_cycle=prior_cycle,
        check_defensibility=not args.no_defensibility,
    )
    print(f"Cells total: {report.cells_total}")
    print(f"Cells match: {report.cells_match}  ({report.pass_rate:.0%})")
    print(f"Cells differ: {report.cells_differ}")
    print(f"Cells missing: {report.cells_missing}")
    print(f"Cells extra: {report.cells_extra}")
    print(f"Cells with source: {report.cells_with_source}  ({report.source_rate:.0%})")
    print(f"Cells without source: {report.cells_without_source}")
    print(f"Cells not defensible: {report.cells_not_defensible}  ({report.defensible_rate:.0%} defensible)")
    if report.warnings:
        print(f"\nWarnings:")
        for w in report.warnings[:30]:
            print(f"  - {w}")
        if len(report.warnings) > 30:
            print(f"  ... and {len(report.warnings) - 30} more")
    if report.diffs:
        print(f"\nDiffs (>tolerance):")
        for d in report.diffs[:30]:
            print(f"  - {d['key']}: e2e={d['e2e']} ref={d['ref']} Δ={d['diff']:.2f}")

    passed = (
        report.pass_rate >= args.min_pass_rate
        and report.cells_without_source == 0
        and (args.no_defensibility or report.defensible_rate >= args.min_defensible_rate)
    )
    if passed:
        print("\nE2E: PASS")
        sys.exit(0)
    else:
        print("\nE2E: FAIL")
        sys.exit(1)


def cmd_e2e_run(args):
    """Spawn a fresh subagent in a secluded environment.

    NOTE: this is a stub. The full implementation lives in Phase E Task 19
    and requires: a secluded workdir, a separate service account JSON, and
    a runner (claude-code / codex / opencode) installed.
    """
    print("e2e-run is a stub in v0.1. See docs/E2E.md for the full setup.")
    print(f"  Quarter: {args.quarter}")
    print(f"  Sheet: {args.sheet_id}")
    print(f"  Workdir: {args.workdir}")
    sys.exit(2)


def _parse(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        s = str(v).strip().rstrip("%").strip()
        if "," in s and "." in s:
            s = s.replace(",", "")
        elif "," in s and "." not in s:
            s = s.replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return None


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="qpr", description="QPR Auto-Fill CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run-quarter", help="Render the SSSG + macro briefs for a quarter")
    p.add_argument("quarter", help="Quarter like 2026Q2")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p.add_argument("--memory", default=str(DEFAULT_MEMORY))
    p.add_argument("--output-dir", default="notes")
    p.set_defaults(func=cmd_run_quarter)

    p = sub.add_parser("verify-results", help="Verify URLs in agent result JSONs")
    p.add_argument("results", nargs="+", help="Agent result JSON files")
    p.add_argument("--pages-dir", required=True, help="Directory of saved page HTMLs")
    p.set_defaults(func=cmd_verify_results)

    p = sub.add_parser("preflight", help="Self-defensibility check on a working sheet")
    p.add_argument("--sheet-id", required=True)
    p.add_argument("--tab", default=None)
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("update-channel-memory", help="Update channel memory from results")
    p.add_argument("--sheet-id", default=None)
    p.add_argument("--tab", default=None)
    p.add_argument("--results", action="append", default=[], help="Agent result JSON (can repeat)")
    p.add_argument("--memory-file", default=str(DEFAULT_MEMORY))
    p.set_defaults(func=cmd_update_channel_memory)

    p = sub.add_parser("grade", help="Compare two sheets cell-by-cell")
    p.add_argument("working_sheet")
    p.add_argument("ref_sheet")
    p.add_argument("--tab", default=None)
    p.add_argument("--col-map", default=None, help="Comma-separated cell refs to compare")
    p.add_argument("--tolerance", type=float, default=0.5)
    p.set_defaults(func=cmd_grade)

    p = sub.add_parser("grade-e2e", help="Grade an E2E test against a reference")
    p.add_argument("--e2e-sheet-id", required=True)
    p.add_argument("--ref-sheet-id", required=True)
    p.add_argument("--tab", default=None)
    p.add_argument("--tolerance", type=float, default=0.5)
    p.add_argument("--min-pass-rate", type=float, default=0.8)
    p.add_argument("--min-defensible-rate", type=float, default=0.8)
    p.add_argument("--no-defensibility", action="store_true")
    p.add_argument("--prior-cycle-path", default=None)
    p.set_defaults(func=cmd_grade_e2e)

    p = sub.add_parser("e2e-run", help="Spawn a fresh subagent (Phase E)")
    p.add_argument("--quarter", required=True)
    p.add_argument("--sheet-id", required=True)
    p.add_argument("--workdir", required=True)
    p.add_argument("--plugin-dir", default=".")
    p.set_defaults(func=cmd_e2e_run)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
