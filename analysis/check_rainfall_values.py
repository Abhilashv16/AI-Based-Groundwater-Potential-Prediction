import h5py
import numpy as np

file_path = "data/raw/rainfall/GPMMRG_MAP_2501010000_H_L3S_MCH_03F.h5"

MIN_LAT = 12.75
MAX_LAT = 13.55
MIN_LON = 77.05
MAX_LON = 78.05

with h5py.File(file_path, "r") as f:

    lat = f["Grid/Latitude"][:]
    lon = f["Grid/Longitude"][:]
    rainfall = f["Grid/hourlyPrecipRateGC"][:]

    mask = (
        (lat >= MIN_LAT) &
        (lat <= MAX_LAT) &
        (lon >= MIN_LON) &
        (lon <= MAX_LON)
    )

    values = rainfall[mask]

    # Remove missing values
    valid = values[values > -9999]

    print("=" * 60)
    print("JANUARY 1, 2025 00:00 RAINFALL CHECK")
    print("=" * 60)

    print(f"Study-area pixels : {len(values)}")
    print(f"Valid pixels      : {len(valid)}")

    if len(valid) > 0:
        print(f"Minimum rainfall  : {valid.min():.4f} mm/hr")
        print(f"Maximum rainfall  : {valid.max():.4f} mm/hr")
        print(f"Mean rainfall     : {valid.mean():.4f} mm/hr")

    print("\nFirst 10 valid values:")
    print(valid[:10])

    print("=" * 60)