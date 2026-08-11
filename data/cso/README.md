# CSO source CSVs for updates

Place exports in `scripts/cso/` (see `scripts/compile_cso.py`), then:

```bash
python3 scripts/compile_cso.py --period YYYY-MM --label "Month YYYY" --date YYYY-MM-DD
npm run build
```

Expected files:

- `ROA30-pass-rates-YYYY-MM.csv`
- `ROA36-waiting-times-YYYY-MM.csv`
- `ROA30-abandoned-YYYY-MM.csv` (optional)

One-time seed from DriveFlow:

```bash
npm run seed
# or: python3 scripts/seed_from_driveflow.py ../my-frontend-new
```
