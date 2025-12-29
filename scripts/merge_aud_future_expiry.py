"""
merge_aud_future_expiry.py

This script merges AUD future option expiry folders into their correct quarterly folders.

Folder structure:

    futureoption/cme/minute/adu/YYYYMM/

- Each subfolder YYYYMM represents a futures expiry month.
- Only quarter months (March, June, September, December) are considered "correct" expiries.
- If a folder is not a quarter month, its contents are merged into the next quarter folder.
- ZIP files inside each expiry folder are merged (added or overwritten if duplicates) in the target folder.

Example usage:

    python merge_aud_future_expiry.py

Output:

- Merged folders are written to "temp-output-directory" in the same relative structure
  as the source folders.
- Logs show which folders were merged or skipped.
"""

import os
import sys
import shutil
import logging
from functools import partial
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
from dataclasses import dataclass, field
from typing import List

QUARTER_MONTHS = {3, 6, 9, 12}  # March, June, September, December

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


@dataclass(frozen=True)
class ExpiryFolder:
    """
    Futures expiry folder.

    name: folder name in YYYYMM format
    expiry_date: parsed expiry date
    """
    name: str
    expiry_date: datetime = field(init=False)

    def __post_init__(self):
        try:
            parsed_date = datetime.strptime(self.name, "%Y%m")
        except ValueError:
            raise ValueError(
                f"Invalid expiry folder name (expected YYYYMM): {self.name}")

        object.__setattr__(self, "expiry_date", parsed_date)

    @property
    def is_quarter(self) -> bool:
        return self.expiry_date.month in QUARTER_MONTHS


def get_sorted_expiry_folders(path: str) -> List[ExpiryFolder]:
    """
    Return sorted subfolders representing futures expiry dates (YYYYMM).

    Args:
        path (str): Path to scan for expiry folders.

    Returns:
        List[ExpiryFolder]: Sorted valid YYYYMM folder names.
    """
    folders: List[ExpiryFolder] = []

    for name in os.listdir(path):
        full_path = os.path.join(path, name)
        if not os.path.isdir(full_path):
            logging.warning(f"Skipping non-directory file: {name}")
            continue  # skip files

        try:
            folder = ExpiryFolder(name)
        except ValueError as exc:
            logging.warning(
                f"Skipping invalid folder name (expected YYYYMM): {name} - {exc}")
            continue  # skip invalid folder names

        folders.append(folder)

    return sorted(folders, key=lambda f: f.expiry_date)  # O(n log n)


def compute_next_quarter(date: datetime) -> ExpiryFolder:
    """
    Compute the next calendar quarter after the given date.
    """
    year = date.year
    month = date.month

    if month <= 3:
        qm = 3
    elif month <= 6:
        qm = 6
    elif month <= 9:
        qm = 9
    else:
        qm = 12

    return ExpiryFolder(f"{year}{qm:02d}")


def next_quarter(expiry: ExpiryFolder, all_folders: List[ExpiryFolder]) -> ExpiryFolder:
    # 1. Try to find existing next quarter
    for f in all_folders:
        if f.expiry_date > expiry.expiry_date and f.is_quarter:
            return f

    # 2. Otherwise compute and create next quarter
    computed = compute_next_quarter(expiry.expiry_date)
    logging.info(f"Creating next quarter: {expiry.name} -> {computed.name}")
    return computed


def merge_zip(src_zip: str, dst_zip: str):
    """
    Merge src_zip into dst_zip (append files).
    """
    if not os.path.exists(dst_zip):
        shutil.copy(src_zip, dst_zip)
        return

    with ZipFile(dst_zip, "a", ZIP_DEFLATED) as dst, ZipFile(src_zip, "r") as src:
        for name in src.namelist():
            dst.writestr(name, src.read(name))


def merge_expiries(src_root: str, out_root: str, data_root: str = "data"):
    expiries = get_sorted_expiry_folders(src_root)
    known = {e.name: e for e in expiries}

    for exp in expiries:
        if exp.is_quarter:
            target = exp
            logging.info(f"{exp.name} is a quarter expiry")
        else:
            target = next_quarter(exp, list(known.values()))
            logging.info(f"Merging {exp.name} -> {target.name}")

            if target.name not in known:
                known[target.name] = target

        # Preserve folder structure relative to source
        rel_path = os.path.relpath(src_root, data_root)
        src_dir = os.path.join(src_root, exp.name)
        dst_dir = os.path.join(out_root, rel_path, target.name)
        os.makedirs(dst_dir, exist_ok=True)

        # Execute merge
        for file in os.listdir(src_dir):
            if not file.lower().endswith(".zip"):
                continue

            src_zip = os.path.join(src_dir, file)
            dst_zip = os.path.join(dst_dir, file)

            merge_zip(src_zip, dst_zip)


def main():
    if len(sys.argv) <= 1:
        raise RuntimeError(
            "No path argument provided. This script requires one or more symbol paths to run.\n"
            "Example:\n  python3 run.py futureoption/cme/minute/adu\n"
            "or multiple:\n  python3 run.py futureoption/cme/minute/adu futureoption/cbot/minute/ozs"
        )

    pending_logs = []
    for provided_path in sys.argv[1:]:
        parts = os.path.normpath(provided_path).split(os.sep)

        if len(parts) < 5 or parts[0].lower() != "data" or parts[1] != "futureoption" or parts[3] != "minute":
            msg = f"Invalid path format: {provided_path}\nExpected: data/futureoption/<exchange>/minute/<symbol>"
            pending_logs.append(partial(logging.error, msg))
            continue

        provided_path_abs = os.path.abspath(provided_path)
        if not os.path.isdir(provided_path_abs):
            msg = f"Provided path is not a directory: {provided_path_abs}"
            pending_logs.append(partial(logging.error, msg))
            continue

        temp_output_directory = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "temp-output-directory")

        # Prepare output
        os.makedirs(temp_output_directory, exist_ok=True)

        logging.info(f"Processing provided path: {provided_path_abs}")

        merge_expiries(provided_path_abs, temp_output_directory, parts[0])

    if pending_logs:
        logging.error("Completed with %d error(s):", len(pending_logs))
        for log_action in pending_logs:
            log_action()
    else:
        logging.info("Done \u2714")


if __name__ == "__main__":
    main()
