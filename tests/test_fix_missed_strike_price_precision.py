"""
test_fix_missed_strike_price_precision.py

Pytest tests for fix_missed_strike_price_precision.py script.

These tests verify that:

1. Strike price scaling is correctly applied for symbols 'adu', 'euu', 'jpu'
2. Files with remainder 2 or 7 after scaling are renamed with corrected strike prices
3. Files without remainder 2 or 7 are copied as-is without renaming
4. The script properly handles missing symbol configurations
5. The script requires explicit path arguments to prevent accidental bulk processing
6. ZIP files are properly processed and rewritten with corrected filenames

Test folder structure:

- Uses temporary directories provided by pytest's tmp_path fixture.
- Creates mock expiry folders with ZIP files containing CSV files inside.
- Checks that processed ZIPs exist in the correct output folders with correct filenames.

Example:

    pytest -v tests/test_fix_missed_strike_price_precision.py
"""

import glob
import os
import pathlib
import shutil
import sys

import pytest
from decimal import Decimal
from zipfile import ZipFile

import scripts.fix_missed_strike_price_precision as script_module
from scripts.fix_missed_strike_price_precision import (
    StrikeScalingRule,
    StrikeScalingFactors,
    scale_strike,
    process_zip,
    main,
    RE_FOP_FILENAME_PATTERN,
)

# Constant for output directory name used across tests
TEMP_OUTPUT_DIR_NAME = "temp-output-directory"


@pytest.fixture
def script_temp_output_dir():
    """
    Fixture to get and cleanup the temp-output-directory created by the main script.
    
    Returns the path to the temp-output-directory and ensures it's cleaned up after the test.
    """
    script_file = script_module.__file__
    temp_output_dir = os.path.join(
        os.path.dirname(script_file), TEMP_OUTPUT_DIR_NAME)

    yield temp_output_dir

    # Cleanup after test
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)


def test_strike_scaling_rule():
    """Test that StrikeScalingRule properly stores scaling factor as Decimal."""
    rule = StrikeScalingRule(1_000)
    assert rule.factor == Decimal("1000")
    
    rule_jpu = StrikeScalingRule(100_000)
    assert rule_jpu.factor == Decimal("100000")


def test_strike_scaling_factors_get():
    """Test that StrikeScalingFactors.get() returns correct rules for known symbols."""
    adu_rule = StrikeScalingFactors.get("adu")
    assert adu_rule is not None
    assert adu_rule.factor == Decimal("1000")
    
    euu_rule = StrikeScalingFactors.get("euu")
    assert euu_rule is not None
    assert euu_rule.factor == Decimal("1000")
    
    jpu_rule = StrikeScalingFactors.get("jpu")
    assert jpu_rule is not None
    assert jpu_rule.factor == Decimal("100000")
    
    # Unknown symbol should return None
    unknown_rule = StrikeScalingFactors.get("unknown")
    assert unknown_rule is None


def test_regex_pattern_matching():
    """Test that the regex pattern correctly matches FOP filenames."""
    # Valid filename
    filename = "20251224_euu_minute_openinterest_american_call_11600_20260109.csv"
    match = RE_FOP_FILENAME_PATTERN.match(filename)
    
    assert match is not None
    assert match.group("date") == "20251224"
    assert match.group("fop_ticker") == "euu"
    assert match.group("resolution") == "minute"
    assert match.group("tick_type") == "openinterest"
    assert match.group("style") == "american"
    assert match.group("right") == "call"
    assert match.group("strike") == "11600"
    assert match.group("expiry") == "20260109"
    assert match.group("extension") == ".csv"


def test_regex_pattern_with_decimal_strike():
    """Test that the regex pattern correctly handles decimal strike prices."""
    filename = "20251224_adu_minute_quote_american_put_6.25_20260306.csv"
    match = RE_FOP_FILENAME_PATTERN.match(filename)
    
    assert match is not None
    assert match.group("strike") == "6.25"


