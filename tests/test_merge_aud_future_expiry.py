"""
test_merge_aud_future_expiry.py

Pytest tests for merge_aud_future_expiry.py script.

These tests verify that:

1. Non-quarter expiry folders are correctly merged into the next quarter folder.
2. Quarter expiry folders remain as-is.
3. Missing last-quarter folders are automatically created if needed.
4. ZIP files are properly copied or merged without losing data.

Test folder structure:

- Uses temporary directories provided by pytest's tmp_path fixture.
- Creates mock expiry folders with ZIP files inside.
- Checks that merged ZIPs exist in the correct output folders.

Example:

    pytest -v tests/test_merge_aud_future_expiry.py
"""

from zipfile import ZipFile
from scripts.merge_aud_future_expiry import (
    ExpiryFolder,
    next_quarter,
    merge_expiries,
)


def test_quarter_detection():
    assert ExpiryFolder("202503").is_quarter
    assert not ExpiryFolder("202502").is_quarter


def test_next_quarter():
    folders = [
        ExpiryFolder("202501"),
        ExpiryFolder("202503"),
        ExpiryFolder("202506"),
    ]
    assert next_quarter(folders[0], folders).name == "202503"


def test_compute_next_quarter():
    from scripts.merge_aud_future_expiry import compute_next_quarter
    from datetime import datetime

    assert compute_next_quarter(datetime(2025, 4, 1)).name == "202506"
    assert compute_next_quarter(datetime(2025, 7, 1)).name == "202509"
    assert compute_next_quarter(datetime(2025, 11, 1)).name == "202512"


def test_full_merge(tmp_path):
    src = tmp_path / "adu"
    src.mkdir()

    for f in ["202501", "202502", "202503"]:
        (src / f).mkdir()

    with ZipFile(src / "202501" / "a.zip", "w") as z:
        z.writestr("x.txt", "501")

    with ZipFile(src / "202502" / "a.zip", "w") as z:
        z.writestr("y.txt", "502")

    out = tmp_path / "out"

    merge_expiries(str(src), str(out))

    # Small change: merged path is under "adu"
    merged = out / "adu" / "202503" / "a.zip"
    assert merged.exists()
    
    # Verify merged ZIP contains files from both source folders
    with ZipFile(merged, "r") as z:
        namelist = z.namelist()
        assert "x.txt" in namelist, "x.txt from 202501 should be in merged ZIP"
        assert "y.txt" in namelist, "y.txt from 202502 should be in merged ZIP"
        
        # Verify content of both files
        assert z.read("x.txt").decode() == "501", "x.txt content should match"
        assert z.read("y.txt").decode() == "502", "y.txt content should match"


def test_missing_last_quarter(tmp_path):
    src = tmp_path / "adu"
    src.mkdir()

    for f in ["202503", "202504"]:
        (src / f).mkdir()

    with ZipFile(src / "202504" / "a.zip", "w") as z:
        z.writestr("x.txt", "data")

    out = tmp_path / "out"

    merge_expiries(str(src), str(out))

    assert (out / "adu" / "202506" / "a.zip").exists()
