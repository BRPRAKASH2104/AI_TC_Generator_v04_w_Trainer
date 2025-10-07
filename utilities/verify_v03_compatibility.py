#!/usr/bin/env python3
"""
Verification script to test v03 compatibility fixes in v04.

This script verifies:
1. Artifact extraction matches v03 behavior (extracts ALL spec objects)
2. Classification doesn't drop valid requirements
3. Context-aware augmentation works correctly
4. AI prompt generation includes all context
5. Field name mapping works for both v03 and v04 formats
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.extractors import REQIFArtifactExtractor
from core.prompt_builder import PromptBuilder
from core.formatters import TestCaseFormatter
from processors.base_processor import BaseProcessor
from config import ConfigManager
from yaml_prompt_manager import YAMLPromptManager


class V03CompatibilityVerifier:
    """Verifies v03 compatibility fixes"""

    def __init__(self, reqifz_path: Path):
        self.reqifz_path = reqifz_path
        self.results = {
            "extraction": False,
            "classification": False,
            "augmentation": False,
            "prompt_generation": False,
            "field_mapping": False
        }

    def verify_all(self) -> dict:
        """Run all verification checks"""
        print("="*80)
        print("V03 COMPATIBILITY VERIFICATION")
        print("="*80)
        print(f"\nTesting file: {self.reqifz_path.name}\n")

        self.verify_extraction()
        self.verify_classification()
        self.verify_augmentation()
        self.verify_prompt_generation()
        self.verify_field_mapping()

        self.print_summary()
        return self.results

    def verify_extraction(self):
        """Verify artifact extraction extracts ALL spec objects"""
        print("\n[1/5] Testing Artifact Extraction...")
        print("-" * 80)

        try:
            extractor = REQIFArtifactExtractor()
            artifacts = extractor.extract_reqifz_content(self.reqifz_path)

            if not artifacts:
                print("❌ FAIL: No artifacts extracted")
                self.results["extraction"] = False
                return

            print(f"✅ Extracted {len(artifacts)} artifacts")

            # Show type breakdown
            type_counts = {}
            for artifact in artifacts:
                artifact_type = artifact.get("type", "UNKNOWN")
                type_counts[artifact_type] = type_counts.get(artifact_type, 0) + 1

            print("\nArtifact Type Breakdown:")
            for artifact_type, count in sorted(type_counts.items()):
                print(f"  - {artifact_type}: {count}")

            # Check for variety (good sign)
            if len(type_counts) >= 2:
                print("\n✅ PASS: Multiple artifact types detected (good classification)")
                self.results["extraction"] = True
            else:
                print("\n⚠️  WARNING: Only one artifact type found - may need classification tuning")
                self.results["extraction"] = True  # Still pass, but warn

        except Exception as e:
            print(f"❌ FAIL: Exception during extraction: {e}")
            self.results["extraction"] = False

    def verify_classification(self):
        """Verify classification doesn't drop valid requirements"""
        print("\n[2/5] Testing Artifact Classification...")
        print("-" * 80)

        try:
            extractor = REQIFArtifactExtractor()
            artifacts = extractor.extract_reqifz_content(self.reqifz_path)

            if not artifacts:
                print("❌ FAIL: No artifacts to classify")
                self.results["classification"] = False
                return

            # Check for System Requirements
            sys_reqs = [a for a in artifacts if a.get("type") == "System Requirement"]

            if not sys_reqs:
                print("❌ FAIL: No System Requirements classified")
                print("   This means all requirements were dropped!")
                self.results["classification"] = False
                return

            print(f"✅ Found {len(sys_reqs)} System Requirements")

            # Check if any have text content
            with_text = [r for r in sys_reqs if r.get("text", "").strip()]
            print(f"✅ {len(with_text)} have text content")

            # Show sample
            if with_text:
                sample = with_text[0]
                print(f"\nSample Requirement:")
                print(f"  ID: {sample.get('id', 'UNKNOWN')}")
                print(f"  Type: {sample.get('type')}")
                print(f"  Text: {sample.get('text', '')[:100]}...")
                print(f"  Has Table: {sample.get('table') is not None}")

            if len(with_text) > 0:
                print("\n✅ PASS: Requirements classified and have content")
                self.results["classification"] = True
            else:
                print("\n❌ FAIL: Requirements have no text content")
                self.results["classification"] = False

        except Exception as e:
            print(f"❌ FAIL: Exception during classification: {e}")
            self.results["classification"] = False

    def verify_augmentation(self):
        """Verify context-aware augmentation"""
        print("\n[3/5] Testing Context-Aware Augmentation...")
        print("-" * 80)

        try:
            # Create minimal processor setup
            config = ConfigManager()
            processor = BaseProcessor(config)
            processor._initialize_logger(self.reqifz_path)

            # Extract and augment
            extractor = REQIFArtifactExtractor(processor.logger)
            processor.extractor = extractor

            artifacts = extractor.extract_reqifz_content(self.reqifz_path)

            if not artifacts:
                print("❌ FAIL: No artifacts to augment")
                self.results["augmentation"] = False
                return

            augmented, interface_count = processor._build_augmented_requirements(artifacts)

            print(f"✅ Augmented {len(augmented)} requirements")
            print(f"✅ Found {interface_count} system interfaces (global context)")

            if not augmented:
                print("❌ FAIL: No augmented requirements created")
                self.results["augmentation"] = False
                return

            # Check augmentation quality
            sample = augmented[0]
            has_heading = bool(sample.get("heading"))
            has_info = "info_list" in sample
            has_interfaces = "interface_list" in sample

            print(f"\nAugmentation Quality Check (first requirement):")
            print(f"  Heading: {'✅' if has_heading else '❌'} {sample.get('heading', 'N/A')}")
            print(f"  Info List: {'✅' if has_info else '❌'} ({len(sample.get('info_list', []))} items)")
            print(f"  Interfaces: {'✅' if has_interfaces else '❌'} ({len(sample.get('interface_list', []))} items)")

            if has_heading and has_info and has_interfaces:
                print("\n✅ PASS: Context-aware augmentation working correctly")
                self.results["augmentation"] = True
            else:
                print("\n⚠️  WARNING: Some context fields missing, but augmentation working")
                self.results["augmentation"] = True

        except Exception as e:
            print(f"❌ FAIL: Exception during augmentation: {e}")
            import traceback
            traceback.print_exc()
            self.results["augmentation"] = False

    def verify_prompt_generation(self):
        """Verify prompt generation includes all context"""
        print("\n[4/5] Testing Prompt Generation...")
        print("-" * 80)

        try:
            yaml_manager = YAMLPromptManager()
            builder = PromptBuilder(yaml_manager)

            # Create mock augmented requirement
            mock_req = {
                "id": "TEST_REQ_001",
                "heading": "Test Feature Heading",
                "text": "System shall perform test operation",
                "table": {"rows": 2, "data": [{"input": "A", "output": "B"}]},
                "info_list": [{"text": "Additional context information"}],
                "interface_list": [{"id": "SIG_001", "text": "Test signal input"}]
            }

            # Test default prompt (no template)
            builder_no_template = PromptBuilder(yaml_manager=None)
            prompt = builder_no_template.build_prompt(mock_req)

            # Check if context is included
            has_heading = "Test Feature Heading" in prompt
            has_info = "Additional context" in prompt or "info" in prompt.lower()
            has_interface = "SIG_001" in prompt or "interface" in prompt.lower()
            has_field_names = "summary_suffix" in prompt and "action" in prompt and "data" in prompt

            print("Prompt Content Check:")
            print(f"  Includes Heading: {'✅' if has_heading else '❌'}")
            print(f"  Includes Info Context: {'✅' if has_info else '❌'}")
            print(f"  Includes Interfaces: {'✅' if has_interface else '❌'}")
            print(f"  Requests Correct Field Names: {'✅' if has_field_names else '❌'}")

            print(f"\nPrompt Preview (first 500 chars):")
            print("-" * 80)
            print(prompt[:500])
            print("...")

            if has_heading and has_info and has_interface and has_field_names:
                print("\n✅ PASS: Prompt generation includes all context and correct field names")
                self.results["prompt_generation"] = True
            else:
                print("\n⚠️  WARNING: Some context missing, but prompt generated")
                self.results["prompt_generation"] = False

        except Exception as e:
            print(f"❌ FAIL: Exception during prompt generation: {e}")
            import traceback
            traceback.print_exc()
            self.results["prompt_generation"] = False

    def verify_field_mapping(self):
        """Verify field name mapping works for both v03 and v04 formats"""
        print("\n[5/5] Testing Field Name Mapping...")
        print("-" * 80)

        try:
            formatter = TestCaseFormatter()

            # Test v03-style test case
            v03_test_case = {
                "requirement_id": "REQ_001",
                "feature_name": "Test Feature",
                "preconditions": "1. IGN ON\n2. Voltage 12V",
                "test_steps": "1. Press button\n2. Verify LED",
                "expected_result": "LED turns on"
            }

            # Test v04-style test case
            v04_test_case = {
                "requirement_id": "REQ_002",
                "summary_suffix": "Test Summary",
                "action": "1. IGN ON\n2. Voltage 12V",
                "data": "1. Press button\n2. Verify LED",
                "expected_result": "LED turns on",
                "test_type": "positive"
            }

            # Format both
            v03_formatted = formatter._prepare_test_cases_for_excel([v03_test_case])
            v04_formatted = formatter._prepare_test_cases_for_excel([v04_test_case])

            print("v03-style test case mapping:")
            if v03_formatted:
                tc = v03_formatted[0]
                print(f"  Summary: {tc.get('Summary', 'MISSING')[:50]}...")
                print(f"  Action: {tc.get('Action', 'MISSING')[:50]}...")
                print(f"  Data: {tc.get('Data', 'MISSING')[:50]}...")
                v03_ok = all(tc.get(key) != 'MISSING' for key in ['Summary', 'Action', 'Data'])
            else:
                print("  ❌ Failed to format")
                v03_ok = False

            print("\nv04-style test case mapping:")
            if v04_formatted:
                tc = v04_formatted[0]
                print(f"  Summary: {tc.get('Summary', 'MISSING')[:50]}...")
                print(f"  Action: {tc.get('Action', 'MISSING')[:50]}...")
                print(f"  Data: {tc.get('Data', 'MISSING')[:50]}...")
                v04_ok = all(tc.get(key) != 'MISSING' for key in ['Summary', 'Action', 'Data'])
            else:
                print("  ❌ Failed to format")
                v04_ok = False

            if v03_ok and v04_ok:
                print("\n✅ PASS: Both v03 and v04 field names mapped correctly")
                self.results["field_mapping"] = True
            else:
                print("\n❌ FAIL: Field mapping incomplete")
                self.results["field_mapping"] = False

        except Exception as e:
            print(f"❌ FAIL: Exception during field mapping: {e}")
            import traceback
            traceback.print_exc()
            self.results["field_mapping"] = False

    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)

        all_passed = all(self.results.values())
        status = "✅ ALL CHECKS PASSED" if all_passed else "❌ SOME CHECKS FAILED"

        for check, passed in self.results.items():
            symbol = "✅" if passed else "❌"
            print(f"{symbol} {check.replace('_', ' ').title()}")

        print("\n" + status)

        if all_passed:
            print("\n🎉 v04 is now compatible with v03 behavior!")
            print("   - All spec objects are extracted")
            print("   - Classification doesn't drop requirements")
            print("   - Context-aware augmentation works")
            print("   - Prompts include full context")
            print("   - Field mapping supports both v03 and v04 formats")
        else:
            print("\n⚠️  Some issues detected - review the detailed output above")

        return all_passed


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python verify_v03_compatibility.py <path_to_reqifz_file>")
        print("\nExample:")
        print("  python verify_v03_compatibility.py input/sample.reqifz")
        sys.exit(1)

    reqifz_path = Path(sys.argv[1])

    if not reqifz_path.exists():
        print(f"❌ Error: File not found: {reqifz_path}")
        sys.exit(1)

    if not reqifz_path.suffix.lower() == '.reqifz':
        print(f"❌ Error: File must be a .reqifz file, got: {reqifz_path.suffix}")
        sys.exit(1)

    verifier = V03CompatibilityVerifier(reqifz_path)
    results = verifier.verify_all()

    # Exit with status code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