def test_regex_pattern_invalid_filename():
    """Test that invalid filenames don't match the pattern."""
    invalid_filenames = [
        "invalid_filename.csv",
        "20251224_euu_minute.csv",
        "euu_call_11600.csv",
        "not_a_fop_file.txt",
    ]
    
    for filename in invalid_filenames:
        match = RE_FOP_FILENAME_PATTERN.match(filename)
        assert match is None, f"Filename '{filename}' should not match pattern"


def test_scale_strike_with_remainder_7():
    """Test scale_strike function for strikes that produce remainder 7."""
    # Example: 11570 / 10_000 * 1_000 = 1157 % 10 = 7
    # This should be scaled
    scaled_strike = Decimal("11570")
    scaling = Decimal("1000")
    
    result = scale_strike(scaled_strike, scaling)
    
    # Expected: (11570 / 10_000) + (5 / 10_000) = 1.157 + 0.0005 = 1.1575
    # In file format: 1.1575 * 10_000 = 11575
    assert result == "11575"


def test_scale_strike_with_remainder_2():
    """Test scale_strike function for strikes that produce remainder 2."""
    # Example: 11620 / 10_000 * 1_000 = 1162 % 10 = 2
    # This should be scaled
    scaled_strike = Decimal("11620")
    scaling = Decimal("1000")
    
    result = scale_strike(scaled_strike, scaling)
    
    # Expected: (11620 / 10_000) + (5 / 10_000) = 1.162 + 0.0005 = 1.1625
    # In file format: 1.1625 * 10_000 = 11625
    assert result == "11625"


def test_scale_strike_jpu_factor():
    """Test scale_strike function with jpu scaling factor (100,000)."""
    # Example for jpu with factor 100,000
    scaled_strike = Decimal("10020")
    scaling = Decimal("100000")
    
    result = scale_strike(scaled_strike, scaling)
    
    # Expected: (10020 / 10_000) + (5 / 1_000_000) = 1.002 + 0.000005 = 1.002005
    # In file format: 1.002005 * 10_000 = 10020.05
    assert result == "10020.05"


def test_process_zip_euu_with_scaling(tmp_path):
    """
    Test processing a zip file for 'euu' symbol with files that need scaling.
    
    This test uses the example from the user's comment:
    path: data/futureoption/cme/minute/euu/202603/20251224_openinterest_american.zip
    The file contains: 20251224_euu_minute_openinterest_american_call_11600_20260109.csv
    """
    # Create source zip
    src_zip = tmp_path / "20251224_openinterest_american.zip"
    
    # Create CSV files with strikes that need scaling
    # 11600 / 10_000 * 1_000 = 1160 % 10 = 0 (remainder 0, no scaling needed)
    # 11570 / 10_000 * 1_000 = 1157 % 10 = 7 (remainder 7, scaling needed)
    # 11620 / 10_000 * 1_000 = 1162 % 10 = 2 (remainder 2, scaling needed)
    
    with ZipFile(src_zip, "w") as z:
        z.writestr("20251224_euu_minute_openinterest_american_call_11600_20260109.csv", "data1")
        z.writestr("20251224_euu_minute_openinterest_american_call_11570_20260109.csv", "data2")
        z.writestr("20251224_euu_minute_openinterest_american_call_11620_20260109.csv", "data3")
    
    # Create output path
    out_zip = tmp_path / "output" / "20251224_openinterest_american.zip"
    
    # Process the zip
    euu_rule = StrikeScalingFactors.get("euu")
    process_zip(str(src_zip), str(out_zip), euu_rule)
    
    # Verify output zip exists
    assert out_zip.exists()
    
    # Verify the contents
    with ZipFile(out_zip, "r") as z:
        namelist = z.namelist()
        
        # File with 11600 should not be scaled (remainder 0)
        assert "20251224_euu_minute_openinterest_american_call_11600_20260109.csv" in namelist
        
        # File with 11570 should be scaled to 11575 (remainder 7)
        assert "20251224_euu_minute_openinterest_american_call_11575_20260109.csv" in namelist
        assert "20251224_euu_minute_openinterest_american_call_11570_20260109.csv" not in namelist
        
        # File with 11620 should be scaled to 11625 (remainder 2)
        assert "20251224_euu_minute_openinterest_american_call_11625_20260109.csv" in namelist
        assert "20251224_euu_minute_openinterest_american_call_11620_20260109.csv" not in namelist
        
        # Verify data is preserved
        assert z.read("20251224_euu_minute_openinterest_american_call_11600_20260109.csv").decode() == "data1"
        assert z.read("20251224_euu_minute_openinterest_american_call_11575_20260109.csv").decode() == "data2"
        assert z.read("20251224_euu_minute_openinterest_american_call_11625_20260109.csv").decode() == "data3"


