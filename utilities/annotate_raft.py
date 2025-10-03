#!/usr/bin/env python3
"""
Interactive RAFT Annotation Tool

This utility provides an interactive interface for annotating RAFT training data.
Experts can mark context as oracle (relevant) or distractor (irrelevant) and
validate/reject generated test cases.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def annotate_example(example_path: Path) -> None:
    """
    Interactively annotate a RAFT example.

    Args:
        example_path: Path to the RAFT example JSON file
    """
    with open(example_path, encoding="utf-8") as f:
        data = json.load(f)

    print("\n" + "=" * 70)
    print(f"📝 Annotating: {data['requirement_id']}")
    print("=" * 70)
    print(f"\n📋 Requirement: {data['requirement_text'][:200]}...")
    print(f"\n📁 Heading: {data['heading']}")

    # Show retrieved context
    print("\n🔍 Retrieved Context:")
    ctx = data["retrieved_context"]

    print(f"\n  Heading: {ctx['heading']['text']}")

    print(f"\n  Info Artifacts ({len(ctx['info_artifacts'])}):")
    for i, info in enumerate(ctx['info_artifacts'], 1):
        text = info['text'][:80] + "..." if len(info['text']) > 80 else info['text']
        print(f"    [{i}] {info['id']}: {text}")

    print(f"\n  Interfaces ({len(ctx['interfaces'])}):")
    for i, iface in enumerate(ctx['interfaces'], 1):
        text = iface['text'][:80] + "..." if len(iface['text']) > 80 else iface['text']
        print(f"    [{i}] {iface['id']}: {text}")

    # Show generated test cases
    tc_preview = data['generated_test_cases'][:500] + "..." if len(data['generated_test_cases']) > 500 else data['generated_test_cases']
    print(f"\n✨ Generated Test Cases:\n{tc_preview}")

    # Interactive annotation
    print("\n" + "=" * 70)
    print("📊 Annotation")
    print("=" * 70)

    # Quality rating
    print("\n1️⃣ Rate test case quality (1-5):")
    print("   5 = Excellent, production-ready")
    print("   4 = Good, minor edits needed")
    print("   3 = Acceptable, needs revision")
    print("   2 = Poor, major issues")
    print("   1 = Unusable")
    while True:
        try:
            quality = int(input("   Rating: "))
            if 1 <= quality <= 5:
                break
            print("   Please enter a number between 1 and 5")
        except ValueError:
            print("   Please enter a valid number")

    # Validation status
    print("\n2️⃣ Validation status:")
    print("   [1] Validated (accept)")
    print("   [2] Rejected")
    while True:
        status_choice = input("   Choice: ")
        if status_choice in ["1", "2"]:
            break
        print("   Please enter 1 or 2")

    status = "validated" if status_choice == "1" else "rejected"

    # Context annotation
    oracle_ids = []
    distractor_ids = []

    print("\n3️⃣ Annotate context relevance:")
    print("   Oracle (y) = Relevant, helped generate good test cases")
    print("   Distractor (n) = Irrelevant, not useful for this requirement")
    print("   Skip (s) = Uncertain, skip this item")

    # Heading
    heading_text = ctx['heading']['text'][:40] + "..." if len(ctx['heading']['text']) > 40 else ctx['heading']['text']
    choice = input(f"\n   Heading '{heading_text}' - Oracle? (y/n/s): ").lower()
    if choice == 'y':
        oracle_ids.append("HEADING")
    elif choice == 'n':
        distractor_ids.append("HEADING")

    # Info artifacts
    if ctx['info_artifacts']:
        print("\n   Info Artifacts:")
        for info in ctx['info_artifacts']:
            text = info['text'][:60] + "..." if len(info['text']) > 60 else info['text']
            choice = input(f"     {info['id']}: {text}\n     Oracle? (y/n/s): ").lower()
            if choice == 'y':
                oracle_ids.append(info['id'])
            elif choice == 'n':
                distractor_ids.append(info['id'])

    # Interfaces
    if ctx['interfaces']:
        print("\n   Interfaces:")
        for iface in ctx['interfaces']:
            text = iface['text'][:60] + "..." if len(iface['text']) > 60 else iface['text']
            choice = input(f"     {iface['id']}: {text}\n     Oracle? (y/n/s): ").lower()
            if choice == 'y':
                oracle_ids.append(iface['id'])
            elif choice == 'n':
                distractor_ids.append(iface['id'])

    # Notes
    print("\n4️⃣ Annotation notes (optional):")
    print("   (Press Enter to skip)")
    notes = input("   Notes: ")

    # Annotator name
    print("\n5️⃣ Your name/ID:")
    annotated_by = input("   Annotator: ")

    # Update annotation
    data["context_annotation"] = {
        "oracle_context": oracle_ids,
        "distractor_context": distractor_ids,
        "annotation_notes": notes,
        "quality_rating": quality
    }
    data["validation_status"] = status
    data["annotated_by"] = annotated_by
    data["annotation_timestamp"] = datetime.now().isoformat()

    # Save
    with open(example_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Move to appropriate directory
    dest_dir = Path("training_data") / status
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / example_path.name

    # Handle existing file
    if dest_path.exists():
        dest_path = dest_dir / f"{example_path.stem}_v{datetime.now().strftime('%H%M%S')}{example_path.suffix}"

    example_path.rename(dest_path)

    print(f"\n✅ Annotated and moved to: {dest_path}")

    # Summary
    print("\n📊 Annotation Summary:")
    print(f"   Quality: {quality}/5")
    print(f"   Status: {status}")
    print(f"   Oracle context items: {len(oracle_ids)}")
    print(f"   Distractor context items: {len(distractor_ids)}")


def batch_annotate(collected_dir: Path = Path("training_data/collected")) -> None:
    """
    Batch annotate all pending RAFT examples.

    Args:
        collected_dir: Directory containing collected examples
    """
    if not collected_dir.exists():
        print(f"❌ Directory not found: {collected_dir}")
        print("   Please ensure RAFT data collection is enabled and examples have been collected.")
        return

    pending_files = sorted(collected_dir.glob("raft_*.json"))

    if not pending_files:
        print(f"✅ No pending examples found in {collected_dir}")
        return

    print(f"\n📊 Found {len(pending_files)} examples to annotate")
    print("=" * 70)

    for i, file_path in enumerate(pending_files, 1):
        print(f"\n{'='*70}")
        print(f"Progress: {i}/{len(pending_files)}")

        try:
            annotate_example(file_path)
        except KeyboardInterrupt:
            print("\n\n⚠️  Annotation interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error annotating {file_path.name}: {e}")
            cont = input("\nContinue with next example? (y/n): ")
            if cont.lower() != 'y':
                break
            continue

        if i < len(pending_files):
            cont = input("\n➡️  Continue to next? (y/n): ")
            if cont.lower() != 'y':
                break

    print("\n✅ Annotation session complete!")


def show_stats() -> None:
    """Show statistics on RAFT data collection and annotation"""
    base_dir = Path("training_data")

    if not base_dir.exists():
        print("❌ training_data directory not found")
        return

    collected_dir = base_dir / "collected"
    validated_dir = base_dir / "validated"
    rejected_dir = base_dir / "rejected"

    stats = {
        "collected": len(list(collected_dir.glob("raft_*.json"))) if collected_dir.exists() else 0,
        "validated": len(list(validated_dir.glob("raft_*.json"))) if validated_dir.exists() else 0,
        "rejected": len(list(rejected_dir.glob("raft_*.json"))) if rejected_dir.exists() else 0
    }

    total = stats["collected"] + stats["validated"] + stats["rejected"]
    annotated = stats["validated"] + stats["rejected"]

    print("\n📊 RAFT Data Statistics")
    print("=" * 50)
    print(f"  Total examples: {total}")
    print(f"  Pending annotation: {stats['collected']}")
    print(f"  Validated: {stats['validated']}")
    print(f"  Rejected: {stats['rejected']}")
    print(f"  Annotation progress: {annotated}/{total} ({100*annotated/total if total > 0 else 0:.1f}%)")
    print("=" * 50)


def main():
    """Main entry point for annotation tool"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stats":
            show_stats()
            return
        elif sys.argv[1] == "--help":
            print("\nRAFT Annotation Tool")
            print("=" * 50)
            print("\nUsage:")
            print("  python annotate_raft.py             - Annotate all pending examples")
            print("  python annotate_raft.py --stats     - Show statistics")
            print("  python annotate_raft.py --help      - Show this help")
            print("\nAnnotation Guide:")
            print("  Oracle context: Relevant information that helps generate good test cases")
            print("  Distractor context: Irrelevant information that doesn't contribute")
            print("\nQuality Ratings:")
            print("  5 = Excellent, production-ready")
            print("  4 = Good, minor edits needed")
            print("  3 = Acceptable, needs revision")
            print("  2 = Poor, major issues")
            print("  1 = Unusable")
            print("=" * 50)
            return

    batch_annotate()


if __name__ == "__main__":
    main()
