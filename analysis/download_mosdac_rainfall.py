import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import async_playwright


YEAR = 2025

BASE_URL = (
    "https://www.mosdac.gov.in/opendata/"
    "GSMaP_SAC_RAIN/2025/"
)

OUTPUT_DIR = Path("data/raw/rainfall")

BROWSER_PROFILE = Path(".mosdac_browser")

MAX_RETRIES = 3


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


def generate_filenames():
    """
    Generate every hourly GSMaP filename for 2025.
    """

    start = datetime(YEAR, 1, 1, 0, 0)
    end = datetime(YEAR + 1, 1, 1, 0, 0)

    current = start

    while current < end:

        filename = (
            f"GPMMRG_MAP_"
            f"{current.strftime('%y%m%d%H%M')}"
            f"_H_L3S_MCH_03F.h5"
        )

        yield current, filename

        current += timedelta(hours=1)

async def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("MOSDAC GSMaP 2025 DOWNLOADER")
    print("=" * 70)

    print()
    print("Output directory:")
    print(OUTPUT_DIR.resolve())

    print()
    print("Browser profile:")
    print(BROWSER_PROFILE.resolve())

    print()
    print("IMPORTANT:")
    print("A Chromium window will open.")
    print("If MOSDAC asks you to log in, log in manually.")
    print("After login, return to this terminal.")
    print()

    async with async_playwright() as p:

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE),
            headless=False,
            accept_downloads=True,
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening MOSDAC...")

        await page.goto(
            BASE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(3000)

        print()
        print("Current page:")
        print(page.url)

        if "auth" in page.url.lower() or "login" in page.url.lower():

            print()
            print("=" * 70)
            print("MOSDAC LOGIN REQUIRED")
            print("=" * 70)
            print()
            print("Log in to MOSDAC in the browser window.")
            print("After login, return here and press ENTER.")
            input()

            await page.goto(
                BASE_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            await page.wait_for_timeout(3000)

        print()
        print("Authenticated page:")
        print(page.url)

        success = 0
        skipped = 0
        failed = 0

        failures = []

        for current, filename in generate_filenames():

            month_name = MONTH_NAMES[current.month]

            month_dir = OUTPUT_DIR / month_name
            month_dir.mkdir(parents=True, exist_ok=True)

            output_file = month_dir / filename

            if output_file.exists() and output_file.stat().st_size > 0:

                skipped += 1

                print(
                    f"[SKIP] {month_name}/"
                    f"{filename}"
                )

                continue

            url = BASE_URL + filename

            downloaded = False

            for attempt in range(1, MAX_RETRIES + 1):

                try:

                    print(
                        f"[{success + skipped + failed + 1}/8760] "
                        f"Downloading {month_name}/{filename} "
                        f"(attempt {attempt}/{MAX_RETRIES})"
                    )

                    response = await page.request.get(
                        url,
                        timeout=120000,
                    )

                    status = response.status

                    if status != 200:

                        raise RuntimeError(
                            f"HTTP {status}"
                        )

                    data = await response.body()

                    if len(data) < 1000:

                        raise RuntimeError(
                            f"Downloaded response is too small "
                            f"({len(data)} bytes)"
                        )

                    output_file.write_bytes(data)

                    print(
                        f"    OK "
                        f"({len(data) / (1024 * 1024):.2f} MB)"
                    )

                    success += 1
                    downloaded = True

                    break

                except Exception as e:

                    print(
                        f"    ERROR: {e}"
                    )

                    if attempt < MAX_RETRIES:

                        await asyncio.sleep(3)

            if not downloaded:

                failed += 1

                failures.append(
                    f"{current.isoformat()} {filename}"
                )

                print(
                    f"    FAILED: {filename}"
                )

        if failures:

            failure_file = OUTPUT_DIR / "failed_downloads.txt"

            with open(
                failure_file,
                "w",
                encoding="utf-8",
            ) as f:

                for item in failures:
                    f.write(item + "\n")

        print()
        print("=" * 70)
        print("DOWNLOAD COMPLETE")
        print("=" * 70)

        print(f"Successfully downloaded : {success}")
        print(f"Already existed         : {skipped}")
        print(f"Failed                  : {failed}")
        print(f"Total files             : 8760")

        if failures:

            print()
            print(
                f"Failed filenames saved to:"
            )

            print(
                OUTPUT_DIR / "failed_downloads.txt"
            )

        print()
        print("Output structure:")
        print(OUTPUT_DIR.resolve())

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())