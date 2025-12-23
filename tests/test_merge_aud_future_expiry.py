"""
test_merge_aud_future_expiry.py

Pytest tests for merge_aud_future_expiry.py script.

These tests verify that:

1. Non-quarter expiry folders are correctly merged into the next quarter folder.
2. Quarter expiry folders remain as-is.
3. Missing last-quarter folders are automatically created if needed.
4. ZIP files are properly copied or merged without losing data.
5. Duplicate entries in ZIP files are skipped to prevent multiple entries with the same name.
6. Non-duplicate files are correctly added when merging ZIP files.

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
    merge_zip,
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


def test_merge_zip_no_duplicates(tmp_path):
    """Test that merge_zip correctly adds non-duplicate files."""
    src_zip = tmp_path / "src.zip"
    dst_zip = tmp_path / "dst.zip"

    # Create source ZIP with files a.txt and b.txt
    with ZipFile(src_zip, "w") as z:
        z.writestr("a.txt", "content_a")
        z.writestr("b.txt", "content_b")

    # Create destination ZIP with file c.txt
    with ZipFile(dst_zip, "w") as z:
        z.writestr("c.txt", "content_c")

    # Merge source into destination
    merge_zip(str(src_zip), str(dst_zip))

    # Verify all three files are in the destination
    with ZipFile(dst_zip, "r") as z:
        names = z.namelist()
        assert "a.txt" in names
        assert "b.txt" in names
        assert "c.txt" in names
        assert len(names) == 3


def test_merge_zip_with_duplicates(tmp_path):
    """Test that merge_zip skips duplicate entries to prevent multiple entries with the same name."""
    src_zip = tmp_path / "src.zip"
    dst_zip = tmp_path / "dst.zip"

    # Create source ZIP with files a.txt and b.txt
    with ZipFile(src_zip, "w") as z:
        z.writestr("a.txt", "new_content_a")
        z.writestr("b.txt", "new_content_b")

    # Create destination ZIP with files a.txt (different content) and c.txt
    with ZipFile(dst_zip, "w") as z:
        z.writestr("a.txt", "old_content_a")
        z.writestr("c.txt", "content_c")

    # Merge source into destination
    merge_zip(str(src_zip), str(dst_zip))

    # Verify no duplicate entries and original content is preserved
    with ZipFile(dst_zip, "r") as z:
        names = z.namelist()
        # Should have a.txt (original), b.txt (new), c.txt (original)
        assert names.count("a.txt") == 1, "a.txt should appear only once"
        assert names.count("b.txt") == 1, "b.txt should appear only once"
        assert names.count("c.txt") == 1, "c.txt should appear only once"
        assert len(names) == 3
        
        # Original content should be preserved (not overwritten)
        assert z.read("a.txt").decode() == "old_content_a"
        assert z.read("b.txt").decode() == "new_content_b"
        assert z.read("c.txt").decode() == "content_c"


def test_merge_zip_create_new_destination(tmp_path):
    """Test that merge_zip creates a new destination when it doesn't exist."""
    src_zip = tmp_path / "src.zip"
    dst_zip = tmp_path / "dst.zip"

    # Create source ZIP
    with ZipFile(src_zip, "w") as z:
        z.writestr("a.txt", "content_a")
        z.writestr("b.txt", "content_b")

    # Destination doesn't exist yet
    assert not dst_zip.exists()

    # Merge source into non-existent destination
    merge_zip(str(src_zip), str(dst_zip))

    # Verify destination was created with all files
    assert dst_zip.exists()
    with ZipFile(dst_zip, "r") as z:
        names = z.namelist()
        assert "a.txt" in names
        assert "b.txt" in names
        assert len(names) == 2
