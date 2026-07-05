# Query Guide

## Forming a Good Query

### Step 1: Find the domain
```bash
python ./scripts/list_domains.py --filter cuda
```

### Step 2: Find the concept ID
Concept IDs are snake_case. If you know an approximate name, search:
```bash
python ./scripts/search_concepts.py nvidia-cuda-toolkit "tensor"
```

### Step 3: Query the subgraph
```bash
python ./scripts/query_ckg.py nvidia-cuda-toolkit tensorrt_sdk --depth 2
```

## Interpreting Results

Each result line is: `source --[RELATION]--> target [type]`

- `REQUIRES` edges point upstream — these are hard dependencies.
- `ENABLES` edges point downstream — these are capabilities unlocked.
- `REPLACES` marks deprecated paths (go to the target, not the source).
- `OPTIMIZES` shows performance layering — source makes target faster.

## Common Patterns

**What does X need to run?**
Query X at depth=2, look for REQUIRES and PART_OF edges.

**What does X enable?**
Query X at depth=1, look for ENABLES and USED_IN edges pointing out from X.

**What replaced X?**
Query X at depth=1, look for REPLACES edges.

**How do two concepts connect?**
Query both at depth=2 and look for shared neighbors.

## Chaining Traversals

The scripts are composable. Run `search_concepts` to find IDs, then `query_ckg` on each result. Use `--depth 3` for full upstream dependency chains (equivalent to `get_prerequisites` in the ckg-mcp MCP server).
