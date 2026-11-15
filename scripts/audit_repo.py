#!/usr/bin/env python3
"""ETH-WCMK repository audit (gate G0/G9 companion).

Produces the evidence the publication plan is based on: tracked-file tiers by
size, total repo weight, the exact list of GitHub blockers, and the check of
the documentation layer required by GitHub best practice.

Usage:
    python3 scripts/audit_repo.py            # full report
    python3 scripts/audit_repo.py --json     # machine-readable
"""
from __future__ import annotations
import argparse
import gzip
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HARD_LIMIT = 100_000_000          # GitHub: files above this are rejected in plain git
LFS_MAX = 2_000_000_000           # Git LFS ceiling (Free plan): 2 GB per file
TIER_KEEP = 5_000_000             # commit directly
TIER_LFS = 100_000_000            # Git LFS
TIER_ARCHIVE = HARD_LIMIT         # Zenodo / GitHub Release, never in git

CACHE_PATHS = {
    ".cache_validation", ".pytest_cache", "_analysis/docx_v9",
    "_analysis/crops", "_analysis/pages", "_analysis/media", ".playwright-mcp",
}

REQUIRED_DOCS = [
    "README.md", "LICENSE", "CITATION.cff", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md", ".gitignore",
    ".gitattributes", "Makefile", "pyproject.toml",
]

JUNK_PATTERNS = ("__pycache__", ".pyc", ".pkl", ".ipynb_checkpoints")


def tracked_files() -> list[tuple[str, int]]:
    out = subprocess.run(["git", "ls-tree", "-r", "-l", "HEAD"],
                         cwd=REPO, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        meta, path = parts
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        try:
            size = int(meta.split()[3])
        except IndexError:
            size = 0
        rows.append((path, size))
    return rows


def compressed_size(path: str) -> int | None:
    """Size after gzip -9, measured without writing anything to disk."""
    try:
        with open(os.path.join(REPO, path), "rb") as fh:
            return len(gzip.compress(fh.read(), 9))
    except (OSError, MemoryError):
        return None


def classify(files):
    keep, lfs, archive, junk = [], [], [], []
    for path, size in files:
        top = path.split("/")[0]
        if any(p in path for p in JUNK_PATTERNS) or top in CACHE_PATHS:
            junk.append((path, size))
        elif top.startswith("Evaluacoes") and (path.endswith(".jsonl") or path.endswith(".csv")):
            # Corpora are deterministic artefacts: the big rounds are published as
            # release assets, not as git blobs. Frozen rounds r2/r3 are the
            # deliberate exception (owner decision, 2026-11-15): they stay in the
            # repository so the v3/v4 corpora can be cloned, not only downloaded.
            round_name = path.split("/")[1] if "/" in path else ""
            if round_name in {"r2", "r3"} and size <= HARD_LIMIT:
                keep.append((path, size))
            else:
                archive.append((path, size))
        elif size <= TIER_KEEP:
            keep.append((path, size))
        elif size <= TIER_LFS:
            lfs.append((path, size))
        else:
            archive.append((path, size))
    return keep, lfs, archive, junk


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = tracked_files()
    keep, lfs, archive, junk = classify(files)
    blockers = [(p, s) for p, s in files if s > HARD_LIMIT]
    git_size = subprocess.run(["du", "-sh", ".git"], cwd=REPO, capture_output=True,
                              text=True).stdout.split("\t")[0]

    archive_gz = {}
    for p, s in archive:
        c = compressed_size(p)
        if c is not None:
            archive_gz[p] = c

    report = {
        "root": REPO,
        "tracked_files": len(files),
        "tracked_bytes": sum(s for _, s in files),
        "git_dir": git_size,
        "tiers": {
            "keep_plain_git": {"count": len(keep), "bytes": sum(s for _, s in keep)},
            "git_lfs": {"count": len(lfs), "bytes": sum(s for _, s in lfs)},
            "archive_external": {"count": len(archive), "bytes": sum(s for _, s in archive),
                                 "bytes_gzipped": sum(archive_gz.values())},
            "exclude_junk": {"count": len(junk), "bytes": sum(s for _, s in junk)},
        },
        "github_blockers": [{"path": p, "bytes": s} for p, s in blockers],
        "documentation_present": {d: os.path.isfile(os.path.join(REPO, d)) for d in REQUIRED_DOCS},
        "largest": sorted(files, key=lambda x: -x[1])[:12],
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    mb = lambda n: f"{n/1_048_576:8.1f} MB"
    print(f"== ETH-WCMK repo audit ==  root: {REPO}")
    print(f"tracked files: {report['tracked_files']}   tracked weight: {mb(report['tracked_bytes'])}   .git: {git_size}")
    print()
    for tier, d in report["tiers"].items():
        extra = f"  (gzip: {mb(d['bytes_gzipped'])})" if "bytes_gzipped" in d else ""
        print(f"  {tier:<22} {d['count']:>4} files  {mb(d['bytes'])}{extra}")
    print()
    print(f"GitHub blockers (> {HARD_LIMIT/1e6:.0f} MB in plain git): {len(blockers)}")
    for p, s in blockers:
        print(f"   {mb(s)}  {p}")
    print()
    print("Documentation layer required by GitHub best practice:")
    for d, ok in report["documentation_present"].items():
        print(f"   [{'OK' if ok else 'MISSING'}] {d}")
    print()
    print("Suggested publication weight (plain git tier only):",
          mb(report["tiers"]["keep_plain_git"]["bytes"]))
    return 0 if not blockers else 1


if __name__ == "__main__":
    sys.exit(main())
