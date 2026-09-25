import pandas as pd

input_file = "data/raw/groundwater/karnataka_man_gw_wl_monthly_data_2021_2025.csv"
output_file = "data/processed/groundwater2025.csv"



df = pd.read_csv(input_file, low_memory=False)
df.columns = df.columns.str.strip()


df["Monitoring Date"] = pd.to_datetime(
    df["Monitoring Date"],
    format="%d-%m-%Y",
    errors="coerce"
)

df["Latitude"] = pd.to_numeric(
    df["Latitude"],
    errors="coerce"
)

df["Longitude"] = pd.to_numeric(
    df["Longitude"],
    errors="coerce"
)

df["Ground Water Level"] = pd.to_numeric(
    df["Ground Water Level"],
    errors="coerce"
)


MIN_LAT = 12.75
MAX_LAT = 13.55

MIN_LON = 77.05
MAX_LON = 78.05


filtered = df[
    (df["Latitude"].between(MIN_LAT, MAX_LAT)) &
    (df["Longitude"].between(MIN_LON, MAX_LON)) &
    (df["Monitoring Date"].dt.year == 2025)
].copy()


required_columns = [
    "Station Code",
    "District",
    "Block",
    "GP Name",
    "Latitude",
    "Longitude",
    "Monitoring Date",
    "Ground Water Level"
]

filtered = filtered[required_columns]

filtered = filtered.dropna(
    subset=[
        "Station Code",
        "Latitude",
        "Longitude",
        "Monitoring Date",
        "Ground Water Level"
    ]
)

filtered = filtered.drop_duplicates()

filtered = filtered.sort_values(
    by=["Station Code", "Monitoring Date"]
).reset_index(drop=True)

filtered.to_csv(
    output_file,
    index=False
)

print("=" * 60)
print("GROUNDWATER DATA CLEANING COMPLETE")
print("=" * 60)

print(f"Original records       : {len(df):,}")
print(f"Filtered records       : {len(filtered):,}")
print(f"Unique stations        : {filtered['Station Code'].nunique():,}")

print(
    f"Date range             : "
    f"{filtered['Monitoring Date'].min().date()} "
    f"to "
    f"{filtered['Monitoring Date'].max().date()}"
)

print(f"Output file            : {output_file}")

print("\nStudy Area")
print("-" * 60)
print(f"Latitude               : {MIN_LAT} → {MAX_LAT}")
print(f"Longitude              : {MIN_LON} → {MAX_LON}")

print("\nRecords by Month")
print("-" * 60)

monthly = (
    filtered["Monitoring Date"]
    .dt.strftime("%Y-%m")
    .value_counts()
    .sort_index()
)

print(monthly)

print("\nMissing Values")
print("-" * 60)
print(filtered.isnull().sum())

print("\nFinal Columns")
print("-" * 60)

for column in filtered.columns:
    print(column)

print("=" * 60)