#!/usr/bin/env python3
"""
Test Script for Enhanced RAFT Training System

This script demonstrates all the enhanced RAFT training features:
1. Interactive annotation interface
2. Automated quality assessment
3. Progressive training curriculum

Run this to see the complete RAFT training workflow in action.
"""

import json
from pathlib import Path
from src.training.raft_collector import RAFTDataCollector
from src.training.quality_scorer import QualityScorer
from src.training.progressive_trainer import ProgressiveRAFTTrainer
from src.training.raft_annotator import RAFTAnnotator

def create_sample_training_examples():
    """Create sample RAFT training examples for demonstration"""
    print("📊 Creating sample RAFT training examples...")

    collector = RAFTDataCollector(
        output_dir="training_data/collected/demo",
        enabled=True
    )

    # Sample automotive requirements with varying complexity and context
    sample_requirements = [
        {
            "id": "SR_DOOR_LOCK_001",
            "text": "The door lock ECU shall detect mechanical failure within 100ms when the door is electronically locked",
            "type": "System Requirement",
            "table": True,
            "heading": "Door Control System",
            "info_list": [
                {
                    "id": "INFO_DOOR_MECHANICS",
                    "type": "Information",
                    "text": "Door locking mechanism uses solenoid actuator with position feedback sensor"
                }
            ],
            "interface_list": [
                {
                    "id": "IF_CAN_DOOR",
                    "type": "System Interface",
                    "text": "CAN bus interface for door control messages"
                }
            ]
        },
        {
            "id": "SR_ENGINE_TEMP_002",
            "text": "The engine cooling system shall activate fan at temperatures above 95°C",
            "type": "System Requirement",
            "table": True,
            "heading": "Thermal Management",
            "info_list": [
                {
                    "id": "INFO_COOLING_ARCH",
                    "type": "Information",
                    "text": "Cooling system uses dual radiator fans controlled by engine ECU"
                },
                {
                    "id": "INFO_TEMP_SENSORS",
                    "type": "Information",
                    "text": "Temperature sensors located at radiator inlet and engine block"
                }
            ],
            "interface_list": [
                {
                    "id": "IF_ECU_OUTPUTS",
                    "type": "System Interface",
                    "text": "ECU digital outputs for fan relay control"
                }
            ]
        },
        {
            "id": "SR_ADAS_VISION_003",
            "text": "The ADAS camera system shall detect pedestrian obstacles with >85% accuracy using RGB and IR sensors",
            "type": "System Requirement",
            "table": True,
            "heading": "Advanced Driver Assistance Systems",
            "info_list": [
                {
                    "id": "INFO_CAMERA_HARDWARE",
                    "type": "Information",
                    "text": "Camera system uses IMX390 sensor with 1440x1080 resolution"
                },
                {
                    "id": "INFO_COMPUTER_VISION",
                    "type": "Information",
                    "text": "Computer vision processing uses CNN-based pedestrian detection algorithm"
                },
                {
                    "id": "INFO_CALIBRATION",
                    "type": "Information",
                    "text": "Camera calibration performed during vehicle assembly using factory targets"
                }
            ],
            "interface_list": [
                {
                    "id": "IF_ETH_ADAS",
                    "type": "System Interface",
                    "text": "Ethernet interface for ADAS module communication"
                },
                {
                    "id": "IF_CAN_ADAS",
                    "type": "System Interface",
                    "text": "CAN bus for ADAS warning signals to dashboard"
                }
            ]
        }
    ]

    # Generate sample AI responses (simulate what would come from LLM)
    sample_responses = [
        """Test Case: TC_DOOR_LOCK_MECH_FAIL_001 - Mechanical Failure Detection
Preconditions:
- Door is electronically locked
- Mechanical locking mechanism is operational
Test Steps:
1. Simulate mechanical failure by disconnecting solenoid actuator
2. Measure time from failure to detection
Expected Result: Detection occurs within 100ms
Test Type: Functional Negative

Test Case: TC_DOOR_LOCK_POSITION_002 - Position Sensor Validation
Preconditions:
- Door locking system is powered and operational
Test Steps:
1. Alternate door between locked/unlocked states
2. Verify position sensor signals match mechanical position
Expected Result: Position signals are accurate within 5mm tolerance
Test Type: Functional""",

        """Test Case: TC_ENGINE_FAN_TEMP_001 - Temperature Threshold Activation
Preconditions:
- Engine cooling system is functioning normally
- Ambient temperature is below 30°C
Test Steps:
1. Gradually increase engine coolant temperature
2. Monitor fan activation at 95°C threshold
3. Verify fan speed increases appropriately
Expected Result: Fan activates smoothly at 95°C without hysteresis issues
Test Type: Functional

Test Case: TC_ENGINE_FAN_FAIL_002 - Fan Failure Detection
Preconditions:
- Cooling system has been running normally
Test Steps:
1. Simulate radiator fan failure
2. Verify ECU detects fan failure and illuminates warning
Expected Result: Warning is displayed within 5 seconds of failure
Test Type: Safety""",

        """Test Case: TC_ADAS_PEDESTRIAN_ACCURACY_001 - Pedestrian Detection Accuracy
Preconditions:
- ADAS system is calibrated and operational
- Test environment has controlled pedestrian mock-ups
Test Steps:
1. Present pedestrian mock-ups at various distances and lighting conditions
2. Count successful detections vs false positives/negatives
3. Calculate detection accuracy percentage
Expected Result: Accuracy exceeds 85% across all test scenarios
Test Type: Functional AI/ML

Test Case: TC_ADAS_PEDESTRIAN_BOUNDARY_002 - Detection Boundary Conditions
Preconditions:
- Camera system has clear field of view
Test Steps:
1. Test pedestrian detection at maximum specified range
2. Test with various pedestrian sizes and orientations
3. Test under adverse weather conditions (rain, fog)
Expected Result: System correctly handles boundary conditions without false alarms
Test Type: Robustness"""
    ]

    # Collect examples
    for i, (req, response) in enumerate(zip(sample_requirements, sample_responses)):
        collector.collect_example(req, response, "llama3.1:8b")

        # For demo purposes, let's also create a basic annotation for one example
        if i == 0:
            example_path = Path("training_data/collected/demo") / f"raft_{req['id']}_annotated.json"
            if example_path.exists():
                with open(example_path, 'r', encoding='utf-8') as f:
                    example = json.load(f)

                # Add simulated annotation
                example['context_annotation'] = {
                    'oracle_context': ['HEADING', 'INFO_DOOR_MECHANICS', 'IF_CAN_DOOR'],
                    'distractor_context': [],
                    'quality_rating': 4,
                    'annotation_notes': 'Good example with clear interface and mechanical context'
                }
                example['validation_status'] = 'validated'
                example['annotation_timestamp'] = json.dumps(None)

                # Move to validated directory
                validated_path = Path("training_data/validated") / f"{req['id']}_annotated.json"
                validated_path.parent.mkdir(exist_ok=True)

                with open(validated_path, 'w', encoding='utf-8') as f:
                    json.dump(example, f, indent=2, ensure_ascii=False)

    print(f"✅ Created {len(sample_requirements)} sample training examples")

