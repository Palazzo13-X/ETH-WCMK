#!/usr/bin/env python3
"""Download the published corpora and verify them against the manifest.

    python3 scripts/fetch_data.py --release v13.0.0          # from GitHub Releases
    python3 scripts/fetch_data.py --base <url>               # any base URL
    python3 scripts/fetch_data.py --local release_assets     # already-built assets

Each asset is decompressed into its original path under Evaluacoes/ or
Ontologias/ and its SHA-256 is compared with data/CORPUS_MANIFEST.sha256.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER = os.environ.get("ETHWCMK_OWNER", "ETH-WCMK")
REPO_NAME = os.environ.get("ETHWCMK_REPO", "ETH-WCMK")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict[str, str]:
    out = {}
    with open(os.path.join(REPO, "data", "CORPUS_MANIFEST.sha256")) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                h, path = line.split("\t", 1)
                out[path] = h
    return out


def download(url: str, dest: str) -> None:
    print(f"GET {url}")
    with urllib.request.urlopen(url, timeout=120) as resp, open(dest, "wb") as fh:
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            fh.write(chunk)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default="v13.0.0", help="release tag")
    ap.add_argument("--base", help="base URL of the assets (overrides --release)")
    ap.add_argument("--local", help="local directory with the .gz assets")
    ap.add_argument("--out", default=os.path.join(REPO, "data", "downloaded"))
    args = ap.parse_args()

    manifest = load_manifest()
    os.makedirs(args.out, exist_ok=True)

    # source path -> asset filename
    asset_map = {}
    asset_manifest_path = os.path.join(REPO, "release_assets", "ASSET_MANIFEST.json")
    if os.path.isfile(asset_manifest_path):
        with open(asset_manifest_path) as fh:
            for entry in json.load(fh)["assets"]:
                asset_map[entry["source"]] = entry["file"]

    if args.local:
        pairs = [(src, os.path.join(args.local, asset_map.get(src, os.path.basename(src) + ".gz")))
                 for src in manifest]
    else:
        base = args.base or (
            f"https://github.com/{OWNER}/{REPO_NAME}/releases/download/{args.release}"
        )
        pairs = []
        for src in manifest:
            name = asset_map.get(src, os.path.basename(src) + ".gz")
            dest = os.path.join(args.out, name)
            try:
                download(f"{base}/{name}", dest)
                pairs.append((src, dest))
            except Exception as exc:
                print(f"[skip] {base}/{name} ({exc})")

    ok = bad = 0
    for src, asset in pairs:
        if not os.path.isfile(asset):
            print(f"[missing] {src}")
            bad += 1
            continue
        target = os.path.join(args.out, os.path.basename(src))
        with gzip.open(asset, "rb") as g, open(target, "wb") as dst:
            for chunk in iter(lambda: g.read(1 << 20), b""):
                dst.write(chunk)
        digest = sha256_file(target)
        status = "OK" if digest == manifest[src] else "MISMATCH"
        ok += status == "OK"
        bad += status != "OK"
        print(f"{status:9} {src}  {digest[:16]}…")
    print(f"{ok} verified, {bad} mismatched. Files are in {args.out}/")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
