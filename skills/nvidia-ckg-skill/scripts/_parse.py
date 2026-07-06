"""Shared CKG file parsing utilities."""
import re
from pathlib import Path


def find_domain_file(path: Path, domain_slug: str) -> Path | None:
    candidates = [
        path / f"ckg-{domain_slug}-v0.1.md",
        path / f"ckg-{domain_slug}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    for f in sorted(path.glob("ckg-*.md")):
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


def parse_nodes(text: str) -> dict[str, dict]:
    """Parse nodes from both CKG formats:
      New: node_id: actual_id_value  (generated CKGs)
      Old: snake_case_id: Display Name  (hand-authored CKGs)
    Returns dict keyed by node ID.
    """
    nodes: dict[str, dict] = {}
    current: dict = {}
    in_nodes = False
    _KNOWN_FIELDS = {"type", "desc", "deps", "node_id", "display", "version", "domain", "nodes", "edges", "domains", "created", "author", "purpose", "parent_ckg", "benchmark", "dataset", "benchmarked", "this_domain_f1", "queries_tested", "rag_baseline_f1", "graphrag_baseline_f1", "mean_tokens", "paper"}

    def save_current():
        if current and current.get("id"):
            nodes[current["id"]] = dict(current)

    for line in text.splitlines():
        if line.strip() == "## NODES":
            in_nodes = True
            continue
        if in_nodes and line.startswith("## "):
            save_current()
            current = {}
            break
        if not in_nodes:
            continue
        if line.startswith("### "):
            continue

        stripped = line.strip()

        # New format: "node_id: actual_value" at column 0
        if line.startswith("node_id:"):
            save_current()
            actual_id = line[len("node_id:"):].strip()
            if actual_id:
                current = {"id": actual_id, "display": actual_id.replace("_", " ").title(), "type": "", "desc": "", "deps": []}
            continue

        # Property lines (indented, or known field names)
        if stripped.startswith("type:"):
            current["type"] = stripped[5:].strip()
        elif stripped.startswith("desc:"):
            current["desc"] = stripped[5:].strip()
        elif stripped.startswith("display:"):
            current["display"] = stripped[8:].strip()
        elif stripped.startswith("deps:"):
            deps_str = stripped[5:].strip().strip("[]")
            current["deps"] = [d.strip() for d in deps_str.split(",") if d.strip() and d.strip() != "null"]

        # Old format: "snake_case: Display Name" at column 0 (not a known meta field)
        elif (line and not line.startswith(" ") and not line.startswith("\t")
              and ":" in line and not line.startswith("#")):
            key, _, val = line.partition(":")
            key = key.strip()
            # Must look like a node ID: lowercase snake_case, not a known meta field
            if (key not in _KNOWN_FIELDS
                    and key == key.lower()
                    and re.match(r'^[a-z][a-z0-9_]*$', key)):
                save_current()
                current = {"id": key, "display": val.strip(), "type": "", "desc": "", "deps": []}

        # Bare format: "snake_case_id" at column 0, no colon (third CKG variant)
        elif (line and not line.startswith(" ") and not line.startswith("\t")
              and ":" not in line and not line.startswith("#")
              and re.match(r'^[a-z][a-z0-9_]*$', line.strip())):
            save_current()
            actual_id = line.strip()
            current = {"id": actual_id, "display": actual_id.replace("_", " ").title(), "type": "", "desc": "", "deps": []}

    save_current()
    return nodes


def parse_edges(text: str) -> list[tuple[str, str, str]]:
    """Returns list of (source, relation, target). Handles three formats:
      --[REL]-->   new format with brackets
      --REL-->     no brackets, double dash
      -REL->       no brackets, single dash
    """
    edges = []
    in_edges = False
    patterns = [
        re.compile(r'(\S+)\s+--\[(\w+)\]-->\s+(\S+)'),   # --[REL]-->
        re.compile(r'(\S+)\s+--(\w+)-->\s+(\S+)'),         # --REL-->
        re.compile(r'(\S+)\s+-(\w+)->\s+(\S+)'),           # -REL->
    ]
    for line in text.splitlines():
        if line.strip() == "## EDGES":
            in_edges = True
            continue
        if in_edges and line.startswith("## "):
            break
        if not in_edges:
            continue
        for pattern in patterns:
            m = pattern.search(line)
            if m:
                edges.append((m.group(1), m.group(2), m.group(3)))
                break
    return edges


def parse_section(text: str, header: str) -> list[str]:
    lines, active = [], False
    for line in text.splitlines():
        if line.strip() == f"## {header}":
            active = True
            continue
        if active and line.startswith("##"):
            break
        if active and line.strip():
            lines.append(line.strip())
    return lines
