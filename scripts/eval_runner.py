#!/usr/bin/env python3
"""
Script-level eval runner for nvidia-ckg-skill.

Runs the 12 positive eval tasks from evals/evals.json by executing the expected
scripts with the expected args. Negative cases (requires LLM routing decision)
are flagged as agent-level and skipped.

Usage:
    python scripts/eval_runner.py [--path CKG_PATH] [--json] [--update-benchmark]

Outputs:
  - Terminal table of pass/fail per task
  - Overall pass rate
  - Optional --json output for CI
  - Optional --update-benchmark patches BENCHMARK.md with latest results
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent / "skills" / "nvidia-ckg-skill"
SCRIPTS_DIR = SKILL_DIR / "scripts"
EVALS_FILE = SKILL_DIR / "evals" / "evals.json"
BENCHMARK_FILE = Path(__file__).parent.parent / "BENCHMARK.md"
DEFAULT_CKG_PATH = os.environ.get("CKG_PATH", str(Path.home() / "Desktop" / "Knowledge_Graph_Graphify"))

try:
    from rich.console import Console
    from rich.table import Table
    RICH = True
except ImportError:
    RICH = False


def run_script(script_name: str, args: list[str], ckg_path: str, timeout: int = 30) -> dict:
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + args + ["--path", ckg_path]
    start = time.monotonic()
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "CKG_PATH": ckg_path},
        )
        elapsed = time.monotonic() - start
        return {
            "returncode": r.returncode,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "elapsed": round(elapsed, 2),
            "timeout": False,
        }
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "TIMEOUT", "elapsed": timeout, "timeout": True}
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e), "elapsed": 0.0, "timeout": False}


def check_output(result: dict, task: dict) -> tuple[bool, str]:
    """Return (passed, reason). Validates by script type, not by prose keyword matching."""
    if result["timeout"]:
        return False, "TIMEOUT"
    if result["returncode"] != 0:
        err = (result["stderr"] or "").strip()[:120]
        return False, f"exit {result['returncode']}: {err}"
    out = (result["stdout"] + result["stderr"]).lower()
    if not out.strip():
        return False, "empty output"

    script = task.get("expected_script", "")
    args = task.get("expected_args", [])

    if script == "list_domains.py":
        # Must list at least one domain slug
        if "nvidia" not in out and "domain" not in out:
            return False, "no domains in output"

    elif script == "load_domain.py":
        # Domain name should appear in output
        domain = next((a for a in args if a.startswith("nvidia-")), "")
        short = domain.replace("nvidia-", "").replace("-", " ").split()[0] if domain else ""
        if short and short not in out:
            return False, f"domain name {short!r} missing from output"

    elif script == "search_concepts.py":
        # Should return matching concepts, not a "No concepts" message
        if "no concepts" in out:
            return False, "no concepts found"

    elif script == "query_ckg.py":
        # Should have edges in the subgraph
        if "-->" not in out and "edges" not in out:
            return False, "no edges in subgraph output"

    return True, "ok"


def run_evals(ckg_path: str) -> list[dict]:
    evals = json.loads(EVALS_FILE.read_text())
    results = []

    for task in evals:
        entry = {
            "id": task["id"],
            "area": task.get("area", ""),
            "positive": task.get("positive", True),
            "prompt": task["prompt"][:80],
        }

        if not task.get("positive", True):
            entry.update({"status": "skip", "reason": "agent-level (requires LLM routing)", "elapsed": 0.0})
            results.append(entry)
            continue

        # Research-brief tasks read a file rather than run a script
        if task.get("expected_action", "").startswith("read "):
            target = SKILL_DIR / task["expected_action"].split("read ", 1)[1].strip()
            if target.exists():
                entry.update({"status": "pass", "reason": "file exists", "elapsed": 0.0})
            else:
                entry.update({"status": "fail", "reason": f"file not found: {target.name}", "elapsed": 0.0})
            results.append(entry)
            continue

        script = task.get("expected_script", "")
        args = task.get("expected_args", [])
        if not script:
            entry.update({"status": "skip", "reason": "no script specified", "elapsed": 0.0})
            results.append(entry)
            continue

        run = run_script(script, args, ckg_path)
        passed, reason = check_output(run, task)
        entry.update({
            "status": "pass" if passed else "fail",
            "reason": reason,
            "elapsed": run["elapsed"],
        })
        results.append(entry)

    return results


def print_table(results: list[dict]):
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    skipped = sum(1 for r in results if r["status"] == "skip")

    if RICH:
        console = Console()
        table = Table(title="nvidia-ckg-skill Eval Results", show_lines=False)
        table.add_column("ID", style="dim", no_wrap=True)
        table.add_column("Area", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Elapsed", justify="right", style="dim")
        table.add_column("Note", style="dim")

        STATUS_STYLE = {"pass": "green", "fail": "red", "skip": "yellow"}
        for r in results:
            style = STATUS_STYLE.get(r["status"], "white")
            table.add_row(
                r["id"],
                r["area"],
                f"[{style}]{r['status'].upper()}[/{style}]",
                f"{r['elapsed']:.2f}s" if r["elapsed"] else "—",
                r["reason"][:60],
            )
        console.print(table)
        console.print(
            f"\n[green]{passed} pass[/green]  [red]{failed} fail[/red]  "
            f"[yellow]{skipped} skip[/yellow]  "
            f"(script-level pass rate: [bold]{passed}/{passed+failed}[/bold] = "
            f"[bold]{100*passed//(passed+failed) if passed+failed else 0}%[/bold])"
        )
    else:
        print(f"\n{'ID':<40} {'Area':<18} {'Status':<8} {'Elapsed':>8}  Note")
        print("-" * 100)
        for r in results:
            print(f"{r['id']:<40} {r['area']:<18} {r['status'].upper():<8} "
                  f"{r['elapsed']:.2f}s  {r['reason'][:50]}")
        rate = f"{100*passed//(passed+failed)}%" if passed+failed else "—"
        print(f"\nPass: {passed}  Fail: {failed}  Skip: {skipped}  Script-level pass rate: {passed}/{passed+failed} = {rate}")


def update_benchmark(results: list[dict]):
    """Patch the Evaluation Agents table in BENCHMARK.md with script-level results."""
    passed = sum(1 for r in results if r["status"] == "pass")
    total = sum(1 for r in results if r["status"] in ("pass", "fail"))
    rate = f"{passed}/{total}" if total else "—"
    pct = f"{100*passed//total}%" if total else "—"

    new_row = f"| Script eval (this runner) | — | {rate} ({pct}) | N/A | N/A | N/A |"

    text = BENCHMARK_FILE.read_text()
    # Replace the existing script eval row if present, else append before end of table
    if "Script eval (this runner)" in text:
        lines = text.splitlines()
        out = []
        for line in lines:
            if "Script eval (this runner)" in line:
                out.append(new_row)
            else:
                out.append(line)
        BENCHMARK_FILE.write_text("\n".join(out) + "\n")
    else:
        # Inject after the Codex row
        text = text.replace(
            "| Codex | GPT-5.4 | — | — | — | — |",
            "| Codex | GPT-5.4 | — | — | — | — |\n" + new_row,
        )
        BENCHMARK_FILE.write_text(text)

    print(f"\nBENCHMARK.md updated — script eval: {rate} ({pct})")


def main():
    parser = argparse.ArgumentParser(description="Run nvidia-ckg-skill script-level evals.")
    parser.add_argument("--path", default=DEFAULT_CKG_PATH, help="Path to CKG files directory.")
    parser.add_argument("--json", action="store_true", help="Output results as JSON.")
    parser.add_argument("--update-benchmark", action="store_true", help="Patch BENCHMARK.md with results.")
    args = parser.parse_args()

    ckg_path = str(Path(args.path).expanduser())

    if not Path(ckg_path).is_dir():
        print(f"ERROR: CKG path not found: {ckg_path}", file=sys.stderr)
        sys.exit(1)

    results = run_evals(ckg_path)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print_table(results)

    if args.update_benchmark:
        update_benchmark(results)


if __name__ == "__main__":
    main()
