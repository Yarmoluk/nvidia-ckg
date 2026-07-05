#!/usr/bin/env python3
"""List available CKG domains in the configured path."""
import argparse
import os
import re
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    RICH = True
except ImportError:
    RICH = False

DEFAULT_PATH = os.environ.get("CKG_PATH", "~/Desktop/Knowledge_Graph_Graphify")


def parse_meta(text: str) -> dict:
    meta = {}
    in_meta = False
    for line in text.splitlines():
        if line.strip() == "## META":
            in_meta = True
            continue
        if in_meta and line.startswith("##"):
            break
        if in_meta and ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta


def list_domains(path: Path, keyword: str = "") -> list[dict]:
    results = []
    for f in sorted(path.glob("ckg-*.md")):
        text = f.read_text(errors="replace")
        meta = parse_meta(text)
        domain = meta.get("domain", "")
        if not domain:
            continue
        if keyword and keyword.lower() not in domain.lower() and keyword.lower() not in meta.get("purpose", "").lower():
            continue
        results.append({
            "domain": domain,
            "nodes": meta.get("nodes", "?"),
            "edges": meta.get("edges", "?"),
            "domains": meta.get("domains", "?"),
            "version": meta.get("version", "?"),
            "file": f.name,
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="List available CKG domains.")
    parser.add_argument("--filter", "-f", metavar="KEYWORD", default="", help="Filter by keyword in domain name or purpose.")
    parser.add_argument("--path", "-p", default=DEFAULT_PATH, help="Path to CKG files directory.")
    args = parser.parse_args()

    search_path = Path(args.path).expanduser()
    if not search_path.is_dir():
        print(f"ERROR: CKG path not found: {search_path}", file=sys.stderr)
        print("Set CKG_PATH environment variable or pass --path.", file=sys.stderr)
        sys.exit(1)

    domains = list_domains(search_path, args.filter)

    if not domains:
        print(f"No CKG domains found in {search_path}" + (f" matching '{args.filter}'" if args.filter else "") + ".")
        sys.exit(0)

    if RICH:
        console = Console()
        table = Table(title=f"CKG Domains — {search_path}", show_lines=False)
        table.add_column("Domain", style="cyan", no_wrap=True)
        table.add_column("Nodes", justify="right", style="green")
        table.add_column("Edges", justify="right", style="green")
        table.add_column("Sub-domains", justify="right")
        table.add_column("Version")
        table.add_column("File", style="dim")
        for d in domains:
            table.add_row(d["domain"], d["nodes"], d["edges"], d["domains"], d["version"], d["file"])
        console.print(table)
        console.print(f"\n[dim]{len(domains)} domains found.[/dim]")
    else:
        print(f"CKG Domains — {search_path}\n")
        print(f"{'Domain':<50} {'Nodes':>6} {'Edges':>6}  File")
        print("-" * 90)
        for d in domains:
            print(f"{d['domain']:<50} {d['nodes']:>6} {d['edges']:>6}  {d['file']}")
        print(f"\n{len(domains)} domains found.")


if __name__ == "__main__":
    main()
