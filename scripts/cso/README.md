# CSO data files

Full exports from [data.cso.ie](https://data.cso.ie/) PxStat API:

| File | CSO table | Contents |
|------|-----------|----------|
| `ROA30-full.csv` | ROA30 | Pass rates, abandoned tests, delivered, no-shows (all categories) |
| `ROA36-full.csv` | ROA36 | Estimated waiting time to invite (weeks) |

## Refresh data

```bash
npm run fetch-cso      # download latest CSVs from CSO
npm run compile-cso    # rebuild src/data/centres.json
npm run export         # write public/data/latest.{json,csv}
npm run build          # build static site
```

Or in one step: `npm run data && npm run build`

## Source URLs

- ROA30: `https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/ROA30/CSV/1.0/en`
- ROA36: `https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/ROA36/CSV/1.0/en`

Category B filter applied at compile time. Site uses mapped RSA centres only (61 slugs).
