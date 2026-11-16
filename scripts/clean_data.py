"""
Clean the monthly GB generation data and build the annual summary.

Input : data/gb_generation_monthly_raw.csv   (monthly totals aggregated from NESO half-hourly data)
Output: data/gb_generation_monthly_clean.csv
        data/gb_generation_annual.csv
        data/energy.db                       (SQLite database for the SQL analysis)

Run from the project folder:  python scripts/clean_data.py
"""
import calendar
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

FUELS = ["GAS", "COAL", "NUCLEAR", "WIND", "WIND_EMB", "HYDRO", "IMPORTS",
         "BIOMASS", "OTHER", "SOLAR", "STORAGE"]


def season(month: int) -> str:
    return {12: "Winter", 1: "Winter", 2: "Winter",
            3: "Spring", 4: "Spring", 5: "Spring",
            6: "Summer", 7: "Summer", 8: "Summer"}.get(month, "Autumn")


def main() -> None:
    raw = pd.read_csv(DATA / "gb_generation_monthly_raw.csv")
    log = [f"Loaded {len(raw)} monthly rows ({raw['month'].min()} to {raw['month'].max()})."]

    # 1. Rename columns to clear, consistent names
    df = raw.rename(columns={f"{f}_GWh": f.lower() + "_gwh" for f in FUELS + ["GENERATION"]})
    df = df.rename(columns={"GENERATION_GWh": "total_gwh",
                            "generation_gwh": "total_gwh",
                            "avg_carbon_intensity_gCO2_per_kWh": "carbon_intensity_g_per_kwh"})

    # 2. Split the month into year / month number, and add a season
    df["year"] = df["month"].str[:4].astype(int)
    df["month_num"] = df["month"].str[5:7].astype(int)
    df["season"] = df["month_num"].map(season)

    # 3. Completeness check: a full month has 48 half-hour intervals per day
    df["expected_intervals"] = [calendar.monthrange(y, m)[1] * 48
                                for y, m in zip(df["year"], df["month_num"])]
    df["complete"] = df["intervals"] == df["expected_intervals"]
    incomplete = df.loc[~df["complete"], "month"].tolist()
    log.append(f"Incomplete months removed: {incomplete or 'none'}.")
    df = df[df["complete"]].copy()

    # 4. Sanity checks
    assert df["month"].is_unique, "duplicate months"
    assert (df[[c for c in df.columns if c.endswith('_gwh')]] >= 0).all().all(), "negative values"
    parts = df[[f.lower() + "_gwh" for f in FUELS]].sum(axis=1)
    max_gap = (parts - df["total_gwh"]).abs().max()
    assert max_gap < 1, f"fuel totals do not add up to total generation (gap {max_gap})"
    log.append(f"Checked: no duplicate months, no negative values, fuels sum to total (max gap {max_gap:.2f} GWh).")

    # 5. Derived columns
    df["wind_total_gwh"] = df["wind_gwh"] + df["wind_emb_gwh"]
    for col in ["nuclear", "gas", "coal", "wind_total", "solar"]:
        df[f"{col}_share"] = (df[f"{col}_gwh"] / df["total_gwh"]).round(4)

    cols = (["month", "year", "month_num", "season", "intervals"]
            + [f.lower() + "_gwh" for f in FUELS]
            + ["wind_total_gwh", "total_gwh", "carbon_intensity_g_per_kwh",
               "nuclear_share", "gas_share", "coal_share", "wind_total_share", "solar_share"])
    df = df[cols]
    df.to_csv(DATA / "gb_generation_monthly_clean.csv", index=False)
    log.append(f"Saved {len(df)} clean monthly rows.")

    # 6. Annual summary: full calendar years only
    full_years = df.groupby("year")["month"].count()
    full_years = full_years[full_years == 12].index
    annual = (df[df["year"].isin(full_years)]
              .groupby("year")[[c for c in cols if c.endswith("_gwh")]].sum().round(1))
    for col in ["nuclear", "gas", "coal", "wind_total", "solar"]:
        annual[f"{col}_share"] = (annual[f"{col}_gwh"] / annual["total_gwh"]).round(4)
    annual.reset_index().to_csv(DATA / "gb_generation_annual.csv", index=False)
    log.append(f"Saved annual summary for {len(annual)} full years ({annual.index.min()}-{annual.index.max()}).")

    # 7. Load into SQLite for the SQL analysis
    db = DATA / "energy.db"
    db.unlink(missing_ok=True)
    with sqlite3.connect(db) as con:
        df.to_sql("monthly_generation", con, index=False)
    log.append("Loaded table monthly_generation into data/energy.db.")

    print("\n".join(log))


if __name__ == "__main__":
    main()
