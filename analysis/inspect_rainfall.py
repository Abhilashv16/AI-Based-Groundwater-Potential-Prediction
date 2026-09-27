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

    print("=" * 70)
    print("RAINFALL GRID INFORMATION")
    print("=" * 70)

    print("\nLatitude:")
    print(f"  Minimum : {np.nanmin(lat)}")
    print(f"  Maximum : {np.nanmax(lat)}")
    print(f"  Shape   : {lat.shape}")

    print("\nLongitude:")
    print(f"  Minimum : {np.nanmin(lon)}")
    print(f"  Maximum : {np.nanmax(lon)}")
    print(f"  Shape   : {lon.shape}")

    # Find pixels inside our project area
    mask = (
        (lat >= MIN_LAT) &
        (lat <= MAX_LAT) &
        (lon >= MIN_LON) &
        (lon <= MAX_LON)
    )

    indices = np.where(mask)

    print("\nPROJECT AREA")
    print("-" * 70)

    print(f"Latitude range  : {MIN_LAT} → {MAX_LAT}")
    print(f"Longitude range : {MIN_LON} → {MAX_LON}")

    print(f"\nMatching pixels: {len(indices[0])}")

    if len(indices[0]) > 0:
        print("\nActual grid coverage:")
        print(f"Latitude  : {lat[mask].min()} → {lat[mask].max()}")
        print(f"Longitude : {lon[mask].min()} → {lon[mask].max()}")

    print("\n" + "=" * 70)