def demonstrate_quality_assessment():
    """Demonstrate the automated quality assessment system"""
    print("\n🔍 Demonstrating Quality Assessment...")

    quality_scorer = QualityScorer()

    # Assess example from validated directory
    validated_dir = Path("training_data/validated")
    if not validated_dir.exists():
        print("❌ No validated examples found")
        return

    json_files = list(validated_dir.glob("*_annotated.json"))
    if not json_files:
        print("❌ No annotated examples found")
        return

    # Load and assess first example
    with open(json_files[0], 'r', encoding='utf-8') as f:
        example = json.load(f)

    assessment = quality_scorer.assess_example_quality(example)

    print("Quality Assessment Results:")
    print(f"  Example ID: {assessment.example_id}")
    print(f"  Overall Score: {assessment.metrics.overall_score:.3f}")
    print(f"  Relevance: {assessment.metrics.relevance_score:.3f}")
    print(f"  Diversity: {assessment.metrics.context_diversity:.3f}")
    print(f"  Quantity: {assessment.metrics.context_quantity:.3f}")
    print(f"  Priority: {assessment.priority}")

    for rec in assessment.recommendations:
        print(f"  💡 {rec}")

    # Batch assessment
    print(f"\n📊 Batch Assessment Results:")
    batch_results = quality_scorer.batch_assess_quality("training_data/validated")
    print(f"  Total assessed: {batch_results['total_assessed']}")
    print(f"  Average score: {batch_results['average_score']:.3f}")
    print(f"  Average relevance: {batch_results['average_relevance']:.3f}")