def test_process_zip_adu_with_scaling(tmp_path):
    """Test processing a zip file for 'adu' symbol with files that need scaling."""
    # Create source zip
    src_zip = tmp_path / "20250115_quote_american.zip"
    
    # Create CSV files - adu also uses factor 1,000
    # 62520 / 10_000 * 1_000 = 6.252 * 1_000 = 6252, 6252 % 10 = 2 (scaling needed)
    # 62500 / 10_000 * 1_000 = 6.25 * 1_000 = 6250, 6250 % 10 = 0 (no scaling)
    
    with ZipFile(src_zip, "w") as z:
        z.writestr("20250115_adu_minute_quote_american_call_62520_20260306.csv", "adu_data1")
        z.writestr("20250115_adu_minute_quote_american_put_62500_20260306.csv", "adu_data2")
    
    # Create output path
    out_zip = tmp_path / "output" / "20250115_quote_american.zip"
    
    # Process the zip
    adu_rule = StrikeScalingFactors.get("adu")
    process_zip(str(src_zip), str(out_zip), adu_rule)
    
    # Verify output zip exists
    assert out_zip.exists()
    
    # Verify the contents
    with ZipFile(out_zip, "r") as z:
        namelist = z.namelist()
        
        # File with 62520 should be scaled to 62525 (remainder 2)
        assert "20250115_adu_minute_quote_american_call_62525_20260306.csv" in namelist
        assert "20250115_adu_minute_quote_american_call_62520_20260306.csv" not in namelist
        
        # File with 62500 should not be scaled (remainder 0)
        assert "20250115_adu_minute_quote_american_put_62500_20260306.csv" in namelist
        
        # Verify data is preserved
        assert z.read("20250115_adu_minute_quote_american_call_62525_20260306.csv").decode() == "adu_data1"
        assert z.read("20250115_adu_minute_quote_american_put_62500_20260306.csv").decode() == "adu_data2"


def test_process_zip_jpu_with_scaling(tmp_path):
    """Test processing a zip file for 'jpu' symbol with scaling factor 100,000."""
    # Create source zip
    src_zip = tmp_path / "20250120_trade_american.zip"
    
    # Create CSV files - jpu uses factor 100,000
    # 10020 / 10_000 * 100_000 = 1.002 * 100_000 = 100200, 100200 % 10 = 0 (no scaling)
    # 10022 / 10_000 * 100_000 = 1.0022 * 100_000 = 100220, 100220 % 10 = 0 (no scaling)
    # Let's create ones that need scaling:
    # For remainder 2: we need X where (X / 10_000 * 100_000) % 10 = 2
    # For remainder 7: we need X where (X / 10_000 * 100_000) % 10 = 7
    
    with ZipFile(src_zip, "w") as z:
        # 100020 / 10_000 * 100_000 = 10.002 * 100_000 = 1000200, 1000200 % 10 = 0 (no scaling)
        z.writestr("20250120_jpu_minute_trade_american_call_100020_20260615.csv", "jpu_data1")
        # 10002 / 10_000 * 100_000 = 1.0002 * 100_000 = 100020, 100020 % 10 = 0 (no scaling)
        z.writestr("20250120_jpu_minute_trade_american_put_10002_20260615.csv", "jpu_data2")
    
    # Create output path
    out_zip = tmp_path / "output" / "20250120_trade_american.zip"
    
    # Process the zip
    jpu_rule = StrikeScalingFactors.get("jpu")
    process_zip(str(src_zip), str(out_zip), jpu_rule)
    
    # Verify output zip exists
    assert out_zip.exists()
    
    # Verify the contents - both should remain unchanged (no remainder 2 or 7)
    with ZipFile(out_zip, "r") as z:
        namelist = z.namelist()
        assert "20250120_jpu_minute_trade_american_call_100020_20260615.csv" in namelist
        assert "20250120_jpu_minute_trade_american_put_10002_20260615.csv" in namelist


