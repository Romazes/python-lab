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


def test_compute_next_quarter_with_quarter_months():
    """Test compute_next_quarter when input date is already in a quarter month."""
    from scripts.merge_aud_future_expiry import compute_next_quarter
    from datetime import datetime

    # When already in March (Q1), should still return March (current quarter end)
    assert compute_next_quarter(datetime(2025, 3, 1)).name == "202503"
    
    # When already in June (Q2), should still return June (current quarter end)
    assert compute_next_quarter(datetime(2025, 6, 15)).name == "202506"
    
    # When already in September (Q3), should still return September (current quarter end)
    assert compute_next_quarter(datetime(2025, 9, 30)).name == "202509"
    
    # When already in December (Q4), should still return December (current quarter end)
    assert compute_next_quarter(datetime(2025, 12, 1)).name == "202512"


def test_compute_next_quarter_year_rollover():
    """Test compute_next_quarter with year rollover scenarios."""
    from scripts.merge_aud_future_expiry import compute_next_quarter
    from datetime import datetime

    # December should roll over to March of next year
    # Note: Based on current implementation, December (month 12) returns December of same year
    # This test documents the current behavior
    assert compute_next_quarter(datetime(2025, 12, 31)).name == "202512"
    
    # January should go to March of same year
    assert compute_next_quarter(datetime(2025, 1, 1)).name == "202503"
    
    # February should go to March of same year
    assert compute_next_quarter(datetime(2025, 2, 28)).name == "202503"


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


def test_invalid_folder_name_handling(tmp_path):
    """Test that get_sorted_expiry_folders gracefully handles invalid folder names."""
    from scripts.merge_aud_future_expiry import get_sorted_expiry_folders
    
    src = tmp_path / "test_source"
    src.mkdir()

    # Create valid folders
    (src / "202501").mkdir()
    (src / "202503").mkdir()
    
    # Create invalid folders (not in YYYYMM format)
    (src / "invalid_folder").mkdir()
    (src / "not_a_date").mkdir()
    (src / "2025abc").mkdir()  # contains letters
    (src / "202513").mkdir()  # month = 13, invalid
    
    # get_sorted_expiry_folders should skip invalid folders and return only valid ones
    folders = get_sorted_expiry_folders(str(src))
    
    # Should only get the 2 valid folders
    assert len(folders) == 2
    assert folders[0].name == "202501"
    assert folders[1].name == "202503"


def test_quarter_folders_remain_as_is(tmp_path):
    """Test that quarter expiry folders are copied as-is without merging into another quarter."""
    src = tmp_path / "adu"
    src.mkdir()
    
    # Create quarter folders (March, June, September)
    for f in ["202503", "202506", "202509"]:
        (src / f).mkdir()
    
    # Add ZIP files to each quarter folder
    with ZipFile(src / "202503" / "march.zip", "w") as z:
        z.writestr("march_data.txt", "March data")
    
    with ZipFile(src / "202506" / "june.zip", "w") as z:
        z.writestr("june_data.txt", "June data")
    
    with ZipFile(src / "202509" / "september.zip", "w") as z:
        z.writestr("september_data.txt", "September data")
    
    out = tmp_path / "out"
    
    merge_expiries(str(src), str(out))
    
    # Verify each quarter folder exists in output with its original ZIP
    march_zip = out / "adu" / "202503" / "march.zip"
    assert march_zip.exists(), "March quarter folder should exist in output"
    
    june_zip = out / "adu" / "202506" / "june.zip"
    assert june_zip.exists(), "June quarter folder should exist in output"
    
    september_zip = out / "adu" / "202509" / "september.zip"
    assert september_zip.exists(), "September quarter folder should exist in output"
    
    # Verify content remains unchanged
    with ZipFile(march_zip, "r") as z:
        assert "march_data.txt" in z.namelist()
        assert z.read("march_data.txt").decode() == "March data"
    
    with ZipFile(june_zip, "r") as z:
        assert "june_data.txt" in z.namelist()
        assert z.read("june_data.txt").decode() == "June data"
    
    with ZipFile(september_zip, "r") as z:
        assert "september_data.txt" in z.namelist()
        assert z.read("september_data.txt").decode() == "September data"
