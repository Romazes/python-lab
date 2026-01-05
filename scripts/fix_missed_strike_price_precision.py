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
from zipfile import ZipFile, ZIP_DEFLATED
from decimal import Decimal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Output base (single global folder next to script)
OUT_BASE = os.path.join(SCRIPT_DIR, "/temp-output-directory")


class StrikeScalingRule:
    def __init__(self, strike_scaling_factor):
        self.factor = Decimal(str(strike_scaling_factor))

    def __repr__(self):
        return (f"StrikeScalingRule(factor={self.factor})")


class StrikeScalingFactors:
    DATA = {
        "adu": StrikeScalingRule(1_000),
        "euu": StrikeScalingRule(1_000),
        "jpu": StrikeScalingRule(100_000)
    }

    @classmethod
    def get(cls, symbol):
        return cls.DATA.get(symbol)


# regexes to match "<prefix>_<strike>_<expiry>.csv"
RE_FOP_FILENAME_PATTERN = re.compile(
    r"^(?P<date>\d{8})_"              # 20251103
    r"(?P<fop_ticker>[a-zA-Z0-9]+)_"  # adu
    r"(?P<resolution>[a-zA-Z]+)_"     # minute
    r"(?P<tick_type>[a-zA-Z]+)_"      # quote
    r"(?P<style>[a-zA-Z]+)_"          # american
    r"(?P<right>[a-zA-Z]+)_"          # call
    r"(?P<strike>\d+(?:\.\d+)?)_"     # 6250000, 6.25
    r"(?P<expiry>\d{6,8})"            # 20260306
    r"(?P<extension>\.csv)$",         # .csv
    re.IGNORECASE
)

DIVISOR = Decimal(10)
REMAINDER_TWO = Decimal(2)
REMAINDER_SEVEN = Decimal(7)
LEAN_OPTION_SCALE = Decimal(10_000)


def scale_strike(scaled_strike_file_name_format: Decimal, scaling: Decimal) -> str:
    next_decimal_position = scaling * Decimal(10)
    # (11570 / 10_000) + (5 / 1_000)
    scale_strike_price = (scaled_strike_file_name_format /
                          LEAN_OPTION_SCALE) + (5 / next_decimal_position)
    scale_strike_price_file_name_format = scale_strike_price * LEAN_OPTION_SCALE
    print(
        f"old: {scaled_strike_file_name_format} => new: {scale_strike_price_file_name_format}")
    return scale_strike_price_file_name_format.normalize()


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
                    scaled_strike_file_name_format = Decimal(
                        str(filename_match.group("strike")))
                    # 11570 / 10_000 * 1_000
                    algo_seek_strike_format = scaled_strike_file_name_format / \
                        LEAN_OPTION_SCALE * strike_scaling_factor_rule.factor
                    remainder = algo_seek_strike_format % DIVISOR
                    if remainder == REMAINDER_TWO or remainder == REMAINDER_SEVEN:
                        new_strike = scale_strike(
                            scaled_strike_file_name_format, strike_scaling_factor_rule.factor)
                        new_name_file_csv = original_name_file_csv.replace(
                            f"_{scaled_strike_file_name_format}_", f"_{new_strike}_")
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
            "Example:\n  python3 run.py data/futureoption/cme/minute/adu\n"
            "or multiple:\n  python3 run.py data/futureoption/cme/minute/adu futureoption/cbot/minute/ozs"
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
        print(provided_path_abs)

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
