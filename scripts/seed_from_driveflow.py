#!/usr/bin/env python3
"""One-shot seed: build src/data/centres.json from DriveFlow centre-stats + addresses."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DF_DEFAULT = ROOT.parent / "my-frontend-new"

EXTRA_COUNTY = {
    "dun-laoghaire": "Dublin",
    "tallaght": "Dublin",
    "maldron-hotel": "Laois",
}
NAME_OVERRIDES = {
    "dun-laoghaire": "Dún Laoghaire",
}


def main() -> None:
    df = Path(sys.argv[1]) if len(sys.argv) > 1 else DF_DEFAULT
    stats = json.loads((df / "data/centre-stats.json").read_text(encoding="utf-8"))
    addresses = json.loads((df / "data/centre-addresses.json").read_text(encoding="utf-8"))
    addr = addresses.get("centres", addresses)

    centres = []
    for slug, c in stats["centres"].items():
        county = None
        if slug in addr:
            county = addr[slug].get("county")
        if not county:
            county = EXTRA_COUNTY.get(slug)
        if not county and c.get("csoName"):
            m = re.search(r"Co\.\s*([^,]+)$", c["csoName"])
            if m:
                county = m.group(1).strip()
        name = NAME_OVERRIDES.get(slug, c["displayName"])
        centres.append(
            {
                "slug": slug,
                "name": name,
                "county": county or "Unknown",
                "csoName": c["csoName"],
                "passRate": c["passRate"],
                "waitWeeks": c["waitWeeks"],
                "abandoned": c.get("abandoned"),
                "driveflowUrl": f"https://www.driveflow.ie{c['url']}",
                "history": [
                    {
                        "period": stats["period"],
                        "passRate": c["passRate"],
                        "waitWeeks": c["waitWeeks"],
                        "abandoned": c.get("abandoned"),
                    }
                ],
            }
        )

    centres.sort(key=lambda x: x["name"].lower())
    out = {
        "meta": {
            "period": stats["period"],
            "lastUpdated": stats["lastUpdatedDate"],
            "lastUpdatedLabel": stats["lastUpdatedLabel"],
            "citation": "CSO / RSA (ROA30, ROA36), Category B, July 2026",
            "citationLong": stats["citation"],
            "category": "B",
            "national": stats["national"],
            "siteUrl": "https://www.irishdrivingdata.ie",
            "siteName": "Irish Driving Data",
            "author": {
                "name": "Liam O'Connor",
                "url": "https://www.irishdrivingdata.ie/about/",
            },
        },
        "centres": centres,
    }
    path = ROOT / "src/data/centres.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(centres)} centres → {path}")


if __name__ == "__main__":
    main()
