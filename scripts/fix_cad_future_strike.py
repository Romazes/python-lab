"""
run_by_path.py

Usage (required):
  python run_by_path.py <path1> [<path2> ...]

Each provided path should be a symbol folder, e.g.:
  futureoption/cbot/minute/ozc [futureoption/cbot/minute/oym ...]

If no path is provided the script will raise an exception and exit
(immediate fail-safe to avoid processing all data by accident).
"""

import os
import re
import sys
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
from decimal import Decimal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Output base (single global folder next to script)
OUT_BASE = os.path.join(SCRIPT_DIR, "/temp-output-directory")

DEFAULT_START_DATE = "19990101"
DEFAULT_END_DATE = "99991231"


def to_date(yyyymmdd: str):
    return datetime.strptime(yyyymmdd, "%Y%m%d").date()


class StrikeScalingRule:
    def __init__(self, start_date, end_date, strike_scaling_factor):
        self.start_date = to_date(start_date)
        self.end_date = to_date(end_date)
        self.factor = strike_scaling_factor

    def applies_to(self, date: str) -> bool:
        converted_date = to_date(date)
        return self.start_date <= converted_date <= self.end_date

    def __repr__(self):
        return (f"StrikeScalingRule(start_date={self.start_date}, "
                f"end_date={self.end_date}, factor={self.factor})")


class StrikeScalingFactors:
    DATA = {
        # cme
        "cau": StrikeScalingRule("20251208", DEFAULT_END_DATE, 10)
        # "gbu": StrikeScalingRule(DEFAULT_START_DATE, "20210219", 0.1),
        # "nq":  StrikeScalingRule("20200727", "20230317", 0.1),
        # "jpu": StrikeScalingRule("20251113", DEFAULT_END_DATE, 100_000),
        # "mnq": StrikeScalingRule(DEFAULT_START_DATE, "20230317", 0.1),
        # cbot
        # "oub": StrikeScalingRule(DEFAULT_START_DATE, "20160304", 0.1),
        # "ozb": StrikeScalingRule(DEFAULT_START_DATE, "20160304", 0.1),
        # "ozl": StrikeScalingRule(DEFAULT_START_DATE, "20250207", 0.1),
    }

    @classmethod
    def get(cls, symbol):
        return cls.DATA.get(symbol)


# regexes to match "<prefix>_<strike>_<expiry>.csv"
RE_FOP_FILENAME_PATTERN = re.compile(
    r"^(?P<date>\d{8})_"              # 20251103
    r"(?P<fop_ticker>[a-zA-Z0-9]+)_"     # adu
    r"(?P<resolution>[a-zA-Z]+)_"     # minute
    r"(?P<tick_type>[a-zA-Z]+)_"      # quote
    r"(?P<style>[a-zA-Z]+)_"          # american
    r"(?P<right>[a-zA-Z]+)_"          # call
    r"(?P<strike>\d+(?:\.\d+)?)_"               # 6250000, 6.25
    r"(?P<expiry>\d{6,8})"            # 20260306
    r"(?P<extension>\.csv)$",         # .csv
    re.IGNORECASE
)

LEAN_OPTION_SCALE = Decimal(10_000)


def scale_strike(original_strike_str, scaling) -> str:
    try:
        original_strike_decimal = Decimal(original_strike_str)
    except Exception:
        raise ValueError(
            f"Cannot parse strike '{original_strike_str}' to Decimal")

    # strike_read_symbol_from_zip_entry: (original_strike_int / LEAN_OPTION_SCALE)

    scale_strike_price = original_strike_decimal / Decimal(str(scaling))

    # GenerateZipFilePath: (scale_strike_price * LEAN_OPTION_SCALE)

    # int(5050.0) => str(5050) => "5050"
    return format(scale_strike_price, 'f')


