#!/usr/bin/env python3
"""Build data/CORPUS_MANIFEST.sha256: one line per published data artefact.

The manifest is the bridge between the repository and the release/Zenodo
assets: a reviewer can download a corpus and verify bit-for-bit that it is
the same object every number in the paper was computed from.

Usage:
    python3 scripts/make_data_manifest.py            # write data/CORPUS_MANIFEST.sha256
    python3 scripts/make_data_manifest.py --check    # verify files on disk against manifest
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "CORPUS_MANIFEST.sha256")
MIN_BYTES = 1_000_000
PATTERNS = ("Evaluacoes/", "Ontologias/", "paper/figures/", "paper/figures_v14/")
SKIP = (".cache_validation", "__pycache__", ".pytest_cache")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked_large() -> list[str]:
    """Prefer git-tracked files; fall back to the working tree if git is absent."""
    try:
        out = subprocess.run(["git", "ls-tree", "-r", "-l", "HEAD"],
                             cwd=REPO, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        out = ""
    paths = []
    for line in out.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        path = parts[1]
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        try:
            size = int(line.split()[3])
        except IndexError:
            continue
        if size >= MIN_BYTES and path.startswith(PATTERNS):
            paths.append(path)
    if paths:
        return sorted(paths)
    # fallback: walk the tree
    paths = []
    for root in PATTERNS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, root)):
            if any(s in dirpath for s in SKIP):
                continue
            for f in filenames:
                p = os.path.join(dirpath, f)
                if os.path.getsize(p) >= MIN_BYTES:
                    paths.append(os.path.relpath(p, REPO))
    return sorted(paths)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify existing manifest")
    ap.add_argument("--skip-missing", action="store_true",
                    help="in CI the corpora are not downloaded: only verify the files present")
    args = ap.parse_args()

    if args.check:
        bad = 0
        missing = 0
        with open(OUT) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                h, path = line.split("\t", 1)
                p = os.path.join(REPO, path)
                if not os.path.isfile(p):
                    missing += 1
                    if not args.skip_missing:
                        print(f"[MISSING] {path}")
                        bad += 1
                elif sha256(p) != h:
                    print(f"[MISMATCH] {path}")
                    bad += 1
        if args.skip_missing and missing:
            print(f"{missing} artefacts not on disk (fetch them with scripts/fetch_data.py)")
        print("OK" if bad == 0 else f"{bad} problems")
        return 0 if bad == 0 else 1

    paths = tracked_large()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    meta = {
        "generated_at": "2026-11-15T12:15:00-03:00",
        "files": len(paths),
        "total_bytes": sum(os.path.getsize(os.path.join(REPO, p)) for p in paths),
    }
    with open(OUT, "w") as fh:
        fh.write("# ETH-WCMK published data manifest — SHA-256 of every artefact that\n")
        fh.write("# the paper's numbers are derived from. Verify with:\n")
        fh.write("#   python3 scripts/make_data_manifest.py --check\n")
        fh.write(f"# {meta['files']} files, {meta['total_bytes']:,} bytes\n")
        for p in paths:
            fh.write(f"{sha256(os.path.join(REPO, p))}\t{p}\n")
    print(f"wrote {OUT}: {meta['files']} files, {meta['total_bytes']:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
