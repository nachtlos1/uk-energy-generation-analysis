"""
Build the Excel workbook: analysis/uk_energy_analysis.xlsx
Every summary number is a live formula (SUMIFS / AVERAGEIFS / COUNTIFS) that reads the Monthly_Data sheet.
Run after clean_data.py:  python scripts/build_workbook.py
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

monthly = pd.read_csv(ROOT / "data" / "gb_generation_monthly_clean.csv")
years = sorted(monthly.groupby("year").filter(lambda g: len(g) == 12)["year"].unique())

FONT = "Arial"
HEAD_FILL = PatternFill("solid", start_color="3B2A5C")
HEAD_FONT = Font(name=FONT, bold=True, color="FFFFFF")
INPUT_FONT = Font(name=FONT, color="0000FF")
BODY = Font(name=FONT)
BOLD = Font(name=FONT, bold=True)
TITLE = Font(name=FONT, bold=True, size=14)
NOTE = Font(name=FONT, italic=True, color="666666", size=9)
THIN = Border(bottom=Side(style="thin", color="DDDDDD"))

wb = Workbook()


def header(ws, row, labels):
    for i, label in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=label)
        c.font, c.fill = HEAD_FONT, HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 32


def widths(ws, w):
    for i, width in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(i)].width = width


def style_chart(ch):
    ch.roundedCorners = False
    ch.legend.overlay = False
    ch.legend.position = "b"
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    ch.height, ch.width = 9, 18


# ---------------------------------------------------------------- About
ws = wb.active
ws.title = "About"
rows = [
    ("UK (GB) Electricity Generation Analysis, 2009-2025", TITLE),
    ("Author: ArcSkt1", BODY),
    ("", BODY),
    ("Questions", BOLD),
    ("1. How much electricity has nuclear generated each year, and what share of the total?", BODY),
    ("2. How has the generation mix changed as coal closed and wind and solar grew?", BODY),
    ("3. How does nuclear compare with gas and wind over time?", BODY),
    ("4. Is nuclear's share seasonal?", BODY),
    ("", BODY),
    ("Sheets", BOLD),
    ("Monthly_Data: cleaned monthly totals (GWh), one row per complete month.", BODY),
    ("Annual_Summary: yearly totals and shares, calculated with SUMIFS formulas.", BODY),
    ("Seasonality: average nuclear output and share by calendar month (AVERAGEIFS). Change the blue years to re-run.", BODY),
    ("Data_Checks: completeness and quality checks (COUNTIFS).", BODY),
    ("Cleaning_Log: every cleaning step and why.", BODY),
    ("", BODY),
    ("Source", BOLD),
    ("NESO (National Energy System Operator) Data Portal, 'Historic GB Generation Mix', half-hourly data from 1 Jan 2009.", BODY),
    ("https://www.neso.energy/data-portal/historic-generation-mix", BODY),
    ("Half-hourly MW values were converted to energy (MW x 0.5 h = MWh) and summed per month, then shown in GWh.", BODY),
    ("Covers Great Britain (England, Scotland, Wales) transmission-level generation plus embedded wind and solar estimates.", BODY),
    ("", BODY),
    ("Colour key: blue text = input you can change; black = formula.", NOTE),
]
for i, (text, font) in enumerate(rows, 1):
    ws.cell(row=i, column=1, value=text).font = font
ws.column_dimensions["A"].width = 120

# ---------------------------------------------------------------- Monthly_Data
md = wb.create_sheet("Monthly_Data")
cols = ["month", "year", "month_num", "season", "gas_gwh", "coal_gwh", "nuclear_gwh", "wind_gwh",
        "wind_emb_gwh", "solar_gwh", "hydro_gwh", "biomass_gwh", "imports_gwh", "storage_gwh",
        "other_gwh", "total_gwh", "carbon_intensity_g_per_kwh"]
labels = ["Month", "Year", "Month #", "Season", "Gas (GWh)", "Coal (GWh)", "Nuclear (GWh)",
          "Wind - transmission (GWh)", "Wind - embedded (GWh)", "Solar (GWh)", "Hydro (GWh)",
          "Biomass (GWh)", "Imports (GWh)", "Storage (GWh)", "Other (GWh)", "Total (GWh)",
          "Carbon intensity (gCO2/kWh)", "Wind total (GWh)", "Nuclear share"]
header(md, 1, labels)
for r, rec in enumerate(monthly[cols].itertuples(index=False), 2):
    for c, v in enumerate(rec, 1):
        cell = md.cell(row=r, column=c, value=v)
        cell.font = BODY
        if 5 <= c <= 16:
            cell.number_format = "#,##0.0"
        elif c == 17:
            cell.number_format = "0.0"
    md.cell(row=r, column=18, value=f"=H{r}+I{r}").number_format = "#,##0.0"
    md.cell(row=r, column=19, value=f"=IF(P{r}=0,0,G{r}/P{r})").number_format = "0.0%"
    md.cell(row=r, column=18).font = md.cell(row=r, column=19).font = BODY
last = len(monthly) + 1
md.freeze_panes = "B2"
md.auto_filter.ref = f"A1:S{last}"
widths(md, [10, 7, 8, 9] + [12] * 15)

MD = "Monthly_Data"
rng = lambda col: f"{MD}!${col}$2:${col}${last}"  # noqa: E731

# ---------------------------------------------------------------- Annual_Summary
an = wb.create_sheet("Annual_Summary")
an_labels = ["Year", "Gas (TWh)", "Coal (TWh)", "Nuclear (TWh)", "Wind (TWh)", "Solar (TWh)",
             "Imports (TWh)", "Other (TWh)", "Total (TWh)", "Nuclear %", "Gas %", "Coal %",
             "Wind %", "Solar %", "Avg carbon intensity (gCO2/kWh)", "Months of data"]
header(an, 1, an_labels)
src = {"B": "E", "C": "F", "D": "G", "E": "R", "F": "J", "G": "M", "I": "P"}
for i, y in enumerate(years, 2):
    an.cell(row=i, column=1, value=str(y)).font = BODY
    for col, mcol in src.items():
        an[f"{col}{i}"] = f"=SUMIFS({rng(mcol)},{rng('B')},VALUE($A{i}))/1000"
    an[f"H{i}"] = f"=I{i}-SUM(B{i}:G{i})"
    for col, num in zip("JKLMN", "DBCEF"):
        an[f"{col}{i}"] = f"=IF($I{i}=0,0,{num}{i}/$I{i})"
    an[f"O{i}"] = f"=AVERAGEIFS({rng('Q')},{rng('B')},VALUE($A{i}))"
    an[f"P{i}"] = f"=COUNTIFS({rng('B')},VALUE($A{i}))"
    for c in range(2, 17):
        cell = an.cell(row=i, column=c)
        cell.font = BODY
        cell.number_format = "0.0%" if 10 <= c <= 14 else ("0" if c >= 15 else "#,##0.0")
        cell.border = THIN
end = len(years) + 1
an.cell(row=end + 2, column=1,
        value="All values are formulas reading Monthly_Data. Other = hydro + biomass + storage + other. "
              "Carbon intensity is an average of monthly averages.").font = NOTE
an.freeze_panes = "B2"
widths(an, [8] + [11] * 14 + [15, 9])

c1 = LineChart()
c1.title = "Nuclear share of GB generation"
c1.y_axis.title, c1.x_axis.title = "Share", "Year"
c1.y_axis.number_format = "0%"
c1.add_data(Reference(an, min_col=10, min_row=1, max_row=end), titles_from_data=True)
c1.set_categories(Reference(an, min_col=1, min_row=2, max_row=end))
style_chart(c1)
c1.title.overlay = False
an.add_chart(c1, "R2")

c2 = LineChart()
c2.title = "Nuclear vs gas vs wind (TWh)"
c2.y_axis.title = "TWh"
for col in (2, 4, 5):
    c2.add_data(Reference(an, min_col=col, min_row=1, max_row=end), titles_from_data=True)
c2.set_categories(Reference(an, min_col=1, min_row=2, max_row=end))
style_chart(c2)
c2.title.overlay = False
an.add_chart(c2, "R21")

c3 = BarChart()
c3.type, c3.grouping, c3.overlap = "col", "stacked", 100
c3.title = "Generation mix by year (TWh)"
c3.add_data(Reference(an, min_col=2, max_col=8, min_row=1, max_row=end), titles_from_data=True)
c3.set_categories(Reference(an, min_col=1, min_row=2, max_row=end))
style_chart(c3)
c3.title.overlay = False
an.add_chart(c3, "R40")

# ---------------------------------------------------------------- Seasonality
se = wb.create_sheet("Seasonality")
se["A1"] = "Nuclear by calendar month"
se["A1"].font = TITLE
se["A3"], se["A4"] = "From year", "To year"
se["B3"], se["B4"] = 2021, 2025
for c in ("A3", "A4"):
    se[c].font = BOLD
for c in ("B3", "B4"):
    se[c].font = INPUT_FONT
se["C3"] = "<- change these blue years to re-run the analysis"
se["C3"].font = NOTE
header(se, 6, ["Month #", "Month", "Avg nuclear (GWh)", "Avg total (GWh)", "Avg nuclear share"])
names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
crit = f"{rng('B')},\">=\"&$B$3,{rng('B')},\"<=\"&$B$4"
for m in range(1, 13):
    r = 6 + m
    se.cell(row=r, column=1, value=m).font = BODY
    se.cell(row=r, column=2, value=names[m - 1]).font = BODY
    se[f"C{r}"] = f"=AVERAGEIFS({rng('G')},{rng('C')},$A{r},{crit})"
    se[f"D{r}"] = f"=AVERAGEIFS({rng('P')},{rng('C')},$A{r},{crit})"
    se[f"E{r}"] = f"=AVERAGEIFS({rng('S')},{rng('C')},$A{r},{crit})"
    for col, fmt in (("C", "#,##0"), ("D", "#,##0"), ("E", "0.0%")):
        se[f"{col}{r}"].number_format = fmt
        se[f"{col}{r}"].font = BODY
se["A20"] = "Finding: nuclear's share peaks in late spring and summer. Output stays fairly steady, but total demand is lower, so nuclear covers more of it."
se["A20"].font = NOTE
widths(se, [11, 9, 18, 16, 18])
c4 = BarChart()
c4.title = "Average nuclear share by month"
c4.y_axis.number_format = "0%"
c4.add_data(Reference(se, min_col=5, min_row=6, max_row=18), titles_from_data=True)
c4.set_categories(Reference(se, min_col=2, min_row=7, max_row=18))
style_chart(c4)
c4.title.overlay = False
se.add_chart(c4, "G3")

# ---------------------------------------------------------------- Data_Checks
dc = wb.create_sheet("Data_Checks")
dc["A1"] = "Data quality checks"
dc["A1"].font = TITLE
checks = [
    ("Months in clean data", f"=COUNTA({rng('A')})", "0"),
    ("Duplicate months (should be 0)", f"=SUMPRODUCT((COUNTIF({rng('A')},{rng('A')})>1)*1)", "0"),
    ("Negative values (should be 0)", f"=COUNTIF({MD}!$E$2:$P${last},\"<0\")", "0"),
    ("Blank cells in numeric columns (should be 0)", f"=COUNTBLANK({MD}!$E$2:$Q${last})", "0"),
    ("Total generation, all months (TWh)", f"=SUM({rng('P')})/1000", "#,##0.0"),
    ("Sum of individual sources, all months (TWh)", f"=SUM({MD}!$E$2:$O${last})/1000", "#,##0.0"),
    ("Difference (should be ~0)", "=B8-B9", "0.000"),
    ("Full years in Annual_Summary", "=COUNTIFS(Annual_Summary!$P$2:$P$40,12)", "0"),
]
for i, (label, f, fmt) in enumerate(checks, 4):
    dc.cell(row=i, column=1, value=label).font = BODY
    c = dc.cell(row=i, column=2, value=f)
    c.font, c.number_format = BOLD, fmt
widths(dc, [48, 16])

# ---------------------------------------------------------------- Cleaning_Log
cl = wb.create_sheet("Cleaning_Log")
header(cl, 1, ["Step", "What I did", "Why"])
steps = [
    ("Download", "Downloaded NESO 'Historic GB Generation Mix' CSV (312,816 half-hourly rows, Jan 2009 - Nov 2026).", "Official system operator data, free and open."),
    ("Validate raw", "Checked for duplicate timestamps, blank values, non-numeric values and negatives. Found none.", "Make sure the data can be trusted before aggregating."),
    ("Convert units", "Converted each half-hour from MW (power) to MWh (energy): MW x 0.5 hours.", "MW is a rate. To total generation over time you need energy (MWh)."),
    ("Aggregate", "Summed half-hours into monthly totals and converted to GWh. Averaged carbon intensity per month.", "214 monthly rows are easier to analyse than 312,816 half-hours."),
    ("Rename", "Renamed columns to clear names with units, e.g. NUCLEAR -> nuclear_gwh.", "Readability; units in every column name."),
    ("Add fields", "Split month into year and month number, added season.", "Needed for yearly and seasonal analysis."),
    ("Completeness", "Compared intervals per month with expected (days x 48). Removed Nov 2026 (only 4 of 30 days).", "A partial month would distort averages and totals."),
    ("Reconcile", "Checked the sum of all sources equals NESO's total for every month (max gap 0.2 GWh).", "Confirms no source is missing or double-counted."),
    ("Combine wind", "Wind total = transmission-connected wind + embedded (local) wind.", "Embedded wind is real generation; leaving it out undercounts wind."),
    ("Full years only", "Annual summary uses only years with all 12 months (2009-2025).", "Fair year-on-year comparison."),
]
for r, row in enumerate(steps, 2):
    for c, v in enumerate(row, 1):
        cell = cl.cell(row=r, column=c, value=v)
        cell.font = BODY
        cell.alignment = Alignment(wrap_text=True, vertical="top")
widths(cl, [16, 80, 60])

wb.save(OUT / "uk_energy_analysis.xlsx")
print("Saved", OUT / "uk_energy_analysis.xlsx")