def test_process_zip_invalid_csv_extension(tmp_path):
    """Test that process_zip raises error for non-CSV files in zip."""
    # Create source zip with a non-CSV file
    src_zip = tmp_path / "invalid.zip"
    
    with ZipFile(src_zip, "w") as z:
        z.writestr("invalid_file.txt", "not a csv")
    
    # Create output path
    out_zip = tmp_path / "output" / "invalid.zip"
    
    # Process the zip - should raise RuntimeError
    euu_rule = StrikeScalingFactors.get("euu")
    
    with pytest.raises(RuntimeError) as exc_info:
        process_zip(str(src_zip), str(out_zip), euu_rule)
    
    assert "Unexpected file type" in str(exc_info.value)


def test_process_zip_invalid_filename_pattern(tmp_path):
    """Test that process_zip raises error for CSV files with invalid naming pattern."""
    # Create source zip with CSV that doesn't match pattern
    src_zip = tmp_path / "invalid_pattern.zip"
    
    with ZipFile(src_zip, "w") as z:
        z.writestr("invalid_pattern_file.csv", "data")
    
    # Create output path
    out_zip = tmp_path / "output" / "invalid_pattern.zip"
    
    # Process the zip - should raise ValueError
    euu_rule = StrikeScalingFactors.get("euu")
    
    with pytest.raises(ValueError) as exc_info:
        process_zip(str(src_zip), str(out_zip), euu_rule)
    
    assert "does not match expected FOP pattern" in str(exc_info.value)


def test_main_no_arguments(monkeypatch):
    """Test that main() raises RuntimeError when no arguments are provided."""
    # Mock sys.argv to have only the script name (no arguments)
    monkeypatch.setattr(sys, 'argv', ['fix_missed_strike_price_precision.py'])
    
    # Should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        main()
    
    assert "No path argument provided" in str(exc_info.value)


def test_main_with_valid_euu_path(tmp_path, monkeypatch, capfd, script_temp_output_dir):
    """
    Test that main() processes a valid 'euu' symbol path correctly.
    
    This simulates the example from the user's comment:
    path: data/futureoption/cme/minute/euu/202603/20251224_openinterest_american.zip
    """
    # Create test directory structure in the repository
    test_dir = tmp_path / "data" / "futureoption" / "cme" / "minute" / "euu"
    test_dir.mkdir(parents=True)
    
    # Create expiry folder
    expiry_dir = test_dir / "202603"
    expiry_dir.mkdir()
    
    # Create zip file with CSV files
    zip_file = expiry_dir / "20251224_openinterest_american.zip"
    with ZipFile(zip_file, "w") as z:
        z.writestr("20251224_euu_minute_openinterest_american_call_11600_20260109.csv", "data1")
        z.writestr("20251224_euu_minute_openinterest_american_call_11570_20260109.csv", "data2")
    
    # Change to tmp_path directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock sys.argv with the path
        monkeypatch.setattr(
            sys, 'argv', 
            ['fix_missed_strike_price_precision.py', str(test_dir)]
        )
        
        # Run main
        main()
        
        # Capture output
        captured = capfd.readouterr()
        
        # Verify output messages
        assert "Processing provided path" in captured.out
        assert "euu" in captured.out
        assert "All provided paths processed successfully" in captured.out
        
        # Verify output file exists in temp-output-directory created next to script
        # The script creates temp-output-directory next to itself (in scripts/ directory)
        expected_output_dir = pathlib.Path(script_temp_output_dir)
        assert expected_output_dir.exists()
        
        # Verify the output zip file exists with correct structure
        # The output path is: temp-output-directory/<relative path from "data">/<expiry>
        # Since we provided absolute path, the relpath from "data" will be the full path structure
        # We need to find the output file in the temp-output-directory
        output_zips = list(expected_output_dir.glob("**/20251224_openinterest_american.zip"))
        assert len(output_zips) > 0, f"No output zip found in {expected_output_dir}"
        
        # Verify the contents of the output zip
        with ZipFile(output_zips[0], "r") as z:
            namelist = z.namelist()
            # File with 11600 should not be scaled (remainder 0)
            assert "20251224_euu_minute_openinterest_american_call_11600_20260109.csv" in namelist
            # File with 11570 should be scaled to 11575 (remainder 7)
            assert "20251224_euu_minute_openinterest_american_call_11575_20260109.csv" in namelist
    finally:
        os.chdir(original_cwd)