def demonstrate_progressive_training():
    """Demonstrate the progressive training curriculum"""
    print("\n📚 Demonstrating Progressive Training Curriculum...")

    trainer = ProgressiveRAFTTrainer(
        validated_dir="training_data/validated",
        output_dir="training_data/models/demo_training"
    )

    # Get curriculum status
    status = trainer.get_curriculum_status()

    print("Curriculum Status:")
    print(f"  Current Phase: {status['current_phase']}")
    print(f"  Graduated Phases: {status['graduated_phases']}")
    print(f"  Total Examples: {status['total_examples']}")

    print("Examples per Phase:")
    for phase, count in status['examples_per_phase'].items():
        print(f"  {phase}: {count} examples")

    if status['recommendations']:
        print("Training Recommendations:")
        for rec in status['recommendations']:
            print(f"  💡 {rec}")

    # Start training (simulation)
    print("\n🚀 Starting Progressive Training Simulation...")
    training_results = trainer.start_curriculum_training("demo-progressive-model")

    print("Training Results Summary:")
    print(f"  Model: {training_results['model_name']}")
    print("  Phases Completed:")
    for phase in training_results.get('phases_completed', []):
        print(f"    • {phase['phase']} ({phase['examples_trained']} examples)")
    print(f"  Total Examples Trained: {training_results['total_examples_trained']}")
    print(f"  Final Performance Score: {training_results['final_performance_score']:.3f}")
    print(f"  Training Duration: {training_results['training_duration']:.2f}s")

    if training_results.get('issues_encountered'):
        print("Issues Encountered:")
        for issue in training_results['issues_encountered']:
            print(f"  ⚠️  {issue}")

def demonstrate_annotation_interface():
    """Demonstrate the annotation interface (non-interactive for script)"""
    print("\n🎯 Demonstrating Annotation Interface Structure...")

    # Note: The actual interactive interface requires user input
    # We'll show how it would work by displaying the structure

    collected_examples = list(Path("training_data/collected/demo").glob("raft_*.json"))
    unannotated = []

    for file_path in collected_examples:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                example = json.load(f)

            if 'context_annotation' not in example or not example['context_annotation'].get('quality_rating'):
                unannotated.append(file_path)
        except Exception:
            continue

    print(f"Found {len(unannotated)} unannotated examples that would be available for interactive annotation")
    print("Interactive annotation features:")
    print("  • Rich console interface with guided prompts")
    print("  • Tabular display of context items")
    print("  • Context relevance selection")
    print("  • Quality rating (1-5 scale)")
    print("  • Progress tracking")
    print("  • Keyboard interrupt handling")

    # To run interactive annotation:
    print("\nTo run interactive annotation, use:")
    print("  from src.training.raft_annotator import RAFTAnnotator")
    print("  annotator = RAFTAnnotator()")
    print("  annotator.annotate_examples(batch_size=3)")

def main():
    """Run all RAFT enhancement demonstrations"""
    print("🚀 Enhanced RAFT Training System Demonstration")
    print("=" * 60)

    try:
        # Step 1: Create sample data
        create_sample_training_examples()

        # Step 2: Demonstrate quality assessment
        demonstrate_quality_assessment()

        # Step 3: Demonstrate progressive training
        demonstrate_progressive_training()

        # Step 4: Show annotation interface structure
        demonstrate_annotation_interface()

        print(f"\n{'='*60}")
        print("✅ Enhanced RAFT Training System demonstration complete!")
        print("\nKey features demonstrated:")
        print("  1. 📊 Interactive annotation interface")
        print("  2. 🔍 Automated quality assessment")
        print("  3. 📈 Progressive training curriculum")
        print("  4. 🎯 Multi-dimensional quality scoring")
        print("  5. 📋 Curriculum-based training organization")

        print(f"\nNext steps:")
        print("  1. Run interactive annotation: python -c 'from src.training.raft_annotator import RAFTAnnotator; RAFTAnnotator().annotate_examples(batch_size=5)'")
        print("  2. Assess quality: python -c 'from src.training.quality_scorer import QualityScorer; QualityScorer().batch_assess_quality(\"training_data/validated\")'")
        print("  3. Train curriculum: python -c 'from src.training.progressive_trainer import ProgressiveRAFTTrainer; trainer = ProgressiveRAFTTrainer(); trainer.start_curriculum_training()'")

    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
