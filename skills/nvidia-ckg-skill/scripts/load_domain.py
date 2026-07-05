#!/usr/bin/env python3
"""Load a CKG domain and display its structure."""
import argparse
import os
import re
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH = True
except ImportError:
    RICH = False

DEFAULT_PATH = os.environ.get("CKG_PATH", "~/Desktop/Knowledge_Graph_Graphify")


def find_domain_file(path: Path, domain_slug: str) -> Path | None:
    # Exact filename match first
    candidates = [
        path / f"ckg-{domain_slug}-v0.1.md",
        path / f"ckg-{domain_slug}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fuzzy: scan all files for matching domain: field
    for f in path.glob("ckg-*.md"):
        text = f.read_text(errors="replace")
        m = re.search(r'^domain:\s*(.+)$', text, re.MULTILINE)
        if m and m.group(1).strip() == domain_slug:
            return f
    return None


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


def parse_domains(text: str) -> list[str]:
    lines, in_domains = [], False
    for line in text.splitlines():
        if line.strip() == "## DOMAINS":
            in_domains = True
            continue
        if in_domains and line.startswith("##"):
            break
        if in_domains and line.strip():
            lines.append(line.strip())
    return lines


def parse_nodes(text: str) -> list[dict]:
    nodes, current = [], {}
    in_nodes = False
    for line in text.splitlines():
        if line.strip() == "## NODES":
            in_nodes = True
            continue
        if in_nodes and line.startswith("## "):
            break
        if not in_nodes:
            continue
        # Domain header
        if line.startswith("### "):
            continue
        # Node definition: "node_id: Display Name" (no leading spaces)
        if line and not line.startswith(" ") and not line.startswith("\t") and ":" in line and not line.startswith("#"):
            if current:
                nodes.append(current)
            node_id, _, display = line.partition(":")
            current = {"id": node_id.strip(), "display": display.strip(), "type": "", "desc": "", "deps": []}
        elif current:
            stripped = line.strip()
            if stripped.startswith("type:"):
                current["type"] = stripped[5:].strip()
            elif stripped.startswith("desc:"):
                current["desc"] = stripped[5:].strip()
            elif stripped.startswith("deps:"):
                deps_str = stripped[5:].strip().strip("[]")
                current["deps"] = [d.strip() for d in deps_str.split(",") if d.strip()]
    if current:
        nodes.append(current)
    return nodes


def parse_traversals(text: str) -> list[str]:
    lines, in_traversals = [], False
    for line in text.splitlines():
        if line.strip() == "## KEY TRAVERSALS":
            in_traversals = True
            continue
        if in_traversals and line.startswith("##"):
            break
        if in_traversals and line.strip():
            lines.append(line.strip())
    return lines


def main():
    parser = argparse.ArgumentParser(description="Load and display a CKG domain.")
    parser.add_argument("domain", help="Domain slug (e.g. cuda-toolkit, nvidia-developer-ecosystem)")
    parser.add_argument("--path", "-p", default=DEFAULT_PATH, help="Path to CKG files directory.")
    parser.add_argument("--summary", "-s", action="store_true", help="Print compact summary only.")
    args = parser.parse_args()

    search_path = Path(args.path).expanduser()
    f = find_domain_file(search_path, args.domain)
    if not f:
        print(f"ERROR: Domain '{args.domain}' not found in {search_path}.", file=sys.stderr)
        print("Run list_domains.py to see available domains.", file=sys.stderr)
        sys.exit(1)

    text = f.read_text(errors="replace")
    meta = parse_meta(text)
    subdomains = parse_domains(text)
    nodes = parse_nodes(text)
    traversals = parse_traversals(text)

    if RICH:
        console = Console()
        console.print(Panel(
            f"[bold cyan]{meta.get('domain', args.domain)}[/bold cyan]  v{meta.get('version', '?')}\n"
            f"[dim]{meta.get('purpose', '')}[/dim]",
            title="CKG Domain",
            border_style="cyan"
        ))
        # Meta stats
        console.print(f"  Nodes: [green]{meta.get('nodes', len(nodes))}[/green]  "
                      f"Edges: [green]{meta.get('edges', '?')}[/green]  "
                      f"Sub-domains: [green]{meta.get('domains', len(subdomains))}[/green]  "
                      f"File: [dim]{f.name}[/dim]\n")
        # Sub-domains
        console.print("[bold]Sub-domains:[/bold]")
        for d in subdomains:
            console.print(f"  {d}")
        if not args.summary:
            # Nodes table
            console.print()
            table = Table(title="Nodes", show_lines=False)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Type", style="yellow")
            table.add_column("Display Name")
            table.add_column("Deps", justify="right", style="dim")
            for n in nodes:
                table.add_row(n["id"], n["type"], n["display"], str(len(n["deps"])))
            console.print(table)
        # Traversals
        if traversals:
            console.print("\n[bold]Key Traversals:[/bold]")
            for t in traversals:
                console.print(f"  {t}")
    else:
        print(f"\nDomain: {meta.get('domain', args.domain)}  v{meta.get('version', '?')}")
        print(f"Purpose: {meta.get('purpose', '')}")
        print(f"Nodes: {meta.get('nodes', len(nodes))}  Edges: {meta.get('edges', '?')}  File: {f.name}\n")
        print("Sub-domains:")
        for d in subdomains:
            print(f"  {d}")
        if not args.summary and nodes:
            print(f"\nNodes ({len(nodes)}):")
            for n in nodes:
                print(f"  [{n['type']}] {n['id']}: {n['display']}")
        if traversals:
            print("\nKey Traversals:")
            for t in traversals:
                print(f"  {t}")


if __name__ == "__main__":
    main()