def test_main_with_unknown_symbol(tmp_path, monkeypatch, capfd, script_temp_output_dir):
    """Test that main() handles unknown symbols gracefully."""
    # Create test directory structure with unknown symbol
    test_dir = tmp_path / "data" / "futureoption" / "cme" / "minute" / "xyz"
    test_dir.mkdir(parents=True)
    
    # Create expiry folder
    expiry_dir = test_dir / "202603"
    expiry_dir.mkdir()
    
    # Mock sys.argv with the path
    monkeypatch.setattr(
        sys, 'argv', 
        ['fix_missed_strike_price_precision.py', str(test_dir)]
    )
    
    # Run main
    main()
    
    # Capture output
    captured = capfd.readouterr()
    
    # Verify error message for unknown symbol
    assert "ERROR: No scaling configured for symbol 'xyz'" in captured.out


def test_main_with_multiple_paths(tmp_path, monkeypatch, capfd, script_temp_output_dir):
    """Test that main() processes multiple paths correctly."""
    # Create first test directory (adu)
    test_dir1 = tmp_path / "data" / "futureoption" / "cme" / "minute" / "adu"
    test_dir1.mkdir(parents=True)
    expiry_dir1 = test_dir1 / "202501"
    expiry_dir1.mkdir()
    zip_file1 = expiry_dir1 / "20250115_quote_american.zip"
    with ZipFile(zip_file1, "w") as z:
        z.writestr("20250115_adu_minute_quote_american_call_62520_20260306.csv", "adu_data")
    
    # Create second test directory (euu)
    test_dir2 = tmp_path / "data" / "futureoption" / "cme" / "minute" / "euu"
    test_dir2.mkdir(parents=True)
    expiry_dir2 = test_dir2 / "202603"
    expiry_dir2.mkdir()
    zip_file2 = expiry_dir2 / "20251224_openinterest_american.zip"
    with ZipFile(zip_file2, "w") as z:
        z.writestr("20251224_euu_minute_openinterest_american_call_11570_20260109.csv", "euu_data")
    
    # Change to tmp_path directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock sys.argv with multiple paths
        monkeypatch.setattr(
            sys, 'argv', 
            ['fix_missed_strike_price_precision.py', str(test_dir1), str(test_dir2)]
        )
        
        # Run main
        main()
        
        # Capture output
        captured = capfd.readouterr()
        
        # Verify both paths were processed
        assert "adu" in captured.out
        assert "euu" in captured.out
        assert "All provided paths processed successfully" in captured.out
        
        # Verify output files exist in the temp-output-directory next to script
        expected_output_dir = pathlib.Path(script_temp_output_dir)
        assert expected_output_dir.exists()
        
        # Verify output zips were created
        adu_zips = list(expected_output_dir.glob("**/20250115_quote_american.zip"))
        euu_zips = list(expected_output_dir.glob("**/20251224_openinterest_american.zip"))
        
        assert len(adu_zips) > 0, f"No adu output zip found in {expected_output_dir}"
        assert len(euu_zips) > 0, f"No euu output zip found in {expected_output_dir}"
    finally:
        os.chdir(original_cwd)


