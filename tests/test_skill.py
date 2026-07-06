"""Basic smoke tests for nvidia-ckg-skill scripts."""
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "skills" / "nvidia-ckg-skill" / "scripts"
CKG_PATH = Path.home() / "Desktop" / "Knowledge_Graph_Graphify"


def run_script(name: str, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True, text=True, timeout=30,
        env={"CKG_PATH": str(CKG_PATH), "PATH": __import__("os").environ["PATH"]},
    )


def test_list_domains_runs():
    r = run_script("list_domains.py", "--path", str(CKG_PATH))
    assert r.returncode == 0, r.stderr
    assert "nvidia" in r.stdout.lower()


def test_list_domains_filter():
    r = run_script("list_domains.py", "--filter", "cuda", "--path", str(CKG_PATH))
    assert r.returncode == 0, r.stderr
    assert "cuda" in r.stdout.lower()


def test_load_domain_cuda():
    if not (CKG_PATH / "ckg-nvidia-cuda-toolkit-v0.1.md").exists():
        import pytest; pytest.skip("cuda-toolkit CKG not found locally")
    r = run_script("load_domain.py", "nvidia-cuda-toolkit", "--path", str(CKG_PATH), "--summary")
    assert r.returncode == 0, r.stderr
    assert "cuda" in r.stdout.lower()


def test_search_concepts():
    if not (CKG_PATH / "ckg-nvidia-tensorrt-triton-v0.1.md").exists():
        import pytest; pytest.skip("tensorrt-triton CKG not found locally")
    r = run_script("search_concepts.py", "nvidia-tensorrt-triton", "quantization", "--path", str(CKG_PATH))
    assert r.returncode == 0, r.stderr


def test_query_ckg_depth1():
    if not (CKG_PATH / "ckg-nvidia-tensorrt-triton-v0.1.md").exists():
        import pytest; pytest.skip("tensorrt-triton CKG not found locally")
    r = run_script("query_ckg.py", "nvidia-tensorrt-triton", "tensorrt_sdk", "--depth", "1", "--path", str(CKG_PATH))
    assert r.returncode == 0, r.stderr


def test_query_ckg_unknown_concept():
    if not (CKG_PATH / "ckg-nvidia-cuda-toolkit-v0.1.md").exists():
        import pytest; pytest.skip("cuda-toolkit CKG not found locally")
    r = run_script("query_ckg.py", "nvidia-cuda-toolkit", "does_not_exist_xyz", "--path", str(CKG_PATH))
    assert r.returncode != 0
    assert "not found" in r.stdout.lower() or "not found" in r.stderr.lower()
