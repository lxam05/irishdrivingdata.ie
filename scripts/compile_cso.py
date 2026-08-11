#!/usr/bin/env python3
"""Compile CSO ROA CSVs into src/data/centres.json (append history).

Usage:
  1. Drop CSVs into scripts/cso/ named:
       ROA30-pass-rates-YYYY-MM.csv
       ROA36-waiting-times-YYYY-MM.csv
       ROA30-abandoned-YYYY-MM.csv (optional)
  2. python3 scripts/compile_cso.py --period 2026-08 --label "August 2026" --date 2026-08-31
  3. npm run export && npm run build

CSV columns expected: Driving Test Centre, VALUE
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSO = Path(__file__).resolve().parent / "cso"
OUT = ROOT / "src" / "data" / "centres.json"

# CSO centre name -> site slug (mirrors DriveFlow mapping)
MANUAL = {
    "Athlone, Co. Westmeath": "athlone",
    "Ballina, Co. Mayo": "ballina",
    "Birr (County Arms Hotel), Co. Offaly": "birr-county-arms-hotel",
    "Buncrana, Co. Donegal": "buncrana",
    "Carlow, Co. Carlow": "carlow",
    "Carlow Talbot Hotel, Co. Carlow": "carlow-talbot-hotel",
    "Carrick On Shannon, Co. Leitrim": "carrick-on-shannon",
    "Castlebar, Co. Mayo": "castlebar",
    "Cavan, Co. Cavan": "cavan",
    "Clifden, Co. Galway": "clifden",
    "Clonmel, Co. Tipperary": "clonmel",
    "Cork (Ballincollig), Co. Cork": "ballincollig",
    "Cork (Wilton), Co. Cork": "wilton",
    "Donegal, Co. Donegal": "donegal",
    "Dun Laoghaire / Deansgrange, Co. Dublin": "dun-laoghaire",
    "Dundalk, Co. Louth": "dundalk",
    "Dungarvan, Co. Waterford": "dungarvan",
    "Ennis, Co. Clare": "ennis",
    "Finglas, Co. Dublin": "finglas",
    "Galway (Carnmore), Co. Galway": "carnmore",
    "Galway (Westside), Co. Galway": "westside",
    "Gorey, Co. Wexford": "gorey",
    "Kilkenny (Govt Buildings), Co. Kilkenny": "kilkenny-government-buildings",
    "Kilkenny (O'Loughlin Gaels), Co. Kilkenny": "kilkenny-oloughlin-gaels",
    "Killarney, Co. Kerry": "killarney",
    "Killester, Co. Dublin": "killester",
    "Kilrush, Co. Clare": "kilrush",
    "Letterkenny, Co. Donegal": "letterkenny",
    "Limerick - Castlemungret, Co. Limerick": "limerick-castlemungret",
    "Limerick - Woodview, Co. Limerick": "woodview",
    "Longford, Co. Longford": "longford",
    "Loughrea, Co. Galway": "loughrea",
    "Mallow (Cork Racecourse Mallow), Co. Cork": "mallow",
    "Monaghan, Co. Monaghan": "monaghan",
    "Mulhuddart, Co. Dublin": "mulhuddart",
    "Mulhuddart Maple House, Co. Dublin": "maple-house",
    "Mullingar, Co. Westmeath": "mullingar",
    "Naas, Co. Kildare": "naas",
    "Navan, Co. Meath": "navan",
    "Nenagh, Co. Tipperary": "nenagh",
    "Newcastle West, Co. Limerick": "newcastle-west",
    "Newcastle West (Longcourt House Hotel), Co. Limerick": "newcastle-west-longcourt-house-hotel",
    "Portlaoise, Co. Laois": "portlaoise",
    "Portlaoise (Maldron Hotel), Co. Laois": "maldron-hotel",
    "Raheny, Co. Dublin": "raheny",
    "Roscommon, Co. Roscommon": "roscommon",
    "Shannon, Co. Clare": "shannon",
    "Skibbereen, Co. Cork": "skibbereen",
    "Sligo, Co. Sligo": "sligo",
    "Tallaght, Co. Dublin": "tallaght",
    "Thurles, Co. Tipperary": "thurles",
    "Tipperary, Co. Tipperary": "tipperary",
    "Tralee, Co. Kerry": "tralee",
    "Tuam, Co. Galway": "tuam",
    "Tullamore, Co. Offaly": "tullamore",
    "Waterford, Co. Waterford": "waterford",
    "Wexford, Co. Wexford": "wexford",
    "Wicklow, Co. Wicklow": "wicklow",
    "Galway (Clybaun Hotel), Co. Galway": "clybaun",
    "Drogheda – Southgate, Co. Louth": "drogheda",
    "Mitchelstown, Co. Cork": "mitchelstown",
}


def parse_num(v: str | None):
    v = (v or "").strip()
    if not v:
        return None
    f = float(v)
    return int(f) if f == int(f) else f


def read_csv(path: Path) -> dict:
    out = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out[row["Driving Test Centre"]] = parse_num(row.get("VALUE"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", required=True, help="YYYY-MM")
    ap.add_argument("--label", required=True, help='e.g. "August 2026"')
    ap.add_argument("--date", required=True, help="YYYY-MM-DD lastUpdated")
    args = ap.parse_args()

    pass_path = CSO / f"ROA30-pass-rates-{args.period}.csv"
    wait_path = CSO / f"ROA36-waiting-times-{args.period}.csv"
    aband_path = CSO / f"ROA30-abandoned-{args.period}.csv"

    if not pass_path.exists() or not wait_path.exists():
        raise SystemExit(f"Missing CSVs under {CSO} for period {args.period}")

    pass_rates = read_csv(pass_path)
    waits = read_csv(wait_path)
    abandoned = read_csv(aband_path) if aband_path.exists() else {}

    by_slug: dict[str, dict] = {}
    national = None
    for name, pr in pass_rates.items():
        if name == "All driving test centres":
            national = {
                "passRate": pr,
                "waitWeeks": waits.get(name),
                "abandoned": abandoned.get(name),
            }
            continue
        slug = MANUAL.get(name)
        if not slug:
            continue
        by_slug[slug] = {
            "csoName": name,
            "passRate": pr,
            "waitWeeks": waits.get(name),
            "abandoned": abandoned.get(name),
        }

    data = json.loads(OUT.read_text(encoding="utf-8"))
    data["meta"]["period"] = args.period
    data["meta"]["lastUpdated"] = args.date
    data["meta"]["lastUpdatedLabel"] = args.label
    data["meta"]["citation"] = (
        f"CSO / RSA (ROA30, ROA36), Category B, {args.label}"
    )
    if national:
        data["meta"]["national"] = {
            "passRate": national["passRate"],
            "waitWeeks": national["waitWeeks"],
            "abandoned": national.get("abandoned"),
        }

    for centre in data["centres"]:
        slug = centre["slug"]
        row = by_slug.get(slug)
        if not row:
            continue
        point = {
            "period": args.period,
            "passRate": row["passRate"],
            "waitWeeks": row["waitWeeks"],
            "abandoned": row.get("abandoned"),
        }
        # Replace same-period entry if re-running
        centre["history"] = [h for h in centre["history"] if h["period"] != args.period]
        centre["history"].append(point)
        centre["history"].sort(key=lambda h: h["period"])
        centre["passRate"] = row["passRate"]
        centre["waitWeeks"] = row["waitWeeks"]
        centre["abandoned"] = row.get("abandoned")
        centre["csoName"] = row["csoName"]

    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {OUT} for {args.period} ({len(by_slug)} mapped centres)")


if __name__ == "__main__":
    main()