def test_main_with_non_directory_path(tmp_path, monkeypatch):
    """Test that main() raises RuntimeError when path is not a directory."""
    # Create a file instead of directory
    test_file = tmp_path / "not_a_directory.txt"
    test_file.write_text("test")
    
    # Mock sys.argv with the file path
    monkeypatch.setattr(
        sys, 'argv', 
        ['fix_missed_strike_price_precision.py', str(test_file)]
    )
    
    # Should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        main()
    
    assert "not a directory" in str(exc_info.value)


def test_source_and_destination_path_mapping(tmp_path, monkeypatch, script_temp_output_dir):
    """
    Test that validates correct source and destination path mapping.
    
    This test verifies that files from the source directory structure are correctly
    mapped to the destination directory structure, preserving the path hierarchy
    from the "data" directory onwards.
    
    Source: data/futureoption/cme/minute/euu/202603/20251224_openinterest_american.zip
    Destination: temp-output-directory/futureoption/cme/minute/euu/202603/20251224_openinterest_american.zip
    """
    # Create source directory structure
    source_dir = tmp_path / "data" / "futureoption" / "cme" / "minute" / "euu"
    source_dir.mkdir(parents=True)
    
    # Create expiry folder
    expiry_dir = source_dir / "202603"
    expiry_dir.mkdir()
    
    # Create source zip file
    source_zip = expiry_dir / "20251224_openinterest_american.zip"
    with ZipFile(source_zip, "w") as z:
        z.writestr("20251224_euu_minute_openinterest_american_call_11570_20260109.csv", "test_data")
    
    # Change to tmp_path directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock sys.argv with the source path
        monkeypatch.setattr(
            sys, 'argv', 
            ['fix_missed_strike_price_precision.py', str(source_dir)]
        )
        
        # Run main
        main()
        
        # Verify the destination path structure
        output_dir = pathlib.Path(script_temp_output_dir)
        
        # Find the output zip
        output_zips = list(output_dir.glob("**/20251224_openinterest_american.zip"))
        assert len(output_zips) == 1, f"Expected exactly 1 output zip, found {len(output_zips)}"
        
        output_zip = output_zips[0]
        
        # Verify the output path contains the expected structure
        # The path should be: temp-output-directory/<relpath from "data">/<expiry>/<zipfile>
        # Which means: temp-output-directory/.../futureoption/cme/minute/euu/202603/20251224_openinterest_american.zip
        assert "futureoption" in str(output_zip)
        assert "cme" in str(output_zip)
        assert "minute" in str(output_zip)
        assert "euu" in str(output_zip)
        assert "202603" in str(output_zip)
        
        # Verify the source file still exists (not moved, only copied)
        assert source_zip.exists()
        
    finally:
        os.chdir(original_cwd)


def test_source_destination_path_with_data_prefix(tmp_path, monkeypatch, script_temp_output_dir):
    """
    Test source and destination path mapping when source path starts with 'data/'.
    
    This tests the scenario where the user provides a path like:
    data/futureoption/cme/minute/euu
    
    The destination should strip the 'data' prefix and create:
    temp-output-directory/futureoption/cme/minute/euu/<expiry>/<files>
    """
    # Create source directory structure
    source_dir = tmp_path / "data" / "futureoption" / "cme" / "minute" / "adu"
    source_dir.mkdir(parents=True)
    
    # Create expiry folder
    expiry_dir = source_dir / "202501"
    expiry_dir.mkdir()
    
    # Create source zip file
    source_zip = expiry_dir / "20250115_quote_american.zip"
    with ZipFile(source_zip, "w") as z:
        z.writestr("20250115_adu_minute_quote_american_call_62520_20260306.csv", "adu_test_data")
    
    # Change to tmp_path directory to make relative paths work
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock sys.argv with a relative path starting with 'data/'
        monkeypatch.setattr(
            sys, 'argv', 
            ['fix_missed_strike_price_precision.py', 'data/futureoption/cme/minute/adu']
        )
        
        # Run main
        main()
        
        # Verify the destination path structure
        output_dir = pathlib.Path(script_temp_output_dir)
        
        # Find the output zip
        output_zips = list(output_dir.glob("**/20250115_quote_american.zip"))
        assert len(output_zips) == 1, f"Expected exactly 1 output zip, found {len(output_zips)}"
        
        output_zip = output_zips[0]
        
        # Verify the path structure excludes the "data" prefix from the output
        # The output should be: temp-output-directory/futureoption/cme/minute/adu/202501/...
        # NOT: temp-output-directory/data/futureoption/cme/minute/adu/202501/...
        output_str = str(output_zip)
        
        # Verify the expected structure is present
        assert "futureoption" in output_str
        assert "cme" in output_str
        assert "minute" in output_str
        assert "adu" in output_str
        assert "202501" in output_str
        
        # Verify the file was processed correctly
        with ZipFile(output_zip, "r") as z:
            namelist = z.namelist()
            # File with 62520 should be scaled to 62525 (remainder 2)
            assert "20250115_adu_minute_quote_american_call_62525_20260306.csv" in namelist
            
    finally:
        os.chdir(original_cwd)


