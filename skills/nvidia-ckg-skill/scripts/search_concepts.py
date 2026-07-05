#!/usr/bin/env python3
"""Search for concepts within a CKG domain."""
import argparse
import os
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    RICH = True
except ImportError:
    RICH = False

DEFAULT_PATH = os.environ.get("CKG_PATH", "~/Desktop/Knowledge_Graph_Graphify")

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from _parse import find_domain_file, parse_nodes as _parse_nodes


def parse_nodes(text: str) -> list[dict]:
    return list(_parse_nodes(text).values())


def search_nodes(nodes: list[dict], query: str) -> list[dict]:
    q = query.lower()
    results = []
    for n in nodes:
        score = 0
        if q in n["id"].lower():
            score += 3
        if q in n["display"].lower():
            score += 2
        if q in n["desc"].lower():
            score += 1
        if score:
            results.append((score, n))
    results.sort(key=lambda x: -x[0])
    return [n for _, n in results]


def main():
    parser = argparse.ArgumentParser(description="Search concepts within a CKG domain.")
    parser.add_argument("domain", help="Domain slug (e.g. cuda-toolkit)")
    parser.add_argument("query", help="Search keyword or phrase")
    parser.add_argument("--path", "-p", default=DEFAULT_PATH)
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max results (default: 10)")
    args = parser.parse_args()

    search_path = Path(args.path).expanduser()
    f = find_domain_file(search_path, args.domain)
    if not f:
        print(f"ERROR: Domain '{args.domain}' not found in {search_path}.", file=sys.stderr)
        sys.exit(1)

    nodes = parse_nodes(f.read_text(errors="replace"))
    matches = search_nodes(nodes, args.query)[:args.limit]

    if not matches:
        print(f"No concepts matching '{args.query}' in domain '{args.domain}'.")
        print("Try a shorter keyword or run list_domains.py to verify the domain slug.")
        sys.exit(0)

    if RICH:
        console = Console()
        table = Table(title=f"Concepts matching '{args.query}' in {args.domain}", show_lines=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="yellow", no_wrap=True)
        table.add_column("Display Name")
        table.add_column("Description")
        for n in matches:
            table.add_row(n["id"], n["type"], n["display"], n["desc"][:120] + ("…" if len(n["desc"]) > 120 else ""))
        console.print(table)
        console.print(f"\n[dim]{len(matches)} result(s). Use query_ckg.py <domain> <concept-id> to traverse.[/dim]")
    else:
        print(f"\nConcepts matching '{args.query}' in {args.domain}:\n")
        for n in matches:
            print(f"  [{n['type']}] {n['id']}")
            print(f"    {n['display']}")
            print(f"    {n['desc'][:100]}{'…' if len(n['desc']) > 100 else ''}\n")
        print(f"{len(matches)} result(s). Use query_ckg.py <domain> <concept-id> to traverse.")


if __name__ == "__main__":
    main()
