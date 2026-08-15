#!/usr/bin/env python3
"""Build src/data/centres.json from CSO ROA30 + ROA36 full CSV exports."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSO = Path(__file__).resolve().parent / "cso"
OUT = ROOT / "src" / "data" / "centres.json"
SEED = ROOT / "src" / "data" / "centres.json"

CATEGORY_B = "Category B (Car or light van)"
STAT_PASS = "Driving Test Pass Rate"
STAT_DELIVERED = "Driving Tests Delivered"
STAT_NOSHOW = "Driving Test No-Shows"
STAT_ABANDONED = "Driving Tests Not Conducted / Abandoned"

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
    "Drogheda - Southgate, Co. Louth": "drogheda",
    "Mitchelstown, Co. Cork": "mitchelstown",
}

DISPLAY = {
    "dun-laoghaire": "Dún Laoghaire",
}


def parse_num(v: str | None):
    v = (v or "").strip()
    if not v:
        return None
    f = float(v)
    return int(f) if f == int(f) else round(f, 1)


def tlist_to_period(code: str) -> str:
    # 202607 -> 2026-07
    return f"{code[:4]}-{code[4:6]}"


def load_seed_centres() -> dict[str, dict]:
    if not SEED.exists():
        return {}
    data = json.loads(SEED.read_text(encoding="utf-8"))
    return {c["slug"]: c for c in data.get("centres", [])}


def main() -> None:
    roa30 = CSO / "ROA30-full.csv"
    roa36 = CSO / "ROA36-full.csv"
    if not roa30.exists() or not roa36.exists():
        raise SystemExit("Run scripts/fetch_cso.py first to download ROA30-full.csv and ROA36-full.csv")

    seed = load_seed_centres()
    slugs = sorted(set(MANUAL.values()))

    # period -> slug -> {passRate, abandoned}
    roa30_data: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(dict))
    national: dict[str, dict] = defaultdict(dict)
    period_labels: dict[str, str] = {}

    with roa30.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["Driving Test Categories"] != CATEGORY_B:
                continue
            period = tlist_to_period(row["TLIST(M1)"])
            period_labels[period] = row["Month"]
            centre = row["Driving Test Centre"]
            stat = row["Statistic Label"]
            val = parse_num(row.get("VALUE"))

            if centre == "All driving test centres":
                if stat == STAT_PASS:
                    national[period]["passRate"] = val
                elif stat == STAT_DELIVERED:
                    national[period]["delivered"] = val
                elif stat == STAT_NOSHOW:
                    national[period]["noShow"] = val
                elif stat == STAT_ABANDONED:
                    national[period]["abandoned"] = val
                continue

            slug = MANUAL.get(centre)
            if not slug:
                continue
            if stat == STAT_PASS:
                roa30_data[period][slug]["passRate"] = val
                roa30_data[period][slug]["csoName"] = centre
            elif stat == STAT_DELIVERED:
                roa30_data[period][slug]["delivered"] = val
                roa30_data[period][slug]["csoName"] = centre
            elif stat == STAT_NOSHOW:
                roa30_data[period][slug]["noShow"] = val
                roa30_data[period][slug]["csoName"] = centre
            elif stat == STAT_ABANDONED:
                roa30_data[period][slug]["abandoned"] = val
                roa30_data[period][slug]["csoName"] = centre

    # ROA36 wait times (no category dimension)
    with roa36.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            period = tlist_to_period(row["TLIST(M1)"])
            period_labels.setdefault(period, row["Month"])
            centre = row["Driving Test Centre"]
            val = parse_num(row.get("VALUE"))
            if centre == "All driving test centres":
                national[period]["waitWeeks"] = val
                continue
            slug = MANUAL.get(centre)
            if not slug:
                continue
            roa30_data[period][slug]["waitWeeks"] = val
            roa30_data[period][slug]["csoName"] = centre

    periods = sorted(set(roa30_data.keys()) | set(national.keys()))
    latest = periods[-1]
    latest_label = period_labels.get(latest, latest)

    centres_out = []
    for slug in slugs:
        seed_row = seed.get(slug, {})
        history = []
        for period in periods:
            row = roa30_data.get(period, {}).get(slug, {})
            point = {
                "period": period,
                "passRate": row.get("passRate"),
                "waitWeeks": row.get("waitWeeks"),
                "delivered": row.get("delivered"),
                "noShow": row.get("noShow"),
                "abandoned": row.get("abandoned"),
            }
            if any(v is not None for k, v in point.items() if k != "period"):
                history.append(point)

        latest_row = roa30_data.get(latest, {}).get(slug, {})
        cso_name = latest_row.get("csoName") or seed_row.get("csoName")
        centres_out.append(
            {
                "slug": slug,
                "name": seed_row.get("name") or DISPLAY.get(slug, slug.replace("-", " ").title()),
                "county": seed_row.get("county", "Unknown"),
                "csoName": cso_name,
                "passRate": latest_row.get("passRate"),
                "waitWeeks": latest_row.get("waitWeeks"),
                "delivered": latest_row.get("delivered"),
                "noShow": latest_row.get("noShow"),
                "abandoned": latest_row.get("abandoned"),
                "driveflowUrl": seed_row.get("driveflowUrl")
                or f"https://www.driveflow.ie/{slug}-routes.html",
                "history": history,
            }
        )

    centres_out.sort(key=lambda c: c["name"].lower())

    def period_meta(period: str) -> dict:
        row = national.get(period, {})
        metrics = []
        if row.get("passRate") is not None:
            metrics.append("passRate")
        if row.get("waitWeeks") is not None:
            metrics.append("waitWeeks")
        if row.get("delivered") is not None:
            metrics.append("delivered")
        if row.get("noShow") is not None:
            metrics.append("noShow")
        if row.get("abandoned") is not None:
            metrics.append("abandoned")
        return {
            "period": period,
            "label": period_labels.get(period, period),
            "metrics": metrics,
        }

    july_periods = [p for p in periods if p.endswith("-07")]

    national_history = []
    for period in periods:
        row = national.get(period, {})
        national_history.append(
            {
                "period": period,
                "passRate": row.get("passRate"),
                "waitWeeks": row.get("waitWeeks"),
                "delivered": row.get("delivered"),
                "noShow": row.get("noShow"),
                "abandoned": row.get("abandoned"),
            }
        )

    latest_nat = national.get(latest, {})
    today = date.today().isoformat()

    payload = {
        "meta": {
            "period": latest,
            "lastUpdated": today,
            "lastUpdatedLabel": latest_label,
            "citation": f"CSO / RSA (ROA30, ROA36), Category B, {latest_label}",
            "citationLong": (
                f"CSO PxStat ROA30 (pass rates, abandoned tests) and ROA36 (waiting times), "
                f"Category B, {period_labels.get(periods[0], periods[0])}–{latest_label}. "
                f"Source: data.cso.ie"
            ),
            "category": "B",
            "national": {
                "passRate": latest_nat.get("passRate"),
                "waitWeeks": latest_nat.get("waitWeeks"),
                "delivered": latest_nat.get("delivered"),
                "noShow": latest_nat.get("noShow"),
                "abandoned": latest_nat.get("abandoned"),
            },
            "siteUrl": "https://www.irishdrivingdata.ie",
            "siteName": "Irish Driving Data",
            "author": {
                "name": "Liam O'Connor",
                "url": "https://www.irishdrivingdata.ie/about/",
            },
            "periods": [period_meta(p) for p in periods],
            "julyPeriods": [period_meta(p) for p in july_periods],
            "nationalHistory": national_history,
            "dataSource": {
                "publisher": "Central Statistics Office (CSO)",
                "url": "https://data.cso.ie/",
                "tables": ["ROA30", "ROA36"],
                "downloaded": today,
            },
        },
        "centres": centres_out,
    }

    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"  periods: {len(periods)} ({periods[0]} → {latest})")
    print(f"  july periods: {len(july_periods)}")
    print(f"  centres: {len(centres_out)}")
    print(f"  latest national: pass={latest_nat.get('passRate')}% wait={latest_nat.get('waitWeeks')}w delivered={latest_nat.get('delivered')} noShow={latest_nat.get('noShow')} abandoned={latest_nat.get('abandoned')}")


if __name__ == "__main__":
    main()
