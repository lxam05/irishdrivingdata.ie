#!/usr/bin/env python3
"""Download latest ROA30 and ROA36 CSV exports from CSO PxStat."""
from __future__ import annotations

import urllib.request
from pathlib import Path

CSO = Path(__file__).resolve().parent / "cso"
SOURCES = {
    "ROA30-full.csv": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/ROA30/CSV/1.0/en",
    "ROA36-full.csv": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/ROA36/CSV/1.0/en",
}


def main() -> None:
    CSO.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        dest = CSO / name
        print(f"Fetching {name} …")
        with urllib.request.urlopen(url, timeout=120) as resp:
            dest.write_bytes(resp.read())
        lines = sum(1 for _ in dest.open(encoding="utf-8-sig"))
        print(f"  wrote {dest} ({lines:,} lines)")


if __name__ == "__main__":
    main()
