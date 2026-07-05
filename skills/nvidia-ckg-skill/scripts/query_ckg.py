#!/usr/bin/env python3
"""Query a concept's subgraph within a CKG domain."""
import argparse
import os
import re
import sys
from collections import deque
from pathlib import Path

try:
    from rich.console import Console
    from rich.tree import Tree
    from rich.text import Text
    RICH = True
except ImportError:
    RICH = False

DEFAULT_PATH = os.environ.get("CKG_PATH", "~/Desktop/Knowledge_Graph_Graphify")

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from _parse import find_domain_file, parse_nodes as _parse_nodes_dict, parse_edges as _parse_edges

EDGE_COLORS = {
    "ENABLES": "green", "REQUIRES": "red", "EXTENDS": "blue",
    "IMPLEMENTS": "cyan", "OPTIMIZES": "yellow", "WRAPS": "magenta",
    "CONFIGURES": "white", "MONITORS": "bright_white", "REPLACES": "red",
    "USED_IN": "green", "PART_OF": "blue", "VALIDATES": "cyan",
    "GENERATES": "yellow", "CONSUMES": "magenta",
}


def parse_nodes(text: str) -> dict[str, dict]:
    return _parse_nodes_dict(text)


def parse_edges(text: str) -> list[tuple[str, str, str]]:
    return _parse_edges(text)


def bfs_subgraph(concept_id: str, nodes: dict, edges: list, depth: int) -> dict:
    """BFS from concept_id up to `depth` hops. Returns adjacency info."""
    adjacency: dict[str, list] = {nid: [] for nid in nodes}
    for src, rel, tgt in edges:
        if src in adjacency:
            adjacency[src].append((rel, tgt, "out"))
        if tgt in adjacency:
            adjacency[tgt].append((rel, src, "in"))

    visited = {concept_id: 0}
    queue = deque([concept_id])
    subgraph_edges = []

    while queue:
        current = queue.popleft()
        current_depth = visited[current]
        if current_depth >= depth:
            continue
        for rel, neighbor, direction in adjacency.get(current, []):
            if neighbor not in nodes:
                continue
            edge = (current, rel, neighbor) if direction == "out" else (neighbor, rel, current)
            if edge not in subgraph_edges:
                subgraph_edges.append(edge)
            if neighbor not in visited:
                visited[neighbor] = current_depth + 1
                queue.append(neighbor)

    return {"visited": visited, "edges": subgraph_edges}


def main():
    parser = argparse.ArgumentParser(description="Query a concept's subgraph within a CKG domain.")
    parser.add_argument("domain", help="Domain slug (e.g. cuda-toolkit)")
    parser.add_argument("concept", help="Concept node ID (e.g. tensorrt_sdk)")
    parser.add_argument("--depth", "-d", type=int, default=1, choices=[1, 2, 3],
                        help="Traversal depth: 1=immediate neighbors, 2=2-hop, 3=full upstream chain (default: 1)")
    parser.add_argument("--path", "-p", default=DEFAULT_PATH)
    args = parser.parse_args()

    search_path = Path(args.path).expanduser()
    f = find_domain_file(search_path, args.domain)
    if not f:
        print(f"ERROR: Domain '{args.domain}' not found in {search_path}.", file=sys.stderr)
        sys.exit(1)

    text = f.read_text(errors="replace")
    nodes = parse_nodes(text)
    edges = parse_edges(text)

    if args.concept not in nodes:
        # Fuzzy fallback
        candidates = [nid for nid in nodes if args.concept.lower() in nid.lower()]
        if candidates:
            print(f"Concept '{args.concept}' not found. Did you mean: {', '.join(candidates[:5])}?", file=sys.stderr)
        else:
            print(f"ERROR: Concept '{args.concept}' not found in domain '{args.domain}'.", file=sys.stderr)
            print("Run search_concepts.py to find valid concept IDs.", file=sys.stderr)
        sys.exit(1)

    root = nodes[args.concept]
    result = bfs_subgraph(args.concept, nodes, edges, args.depth)

    if RICH:
        console = Console()
        console.print(f"\n[bold cyan]{root['id']}[/bold cyan] [{root['type']}]  {root['display']}")
        console.print(f"[dim]{root['desc'][:200]}{'…' if len(root['desc']) > 200 else ''}[/dim]")
        console.print(f"\nDepth: {args.depth}  Reachable nodes: {len(result['visited'])}  Edges in subgraph: {len(result['edges'])}\n")

        # Print edges grouped by source
        from itertools import groupby
        sorted_edges = sorted(result["edges"], key=lambda e: e[0])
        for src, group in groupby(sorted_edges, key=lambda e: e[0]):
            src_node = nodes.get(src, {})
            src_label = f"[cyan]{src}[/cyan] [{src_node.get('type', '')}]"
            console.print(src_label)
            for _, rel, tgt in group:
                tgt_node = nodes.get(tgt, {})
                color = EDGE_COLORS.get(rel, "white")
                console.print(f"  --[{color}]{rel}[/{color}]--> [cyan]{tgt}[/cyan] [{tgt_node.get('type', '')}]")
                if tgt_node.get("desc"):
                    console.print(f"  [dim]    {tgt_node['desc'][:100]}{'…' if len(tgt_node.get('desc','')) > 100 else ''}[/dim]")
        console.print(f"\n[dim]Traversal complete. {len(result['edges'])} edges, {len(result['visited'])} nodes reached.[/dim]")
    else:
        print(f"\n{root['id']} [{root['type']}]  {root['display']}")
        print(f"{root['desc'][:200]}")
        print(f"\nDepth: {args.depth}  Reached: {len(result['visited'])} nodes  Edges: {len(result['edges'])}\n")
        for src, rel, tgt in result["edges"]:
            tgt_node = nodes.get(tgt, {})
            print(f"  {src} --[{rel}]--> {tgt} [{tgt_node.get('type', '')}]")
            if tgt_node.get("desc"):
                print(f"      {tgt_node['desc'][:80]}")
        print(f"\n{len(result['edges'])} edges traversed.")


if __name__ == "__main__":
    main()
