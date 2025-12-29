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

import os
import sys
import shutil
import logging
import pytest
from datetime import datetime
from zipfile import ZipFile
from scripts.merge_aud_future_expiry import (
    ExpiryFolder,
    main,
    next_quarter,
    merge_expiries,
    compute_next_quarter,
    get_sorted_expiry_folders,
)

# Constant for output directory name used across tests
TEMP_OUTPUT_DIR_NAME = "temp-output-directory"


@pytest.fixture
def script_temp_output_dir():
    """
    Fixture to get and cleanup the temp-output-directory created by the main script.
    
    Returns the path to the temp-output-directory and ensures it's cleaned up after the test.
    """
    import scripts.merge_aud_future_expiry as script_module
    script_file = script_module.__file__
    temp_output_dir = os.path.join(
        os.path.dirname(script_file), TEMP_OUTPUT_DIR_NAME)

    yield temp_output_dir

    # Cleanup after test
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)


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
    assert compute_next_quarter(datetime(2025, 4, 1)).name == "202506"
    assert compute_next_quarter(datetime(2025, 7, 1)).name == "202509"
    assert compute_next_quarter(datetime(2025, 11, 1)).name == "202512"


def test_full_merge(tmp_path, script_temp_output_dir):
    src = tmp_path / "adu"
    src.mkdir()

    for f in ["202501", "202502", "202503"]:
        (src / f).mkdir()

    with ZipFile(src / "202501" / "a.zip", "w") as z:
        z.writestr("x.txt", "501")

    with ZipFile(src / "202502" / "a.zip", "w") as z:
        z.writestr("y.txt", "502")

    out = tmp_path / TEMP_OUTPUT_DIR_NAME

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


def test_missing_last_quarter(tmp_path, script_temp_output_dir):
    src = tmp_path / "adu"
    src.mkdir()

    for f in ["202503", "202504"]:
        (src / f).mkdir()

    with ZipFile(src / "202504" / "a.zip", "w") as z:
        z.writestr("x.txt", "data")

    out = tmp_path / TEMP_OUTPUT_DIR_NAME

    merge_expiries(str(src), str(out))

    assert (out / "adu" / "202506" / "a.zip").exists()


def test_invalid_folder_name_handling(tmp_path):
    """Test that get_sorted_expiry_folders gracefully handles invalid folder names."""
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


def test_quarter_folders_remain_as_is(tmp_path, script_temp_output_dir):
    """Test that quarter expiry folders are copied as-is without merging into another quarter."""
    src = tmp_path / "adu"
    src.mkdir()

    # Create quarter folders (March, June, September)
    for f in ["202503", "202506", "202509"]:
        (src / f).mkdir()

    # Add ZIP files to each quarter folder
    with ZipFile(src / "202503" / "20240320_quote_american.zip", "w") as z:
        z.writestr(
            "20240320_adu_minute_quote_american_call_5000_20250103.csv", "March data")

    with ZipFile(src / "202506" / "20240620_trade_american.zip", "w") as z:
        z.writestr(
            "20240620_adu_minute_quote_american_call_5000_20250103.csv", "June data")

    with ZipFile(src / "202509" / "20241020_trade_american.zip", "w") as z:
        z.writestr(
            "20241020_adu_minute_quote_american_call_5000_20250103.csv", "September data")

    out = tmp_path / TEMP_OUTPUT_DIR_NAME

    merge_expiries(str(src), str(out))

    # Verify each quarter folder exists in output with its original ZIP
    march_zip = out / "adu" / "202503" / "20240320_quote_american.zip"
    assert march_zip.exists(), "March quarter folder should exist in output"

    june_zip = out / "adu" / "202506" / "20240620_trade_american.zip"
    assert june_zip.exists(), "June quarter folder should exist in output"

    september_zip = out / "adu" / "202509" / "20241020_trade_american.zip"
    assert september_zip.exists(), "September quarter folder should exist in output"

    # Verify content remains unchanged
    with ZipFile(march_zip, "r") as z:
        assert "20240320_adu_minute_quote_american_call_5000_20250103.csv" in z.namelist()
        assert z.read("20240320_adu_minute_quote_american_call_5000_20250103.csv").decode(
        ) == "March data"

    with ZipFile(june_zip, "r") as z:
        assert "20240620_adu_minute_quote_american_call_5000_20250103.csv" in z.namelist()
        assert z.read(
            "20240620_adu_minute_quote_american_call_5000_20250103.csv").decode() == "June data"

    with ZipFile(september_zip, "r") as z:
        assert "20241020_adu_minute_quote_american_call_5000_20250103.csv" in z.namelist()
        assert z.read("20241020_adu_minute_quote_american_call_5000_20250103.csv").decode(
        ) == "September data"


