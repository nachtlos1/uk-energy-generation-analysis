"""
Step 0: turn NESO's half-hourly generation data into monthly totals.

Downloads (or reads) the NESO 'Historic GB Generation Mix' CSV, validates it, converts
MW to energy (MW x 0.5 h) and sums by month in GWh.

Output: data/gb_generation_monthly_raw.csv

Usage:
    python scripts/aggregate_half_hourly.py                 # downloads the latest file (~30 MB)
    python scripts/aggregate_half_hourly.py path/to/df_fuel_ckan.csv
"""
import sys
from pathlib import Path

import pandas as pd

URL = ("https://api.neso.energy/dataset/88313ae5-94e4-4ddc-a790-593554d8c6b9/resource/"
       "f93d1835-75bc-43e5-84ad-12472b180a98/download/df_fuel_ckan.csv")
FUELS = ["GAS", "COAL", "NUCLEAR", "WIND", "WIND_EMB", "HYDRO", "IMPORTS",
         "BIOMASS", "OTHER", "SOLAR", "STORAGE", "GENERATION"]
OUT = Path(__file__).resolve().parent.parent / "data" / "gb_generation_monthly_raw.csv"


def main() -> None:
    source = sys.argv[1] if len(sys.argv) > 1 else URL
    df = pd.read_csv(source, usecols=["DATETIME", *FUELS, "CARBON_INTENSITY"])
    print(f"Read {len(df):,} half-hourly rows")

    # Validate
    df["DATETIME"] = pd.to_datetime(df["DATETIME"], errors="coerce")
    bad_dates = df["DATETIME"].isna().sum()
    dups = df.duplicated("DATETIME").sum()
    blanks = df[FUELS].isna().sum().sum()
    negatives = (df[FUELS] < 0).sum().sum()
    print(f"Bad dates: {bad_dates}, duplicate timestamps: {dups}, blanks: {blanks}, negatives: {negatives}")
    df = df.dropna(subset=["DATETIME"]).drop_duplicates("DATETIME")

    # MW for half an hour -> MWh, then MWh -> GWh
    energy = df[FUELS] * 0.5 / 1000
    energy.columns = [f"{c}_GWh" for c in FUELS]
    energy["month"] = df["DATETIME"].dt.strftime("%Y-%m")

    monthly = energy.groupby("month").sum().round(1)
    monthly.insert(0, "intervals", df.groupby(df["DATETIME"].dt.strftime("%Y-%m")).size())
    monthly["avg_carbon_intensity_gCO2_per_kWh"] = (
        df.groupby(df["DATETIME"].dt.strftime("%Y-%m"))["CARBON_INTENSITY"].mean().round(1))

    monthly.reset_index().to_csv(OUT, index=False)
    print(f"Saved {len(monthly)} months to {OUT}")


if __name__ == "__main__":
    main()
