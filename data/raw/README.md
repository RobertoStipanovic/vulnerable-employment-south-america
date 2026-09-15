# Raw data

This folder is intentionally empty in the repository.

`WDICSV.csv` is the full World Development Indicators release from the World Bank
(~190 MB, above GitHub's 100 MB per-file limit), so it is git-ignored.

Download it with:

```bash
python scripts/download_wdi.py
```

You do **not** need it to run the notebook: the South-America subset used by the
analysis is committed at `data/processed/WDI_SouthAmerica_Filtered.csv`.
