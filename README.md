# Irish Driving Data

Free tracker of Irish RSA Category B driving test **pass rates**, **waiting times**, and **abandoned tests** by centre.

- Site: [www.irishdrivingdata.ie](https://www.irishdrivingdata.ie)
- Maintained by [DriveFlow](https://www.driveflow.ie)
- Written by Liam O'Connor

## Stack

Astro static site. Single source of truth: [`src/data/centres.json`](src/data/centres.json), compiled from CSO PxStat CSV exports.

## Develop

```bash
npm install
npm run dev
```

## Refresh from CSO

Downloads latest ROA30 + ROA36 from [data.cso.ie](https://data.cso.ie/), rebuilds centres.json, exports CSV/JSON:

```bash
npm run data        # fetch + compile + export
npm run build       # build static site
```

## Data coverage

- **ROA30** — Category B pass rates & abandoned tests (Jan 2021 → latest month)
- **ROA36** — estimated wait weeks (Sep 2021 → latest month)
- **61 RSA centres** mapped to DriveFlow route pages

## Embed

```html
<div data-idd-centre="dun-laoghaire"></div>
<script async src="https://www.irishdrivingdata.ie/embed.js"></script>
```

## Routes

| Path | Purpose |
|------|---------|
| `/` | Sortable tracker with latest / compare / all-Julys views |
| `/centres/{slug}/` | Per-centre stats + full monthly history |
| `/about/` | Methodology & author |
| `/data/latest.csv` / `.json` | Downloadable dataset |
# irishdrivingdata.ie