def process_zip(zip_path, out_zip_path, strike_scaling_factor_rule: StrikeScalingRule):
    print(f"--> Processing zip: {zip_path}")

    counter_csv_files = 0
    counter_skip_files = 0
    counter_total_files = 0
    with ZipFile(zip_path, "r") as zip_file:
        os.makedirs(os.path.dirname(out_zip_path), exist_ok=True)
        with ZipFile(out_zip_path, "w", compression=ZIP_DEFLATED) as output_zip_file:
            counter_total_files = len(zip_file.infolist())
            for file_in_zip in zip_file.infolist():
                original_name_file_csv = file_in_zip.filename
                new_name_file_csv = original_name_file_csv

                if not original_name_file_csv.lower().endswith(".csv"):
                    raise RuntimeError(
                        f"Unexpected file type: {original_name_file_csv} (expected a .csv file)")

                filename_match = RE_FOP_FILENAME_PATTERN.match(
                    original_name_file_csv)

                if not filename_match:
                    raise ValueError(
                        f"Filename does not match expected FOP pattern: {original_name_file_csv}")

                try:
                    file_date = filename_match.group("date")
                    if strike_scaling_factor_rule.applies_to(file_date):
                        strike = filename_match.group("strike")
                        new_strike = scale_strike(
                            strike, strike_scaling_factor_rule.factor)
                        new_name_file_csv = original_name_file_csv.replace(
                            f"_{strike}_", f"_{new_strike}_")
                        counter_csv_files += 1
                    else:
                        counter_skip_files += 1
                except Exception as e:
                    print(
                        f"WARNING  Could not scale strike in '{original_name_file_csv}': {e}")

                data_file_csv = zip_file.read(original_name_file_csv)
                output_zip_file.writestr(new_name_file_csv, data_file_csv)

    print(f"Processed {counter_csv_files} CSV files (skipped {counter_skip_files}) out of {counter_total_files} in: {out_zip_path}")


def main():
    # Enforce that at least one path argument is provided.
    if len(sys.argv) <= 1:
        # Throw an exception immediately per your requirement.
        raise RuntimeError(
            "No path argument provided. This script requires one or more symbol paths to run.\n"
            "Example:\n  python3 run.py futureoption/cme/minute/adu\n"
            "or multiple:\n  python3 run.py futureoption/cme/minute/adu futureoption/cbot/minute/ozs"
        )

    # Prepare output
    os.makedirs(OUT_BASE, exist_ok=True)

    provided_paths = sys.argv[1:]
    for provided_path in provided_paths:
        provided_path_abs = os.path.abspath(provided_path)
        print(f"\n===== Processing provided path: {provided_path_abs} =====")

        if not os.path.isdir(provided_path_abs):
            raise RuntimeError(
                f"Provided path is not a directory: {provided_path_abs}")

        symbol = os.path.basename(provided_path_abs).lower()
        strike_scaling_factor_rule = StrikeScalingFactors.get(symbol)
        if not strike_scaling_factor_rule:
            print(f"ERROR:: No scaling configured for symbol '{symbol}'")
            continue

        print(
            f"====== FOP ticker '{symbol}' | Strike scaling factor: '{strike_scaling_factor_rule}'")

        # preserve path starting after SCRIPT_DIR to make output structure readable
        rel_src = os.path.relpath(provided_path_abs, SCRIPT_DIR)

        for expiry in os.listdir(provided_path_abs):
            expiry_path = os.path.join(provided_path_abs, expiry)
            out_expiry = os.path.join(OUT_BASE, rel_src, expiry)
            os.makedirs(out_expiry, exist_ok=True)

            for file in os.listdir(expiry_path):
                if not file.lower().endswith(".zip"):
                    continue  # skip non-zip files

                zip_path = os.path.join(expiry_path, file)
                out_zip_path = os.path.join(out_expiry, file)
                try:
                    process_zip(zip_path, out_zip_path,
                                strike_scaling_factor_rule)
                except Exception as e:
                    print(f"EXCEPTION: Error processing {zip_path}: {e}")

    print("\n========== All provided paths processed successfully ==========")


if __name__ == "__main__":
    main()