def test_main_no_arguments(monkeypatch):
    """Test that main() raises RuntimeError when no arguments are provided."""

    # Mock sys.argv to have only the script name (no arguments)
    monkeypatch.setattr(sys, 'argv', ['merge_aud_future_expiry.py'])

    # Should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        main()

    assert "No path argument provided" in str(exc_info.value)


def test_main_valid_single_argument(tmp_path, monkeypatch, caplog, script_temp_output_dir):
    """Test that main() processes a single valid argument correctly."""

    # Create test directory structure in current directory
    test_dir = tmp_path / "test_workspace" / \
        "futureoption" / "cme" / "minute" / "adu"
    test_dir.mkdir(parents=True)

    # Create a test folder with a ZIP file
    (test_dir / "202501").mkdir()
    with ZipFile(test_dir / "202501" / "test.zip", "w") as z:
        z.writestr("data.txt", "test data")

    # Change to the parent directory so the path can be relative
    original_cwd = os.getcwd()
    os.chdir(tmp_path / "test_workspace")

    try:
        # Mock sys.argv with a valid relative path
        monkeypatch.setattr(
            sys, 'argv', ['merge_aud_future_expiry.py', 'futureoption/cme/minute/adu'])

        # Run main - should complete without errors
        with caplog.at_level(logging.INFO):
            main()

        # Check log contains success message
        assert "Done" in caplog.text
    finally:
        os.chdir(original_cwd)


def test_main_valid_multiple_arguments(tmp_path, monkeypatch, caplog, script_temp_output_dir):
    """Test that main() processes multiple valid arguments correctly."""

    # Create first test directory structure
    test_dir1 = tmp_path / "test_workspace" / \
        "futureoption" / "cme" / "minute" / "adu"
    test_dir1.mkdir(parents=True)
    (test_dir1 / "202501").mkdir()
    with ZipFile(test_dir1 / "202501" / "test1.zip", "w") as z:
        z.writestr("data1.txt", "test data 1")

    # Create second test directory structure
    test_dir2 = tmp_path / "test_workspace" / \
        "futureoption" / "cbot" / "minute" / "ozs"
    test_dir2.mkdir(parents=True)
    (test_dir2 / "202502").mkdir()
    with ZipFile(test_dir2 / "202502" / "test2.zip", "w") as z:
        z.writestr("data2.txt", "test data 2")

    # Change to the parent directory so the paths can be relative
    original_cwd = os.getcwd()
    os.chdir(tmp_path / "test_workspace")

    try:
        # Mock sys.argv with multiple valid relative paths
        monkeypatch.setattr(sys, 'argv', [
            'merge_aud_future_expiry.py',
            'futureoption/cme/minute/adu',
            'futureoption/cbot/minute/ozs'
        ])

        # Run main - should complete without errors
        with caplog.at_level(logging.INFO):
            main()

        # Check log contains success message
        assert "Done" in caplog.text
    finally:
        os.chdir(original_cwd)


def test_main_invalid_path_format(monkeypatch, caplog):
    """Test that main() handles invalid path format correctly."""

    # Mock sys.argv with an invalid path format
    monkeypatch.setattr(
        sys, 'argv', ['merge_aud_future_expiry.py', 'invalid/path'])

    # Run main - should complete but with error logged
    with caplog.at_level(logging.ERROR):
        main()

    # Check log contains error message
    assert "Invalid path format" in caplog.text
    assert "Completed with" in caplog.text and "error" in caplog.text


def test_main_non_existent_directory(tmp_path, monkeypatch, caplog):
    """Test that main() handles non-existent directory correctly."""

    # Change to tmp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Mock sys.argv with a non-existent path (but valid format)
        monkeypatch.setattr(sys, 'argv', [
                            'merge_aud_future_expiry.py', 'futureoption/cme/minute/nonexistent'])

        # Run main - should complete but with error logged
        with caplog.at_level(logging.ERROR):
            main()

        # Check log contains error message
        assert "not a directory" in caplog.text
        assert "Completed with" in caplog.text and "error" in caplog.text
    finally:
        os.chdir(original_cwd)
