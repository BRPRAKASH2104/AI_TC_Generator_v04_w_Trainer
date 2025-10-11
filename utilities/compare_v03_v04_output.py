#!/usr/bin/env python3
"""
Compare v03 CSV output with v04 Excel output to verify compatibility.

This script checks:
1. Column names match exactly
2. Column order matches exactly
3. Default values match (Test Type, Issue Type, etc.)
4. Data formatting matches (Summary format, etc.)
"""

import sys
from pathlib import Path

import pandas as pd


def compare_outputs(v03_csv: Path, v04_xlsx: Path):
    """Compare v03 CSV and v04 Excel outputs"""
    print("=" * 80)
    print("V03 vs V04 OUTPUT COMPARISON")
    print("=" * 80)
    print(f"\nv03 file: {v03_csv.name}")
    print(f"v04 file: {v04_xlsx.name}")

    # Read both files
    try:
        v03_df = pd.read_csv(v03_csv, encoding="utf-8-sig")
        v04_df = pd.read_excel(v04_xlsx, sheet_name="Test Cases")
    except Exception as e:
        print(f"\n❌ Error reading files: {e}")
        return False

    print(f"\nv03 test cases: {len(v03_df)}")
    print(f"v04 test cases: {len(v04_df)}")

    # Compare columns
    v03_cols = list(v03_df.columns)
    v04_cols = list(v04_df.columns)

    print("\n[1/5] Column Name Comparison")
    print("-" * 80)
    print(f"v03 columns ({len(v03_cols)}): {v03_cols}")
    print(f"v04 columns ({len(v04_cols)}): {v04_cols}")

    if v03_cols == v04_cols:
        print("✅ PASS: Column names match exactly")
        cols_match = True
    else:
        print("❌ FAIL: Column names don't match")
        missing_in_v04 = set(v03_cols) - set(v04_cols)
        extra_in_v04 = set(v04_cols) - set(v03_cols)
        if missing_in_v04:
            print(f"  Missing in v04: {missing_in_v04}")
        if extra_in_v04:
            print(f"  Extra in v04: {extra_in_v04}")
        cols_match = False

    # Compare default values
    print("\n[2/5] Default Values Comparison")
    print("-" * 80)

    if len(v03_df) > 0 and len(v04_df) > 0:
        v03_sample = v03_df.iloc[0]
        v04_sample = v04_df.iloc[0]

        defaults_to_check = [
            "Test Type",
            "Issue Type",
            "Project Key",
            "Assignee",
            "Planned Execution",
            "Test Case Type",
            "Components",
            "Labels",
        ]

        defaults_match = True
        for col in defaults_to_check:
            if col in v03_cols and col in v04_cols:
                v03_val = v03_sample[col]
                v04_val = v04_sample[col]
                match = v03_val == v04_val
                symbol = "✅" if match else "❌"
                print(f"{symbol} {col:20s}: v03='{v03_val}' vs v04='{v04_val}'")
                if not match:
                    defaults_match = False

        if defaults_match:
            print("\n✅ PASS: Default values match")
        else:
            print("\n❌ FAIL: Some default values don't match")
    else:
        print("⚠️  SKIP: No test cases to compare")
        defaults_match = True

    # Compare Summary format
    print("\n[3/5] Summary Format Comparison")
    print("-" * 80)

    if len(v03_df) > 0 and len(v04_df) > 0:
        v03_summary = v03_df.iloc[0]["Summary"]
        v04_summary = v04_df.iloc[0]["Summary"]

        print(f"v03 Summary: {v03_summary}")
        print(f"v04 Summary: {v04_summary}")

        # v03 format is [feature_name]
        v03_has_brackets = v03_summary.startswith("[") and v03_summary.endswith("]")
        v04_has_brackets = v04_summary.startswith("[") and v04_summary.endswith("]")

        if v03_has_brackets and v04_has_brackets:
            print("✅ PASS: Both use [feature_name] format")
            summary_match = True
        else:
            print("❌ FAIL: Summary format doesn't match")
            summary_match = False
    else:
        print("⚠️  SKIP: No test cases to compare")
        summary_match = True

    # Check for Feature Group column
    print("\n[4/5] Feature Group Column Check")
    print("-" * 80)

    if "Feature Group" in v03_cols:
        if "Feature Group" in v04_cols:
            print("✅ PASS: Feature Group column exists in v04")
            feature_group_ok = True
        else:
            print("❌ FAIL: Feature Group column missing in v04")
            feature_group_ok = False
    else:
        print("⚠️  WARNING: Feature Group not in v03")
        feature_group_ok = True

    # Check LinkTest column name
    print("\n[5/5] LinkTest Column Name Check")
    print("-" * 80)

    if "LinkTest" in v03_cols:
        if "LinkTest" in v04_cols:
            print("✅ PASS: LinkTest column name matches")
            linktest_ok = True
        elif "Tests" in v04_cols:
            print("❌ FAIL: v04 uses 'Tests' instead of 'LinkTest'")
            linktest_ok = False
        else:
            print("❌ FAIL: LinkTest column missing in v04")
            linktest_ok = False
    else:
        print("⚠️  WARNING: LinkTest not in v03")
        linktest_ok = True

    # Summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    all_checks = [cols_match, defaults_match, summary_match, feature_group_ok, linktest_ok]

    print(f"{'✅' if cols_match else '❌'} Column names match")
    print(f"{'✅' if defaults_match else '❌'} Default values match")
    print(f"{'✅' if summary_match else '❌'} Summary format matches")
    print(f"{'✅' if feature_group_ok else '❌'} Feature Group column present")
    print(f"{'✅' if linktest_ok else '❌'} LinkTest column name correct")

    if all(all_checks):
        print("\n✅ ALL CHECKS PASSED - v04 output matches v03 structure!")
        print("\nNote: v04 outputs XLSX (Excel) instead of CSV")
        print("      Column structure and data format are identical")
        return True
    else:
        print("\n❌ SOME CHECKS FAILED - v04 output differs from v03")
        return False


def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_v03_v04_output.py <v03_output.csv> <v04_output.xlsx>")
        print("\nExample:")
        print("  python compare_v03_v04_output.py output_v03.csv output_v04.xlsx")
        sys.exit(1)

    v03_file = Path(sys.argv[1])
    v04_file = Path(sys.argv[2])

    if not v03_file.exists():
        print(f"❌ Error: v03 file not found: {v03_file}")
        sys.exit(1)

    if not v04_file.exists():
        print(f"❌ Error: v04 file not found: {v04_file}")
        sys.exit(1)

    success = compare_outputs(v03_file, v04_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
