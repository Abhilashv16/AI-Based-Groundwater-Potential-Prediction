
import re
from pathlib import Path
from datetime import datetime

import h5py
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("data/raw/rainfall")
OUTPUT_DIR = Path("data/processed/rainfall")

MIN_LAT = 12.75
MAX_LAT = 13.55

MIN_LON = 77.05
MAX_LON = 78.05

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

FILENAME_PATTERN = re.compile(
    r"GPMMRG_MAP_(\d{10})_H_L3S_MCH_03F\.h5$"
)


# ============================================================
# FIND AND SORT ALL HDF5 FILES
# ============================================================

def get_timestamp(file_path):
    """Extract observation time from the MOSDAC filename."""

    match = FILENAME_PATTERN.fullmatch(file_path.name)

    if not match:
        return None

    try:
        return datetime.strptime(
            match.group(1),
            "%y%m%d%H%M"
        )
    except ValueError:
        return None


def main():

    if not INPUT_DIR.exists():
        raise FileNotFoundError(
            f"Rainfall input directory not found: {INPUT_DIR}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = []

    for file_path in INPUT_DIR.rglob("*.h5"):
        timestamp = get_timestamp(file_path)

        if timestamp is not None and timestamp.year == 2025:
            files.append((timestamp, file_path))

    files.sort(key=lambda item: (item[0], str(item[1])))

    print("=" * 70)
    print("MOSDAC RAINFALL PROCESSING")
    print("=" * 70)
    print(f"Input directory : {INPUT_DIR.resolve()}")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")
    print(f"Files found     : {len(files)}")

    if not files:
        print("No matching 2025 HDF5 files found.")
        return

    # --------------------------------------------------------
    # Rebuild output CSVs from the source files.
    # This prevents duplicate records when rerunning the script.
    # Only existing monthly rainfall.csv files are replaced.
    # --------------------------------------------------------

    for month_name in MONTH_NAMES.values():
        output_file = OUTPUT_DIR / month_name / "rainfall.csv"

        if output_file.exists():
            output_file.unlink()

    # --------------------------------------------------------
    # Cached study-area grid information
    # --------------------------------------------------------

    grid_mask = None
    grid_latitudes = None
    grid_longitudes = None
    expected_grid_shape = None

    successful = 0
    failed = 0
    failure_log = []

    # --------------------------------------------------------
    # Process files one at a time
    # --------------------------------------------------------

    for index, (timestamp, file_path) in enumerate(files, start=1):

        try:
            with h5py.File(file_path, "r") as h5:

                # Check required datasets.
                required = [
                    "Grid/Latitude",
                    "Grid/Longitude",
                    "Grid/hourlyPrecipRateGC",
                ]

                for dataset_name in required:
                    if dataset_name not in h5:
                        raise KeyError(
                            f"Missing dataset: {dataset_name}"
                        )

                # Read the geographic grid once.
                if grid_mask is None:

                    lat = h5["Grid/Latitude"][:]
                    lon = h5["Grid/Longitude"][:]

                    if lat.shape != lon.shape:
                        raise ValueError(
                            "Latitude and longitude shapes differ."
                        )

                    grid_mask = (
                        np.isfinite(lat)
                        & np.isfinite(lon)
                        & (lat >= MIN_LAT)
                        & (lat <= MAX_LAT)
                        & (lon >= MIN_LON)
                        & (lon <= MAX_LON)
                    )

                    grid_latitudes = lat[grid_mask]
                    grid_longitudes = lon[grid_mask]

                    expected_grid_shape = lat.shape

                    print(
                        f"Study-area pixels: "
                        f"{len(grid_latitudes)}"
                    )

                    del lat, lon

                # Read the gauge-adjusted rainfall grid.
                rainfall_dataset = h5[
                    "Grid/hourlyPrecipRateGC"
                ]

                if rainfall_dataset.shape != expected_grid_shape:
                    raise ValueError(
                        "Rainfall grid shape differs from "
                        "the expected geographic grid."
                    )

                rainfall_grid = rainfall_dataset[:]

                # Extract only study-area pixels.
                values = rainfall_grid[grid_mask]

                # Preserve zero rainfall, but mark invalid values
                # as missing rather than treating them as zero.
                valid = np.isfinite(values) & (values > -9999)

                values = values.astype(np.float32, copy=True)
                values[~valid] = np.nan

                del rainfall_grid

            # ------------------------------------------------
            # Create the output table for this observation time.
            # ------------------------------------------------

            month_name = MONTH_NAMES[timestamp.month]

            month_dir = OUTPUT_DIR / month_name
            month_dir.mkdir(parents=True, exist_ok=True)

            output_file = month_dir / "rainfall.csv"

            result = pd.DataFrame({
                "timestamp": timestamp,
                "year": timestamp.year,
                "month": timestamp.month,
                "latitude": grid_latitudes,
                "longitude": grid_longitudes,
                "rainfall_rate_mm_hr": values,
            })

            # Append the extracted pixels for this hour.
            result.to_csv(
                output_file,
                mode="a",
                header=not output_file.exists(),
                index=False,
                na_rep="",
            )

            successful += 1

            if index == 1 or index % 50 == 0 or index == len(files):
                print(
                    f"[{index}/{len(files)}] "
                    f"{timestamp:%Y-%m-%d %H:%M} | "
                    f"{month_name} | "
                    f"Valid pixels: {valid.sum()}/"
                    f"{len(valid)}"
                )

        except Exception as error:

            failed += 1

            failure_log.append(
                f"{file_path} | {timestamp} | {error}"
            )

            print(
                f"[ERROR] {file_path.name}: {error}"
            )

    # --------------------------------------------------------
    # Save failure report
    # --------------------------------------------------------

    failure_file = OUTPUT_DIR / "failed_files.txt"

    if failure_log:
        failure_file.write_text(
            "\n".join(failure_log),
            encoding="utf-8",
        )
    elif failure_file.exists():
        failure_file.unlink()

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)

    print(f"Files discovered  : {len(files)}")
    print(f"Files processed   : {successful}")
    print(f"Files failed      : {failed}")
    print(f"Output directory  : {OUTPUT_DIR.resolve()}")

    print("\nMonthly output counts:")

    for month_name in MONTH_NAMES.values():

        output_file = OUTPUT_DIR / month_name / "rainfall.csv"

        if output_file.exists():
            rows = sum(
                1 for _ in output_file.open(
                    "r", encoding="utf-8"
                )
            ) - 1

            print(f"{month_name:12}: {rows:,} rows")

    if failure_log:
        print(f"\nFailure report: {failure_file.resolve()}")

    print("=" * 70)


if __name__ == "__main__":
    main()
