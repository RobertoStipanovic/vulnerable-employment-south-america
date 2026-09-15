"""Download the full World Development Indicators release into data/raw/.

The bulk CSV is ~190 MB unzipped, which is why it is git-ignored. Running this
script is optional: the notebook reads the committed South-America subset in
data/processed/ by default.

Usage:
    python scripts/download_wdi.py
"""

import io
import sys
import zipfile
from pathlib import Path

import requests

WDI_ZIP_URL = "https://databank.worldbank.org/data/download/WDI_CSV.zip"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
TARGET = RAW_DIR / "WDICSV.csv"

SOUTH_AMERICA = [
    "Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador",
    "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay",
]


def download() -> Path:
    if TARGET.exists():
        print(f"{TARGET} already exists, nothing to do.")
        return TARGET

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {WDI_ZIP_URL} (~60 MB zipped)...")

    response = requests.get(WDI_ZIP_URL, timeout=600)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = [n for n in archive.namelist() if n.upper().endswith("WDICSV.CSV")]
        if not names:
            sys.exit(f"WDICSV.csv not found in the archive. Contents: {archive.namelist()}")
        with archive.open(names[0]) as source, open(TARGET, "wb") as out:
            while chunk := source.read(1 << 20):
                out.write(chunk)

    size_mb = TARGET.stat().st_size / 1e6
    print(f"Wrote {TARGET} ({size_mb:.0f} MB)")
    return TARGET


def rebuild_subset(path: Path) -> None:
    """Regenerate data/processed/WDI_SouthAmerica_Filtered.csv from the full file."""
    import pandas as pd

    out = path.parent.parent / "processed" / "WDI_SouthAmerica_Filtered.csv"
    df = pd.read_csv(path)
    subset = df[df["Country Name"].isin(SOUTH_AMERICA)]
    out.parent.mkdir(parents=True, exist_ok=True)
    subset.to_csv(out, index=False)
    print(f"Wrote {out} ({len(subset):,} rows)")


if __name__ == "__main__":
    csv_path = download()
    if "--rebuild-subset" in sys.argv:
        rebuild_subset(csv_path)