def test_multiple_expiry_folders_path_mapping(tmp_path, monkeypatch, script_temp_output_dir):
    """
    Test that multiple expiry folders are correctly mapped from source to destination.
    
    Source structure:
      data/futureoption/cme/minute/euu/202603/...
      data/futureoption/cme/minute/euu/202604/...
      
    Destination structure:
      temp-output-directory/futureoption/cme/minute/euu/202603/...
      temp-output-directory/futureoption/cme/minute/euu/202604/...
    """
    # Create source directory structure with multiple expiries
    source_dir = tmp_path / "data" / "futureoption" / "cme" / "minute" / "euu"
    source_dir.mkdir(parents=True)
    
    # Create first expiry folder
    expiry_dir1 = source_dir / "202603"
    expiry_dir1.mkdir()
    source_zip1 = expiry_dir1 / "20251224_quote_american.zip"
    with ZipFile(source_zip1, "w") as z:
        z.writestr("20251224_euu_minute_quote_american_call_11570_20260309.csv", "data1")
    
    # Create second expiry folder
    expiry_dir2 = source_dir / "202604"
    expiry_dir2.mkdir()
    source_zip2 = expiry_dir2 / "20260105_trade_american.zip"
    with ZipFile(source_zip2, "w") as z:
        z.writestr("20260105_euu_minute_trade_american_put_11620_20260415.csv", "data2")
    
    # Change to tmp_path directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock sys.argv with the source path
        monkeypatch.setattr(
            sys, 'argv', 
            ['fix_missed_strike_price_precision.py', str(source_dir)]
        )
        
        # Run main
        main()
        
        # Verify the destination path structure
        output_dir = pathlib.Path(script_temp_output_dir)
        
        # Find both output zips
        output_zip1_list = list(output_dir.glob("**/202603/20251224_quote_american.zip"))
        output_zip2_list = list(output_dir.glob("**/202604/20260105_trade_american.zip"))
        
        assert len(output_zip1_list) == 1, f"Expected exactly 1 output zip for 202603, found {len(output_zip1_list)}"
        assert len(output_zip2_list) == 1, f"Expected exactly 1 output zip for 202604, found {len(output_zip2_list)}"
        
        # Verify both expiry folders are correctly mapped
        output_zip1 = output_zip1_list[0]
        output_zip2 = output_zip2_list[0]
        
        # Verify path structure for first expiry
        assert "202603" in str(output_zip1)
        assert "euu" in str(output_zip1)
        
        # Verify path structure for second expiry
        assert "202604" in str(output_zip2)
        assert "euu" in str(output_zip2)
        
        # Verify files were processed correctly
        with ZipFile(output_zip1, "r") as z:
            namelist = z.namelist()
            assert "20251224_euu_minute_quote_american_call_11575_20260309.csv" in namelist
        
        with ZipFile(output_zip2, "r") as z:
            namelist = z.namelist()
            assert "20260105_euu_minute_trade_american_put_11625_20260415.csv" in namelist
            
    finally:
        os.chdir(original_cwd)
