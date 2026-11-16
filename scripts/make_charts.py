"""
Create the PNG charts used in the README.
Run after clean_data.py:  python scripts/make_charts.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)

annual = pd.read_csv(ROOT / "data" / "gb_generation_annual.csv")
monthly = pd.read_csv(ROOT / "data" / "gb_generation_monthly_clean.csv")

COLORS = {"Gas": "#E8833A", "Coal": "#4D4D4D", "Nuclear": "#7B4FB8", "Wind": "#2E9BD6",
          "Solar": "#F2C230", "Imports": "#9AA5B1", "Other (hydro, biomass, storage, other)": "#5BAE6A"}
SOURCE = "Source: NESO Historic GB Generation Mix (half-hourly data, aggregated). Full years 2009-2025."

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})


def finish(fig, ax, title, name):
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold")
    fig.text(0.01, 0.01, SOURCE, fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / name, dpi=150)
    plt.close(fig)


# 1. Nuclear share of generation per year
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(annual["year"], annual["nuclear_share"] * 100, color=COLORS["Nuclear"], lw=2.5, marker="o")
ax.set_ylabel("Share of total generation (%)")
ax.set_ylim(0, 25)
ax.grid(axis="y", alpha=0.3)
for y in (2016, 2025):
    v = annual.loc[annual["year"] == y, "nuclear_share"].item() * 100
    ax.annotate(f"{v:.1f}%", (y, v), textcoords="offset points", xytext=(0, 8), ha="center")
finish(fig, ax, "Nuclear's share of GB electricity has fallen from ~22% to ~12%", "01_nuclear_share.png")

# 2. Generation mix by year (stacked bar, TWh)
annual = annual.set_index("year", drop=False)
mix = pd.DataFrame({
    "Gas": annual["gas_gwh"], "Coal": annual["coal_gwh"], "Nuclear": annual["nuclear_gwh"],
    "Wind": annual["wind_total_gwh"], "Solar": annual["solar_gwh"], "Imports": annual["imports_gwh"],
    "Other (hydro, biomass, storage, other)": annual[["hydro_gwh", "biomass_gwh", "storage_gwh", "other_gwh"]].sum(axis=1),
}, index=annual["year"]) / 1000
fig, ax = plt.subplots(figsize=(11, 5.5))
bottom = pd.Series(0.0, index=mix.index)
for col in mix.columns:
    ax.bar(mix.index, mix[col], bottom=bottom, color=COLORS[col], label=col, width=0.75)
    bottom += mix[col]
ax.set_ylabel("Generation (TWh)")
ax.set_xticks(mix.index[::2])
ax.legend(ncol=4, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.08), frameon=False)
ax.grid(axis="y", alpha=0.3)
finish(fig, ax, "GB generation mix: coal gone, wind up, nuclear down", "02_generation_mix.png")

# 3. Nuclear vs gas vs wind (TWh)
fig, ax = plt.subplots(figsize=(10, 5))
for col, key in [("nuclear_gwh", "Nuclear"), ("gas_gwh", "Gas"), ("wind_total_gwh", "Wind")]:
    ax.plot(annual["year"], annual[col] / 1000, color=COLORS[key], lw=2.5, label=key)
ax.axvline(2019, color="#999999", ls="--", lw=1)
ax.text(2019.15, 140, "2019: wind overtakes nuclear", fontsize=9, color="#555555")
ax.set_ylabel("Generation (TWh)")
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.3)
finish(fig, ax, "Nuclear vs gas vs wind, 2009-2025", "03_nuclear_gas_wind.png")

# 4. Seasonality: average nuclear share by calendar month, 2021-2025
recent = monthly[monthly["year"].between(2021, 2025)]
by_month = recent.groupby("month_num")["nuclear_share"].mean() * 100
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(by_month.index, by_month.values, color=COLORS["Nuclear"])
ax.set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
ax.set_ylabel("Average nuclear share (%)")
ax.grid(axis="y", alpha=0.3)
finish(fig, ax, "Nuclear share by month (2021-2025 average): higher when demand is low", "04_seasonality.png")

print("Charts saved to", OUT)
