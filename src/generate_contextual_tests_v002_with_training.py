#!/usr/bin/env python3
"""
Training-Enhanced AI Test Case Generator v1.3
Extends v002 with integrated training data collection and custom model support

Key Features:
- Automatic training data collection during processing
- LoRA fine-tuning integration
- Custom model management
- Continuous improvement pipeline
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import OllamaConfig, StaticTestConfig, FileProcessingConfig, TrainingConfig
from training_data_collector import TrainingAwareFileProcessor, TrainingDataCollector
from custom_model_trainer import AutomotiveModelTrainer, LoRATrainingConfig, AutomatedTrainingPipeline

# Import existing components
from generate_contextual_tests_v002 import (
    REQIFArtifactExtractor,
    REQIFZFileProcessor,
    ExcelTestCaseGenerator,
    OllamaClient
)


class TrainingEnhancedProcessor(REQIFZFileProcessor):
    """Enhanced processor with integrated training data collection"""
    
    def __init__(self, model_name: str, training_enabled: bool = False):
        # Initialize base processor
        super().__init__(model_name)
        
        # Training configuration
        self.training_config = TrainingConfig()
        self.training_enabled = training_enabled or self.training_config.COLLECT_TRAINING_DATA
        
        # Replace standard logger with training-aware logger
        if self.training_enabled:
            print("🧠 Training mode enabled - collecting data for model improvement")
            self.training_logger = TrainingAwareFileProcessor(
                reqifz_file="training_session",
                input_path="training",
                output_file="training_output",
                version="v002_training",
                ai_model=model_name,
                collect_training_data=True
            )
        else:
            self.training_logger = None
    
    def process_single_file(self, reqifz_file_path: Path) -> bool:
        """Enhanced file processing with training data collection"""
        print(f"\n{'='*60}")
        print(f"🔍 Processing: {reqifz_file_path.name}")
        
        try:
            # Extract artifacts using parent class method
            all_objects = self.extractor.extract_all_artifacts(reqifz_file_path)
            
            if not all_objects:
                print(f"⚠️  No objects found in {reqifz_file_path.name}")
                return False
            
            # Classify artifacts
            headings = [obj for obj in all_objects if obj["artifact_type"] == "Heading"]
            system_interfaces = [obj for obj in all_objects if obj["artifact_type"] == "System Interface"]
            system_requirements = [obj for obj in all_objects if obj["artifact_type"] == "System Requirement"]
            
            print(f"📊 Found: {len(system_requirements)} requirements, {len(system_interfaces)} interfaces")
            
            if not system_requirements:
                print("⚠️  No System Requirements found")
                return False
            
            # Process each requirement
            all_test_cases = []
            successful_requirements = 0
            
            for req in system_requirements:
                try:
                    # Generate test cases using parent method
                    test_cases = self._generate_test_cases_for_requirement(
                        req, headings, system_interfaces
                    )
                    
                    if test_cases and self.training_enabled:
                        # Collect training data
                        self.training_logger.log_test_case_generation(
                            requirement_id=req.get("identifier", "UNKNOWN"),
                            requirement_text=req.get("text", ""),
                            table_data=req.get("table_str", ""),
                            generated_output=test_cases,
                            success=True
                        )
                    
                    if test_cases and "test_cases" in test_cases:
                        all_test_cases.extend(test_cases["test_cases"])
                        successful_requirements += 1
                        print(f"✅ {req.get('identifier', 'REQ')}: Generated {len(test_cases['test_cases'])} test cases")
                    
                except Exception as e:
                    print(f"❌ Error processing {req.get('identifier', 'REQ')}: {e}")
                    
                    if self.training_enabled:
                        # Log failed generation for analysis
                        self.training_logger.log_test_case_generation(
                            requirement_id=req.get("identifier", "UNKNOWN"),
                            requirement_text=req.get("text", ""),
                            table_data=req.get("table_str", ""),
                            generated_output={"error": str(e)},
                            success=False
                        )
            
            if all_test_cases:
                # Generate Excel output
                output_path = self._generate_output_path(reqifz_file_path)
                generator = ExcelTestCaseGenerator()
                success = generator.save_test_cases_to_excel(all_test_cases, output_path)
                
                if success:
                    print(f"📁 Saved {len(all_test_cases)} test cases to: {output_path}")
                    
                    # Finalize training collection if enabled
                    if self.training_enabled:
                        training_summary = self.training_logger.finalize_training_collection()
                        print(f"🧠 Training data collected: {training_summary['training_data_stats']}")
                        
                        # Check if ready for retraining
                        if training_summary.get("ready_for_export", False):
                            self._check_retraining_trigger(training_summary)
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error processing {reqifz_file_path.name}: {e}")
            return False
    
    def _check_retraining_trigger(self, training_summary: dict) -> None:
        """Check if conditions are met for automated retraining"""
        stats = training_summary["training_data_stats"]
        validated_count = stats.get("files_validated", 0)
        
        if validated_count >= self.training_config.MIN_EXAMPLES_FOR_TRAINING:
            print(f"🚀 Ready for model retraining with {validated_count} validated examples")
            print("💡 Run 'python src/train_custom_model.py' to start training")
        else:
            needed = self.training_config.MIN_EXAMPLES_FOR_TRAINING - validated_count
            print(f"📈 Need {needed} more validated examples for retraining")


def create_training_management_cli():
    """Create CLI for training data management"""
    parser = argparse.ArgumentParser(
        description="Training Data Management for Automotive Test Case Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Training Workflow:
1. Enable training data collection: --training-mode
2. Process files normally to collect examples
3. Validate examples: --validate-data 
4. Train custom model: --train-model
5. Use custom model: --model your-custom-model

Examples:
  # Collect training data while processing
  python src/generate_contextual_tests_v002_with_training.py input.reqifz --training-mode
  
  # Validate collected examples  
  python src/generate_contextual_tests_v002_with_training.py --validate-data
  
  # Train new custom model
  python src/generate_contextual_tests_v002_with_training.py --train-model
  
  # Use trained model
  python src/generate_contextual_tests_v002_with_training.py input.reqifz --model automotive-test-v1
        """
    )
    
    # Standard processing arguments
    parser.add_argument("input_path", nargs="?", help="Path to REQIFZ file or directory")
    parser.add_argument("--model", default="llama3.1:8b", help="Model to use")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Training-specific arguments
    parser.add_argument("--training-mode", action="store_true", 
                       help="Enable training data collection")
    parser.add_argument("--validate-data", action="store_true",
                       help="Interactive validation of collected training data")
    parser.add_argument("--train-model", action="store_true",
                       help="Train new custom model from validated data")
    parser.add_argument("--export-training-data", action="store_true",
                       help="Export validated training data to file")
    parser.add_argument("--training-stats", action="store_true",
                       help="Show training data collection statistics")
    
    return parser


def validate_training_data():
    """Interactive validation of collected training data"""
    collector = TrainingDataCollector()
    stats = collector.get_collection_stats()
    
    print(f"📊 Training Data Statistics:")
    print(f"  Total collected: {stats['total_collected']}")
    print(f"  Pending validation: {stats['files_pending']}")
    print(f"  Already validated: {stats['files_validated']}")
    print(f"  Rejected: {stats['files_rejected']}")
    
    if stats['files_pending'] == 0:
        print("✅ No pending examples to validate")
        return
    
    # Interactive validation
    pending_files = list(Path("training_data/collected").glob("*.json"))
    
    for file_path in pending_files:
        with open(file_path) as f:
            example = json.load(f)
        
        print(f"\n{'='*60}")
        print(f"🔍 Validating: {example['requirement_id']}")
        print(f"Requirement: {example['requirement_text'][:200]}...")
        print(f"Generated {len(example['generated_output'].get('test_cases', []))} test cases")
        
        while True:
            choice = input("\nValidate this example? [a]pprove/[r]eject/[s]kip/[q]uit: ").lower()
            
            if choice == 'a':
                collector.approve_example(example['requirement_id'])
                print("✅ Example approved")
                break
            elif choice == 'r':
                reason = input("Rejection reason: ")
                collector.reject_example(example['requirement_id'], reason)
                print("❌ Example rejected")
                break
            elif choice == 's':
                print("⏭️  Skipped")
                break
            elif choice == 'q':
                print("🚪 Validation stopped")
                return
            else:
                print("Invalid choice. Use a/r/s/q")


def train_custom_model():
    """Train custom model from validated data"""
    try:
        from custom_model_trainer import AutomotiveModelTrainer, LoRATrainingConfig, AutomatedTrainingPipeline
    except ImportError as e:
        print(f"❌ Training dependencies not available: {e}")
        print("Install with: pip install torch transformers peft datasets")
        return False
    
    # Setup training configuration
    training_config = TrainingConfig()
    lora_config = LoRATrainingConfig(
        lora_r=training_config.LORA_R,
        lora_alpha=training_config.LORA_ALPHA,
        learning_rate=training_config.LEARNING_RATE,
        num_train_epochs=training_config.NUM_TRAIN_EPOCHS
    )
    
    # Initialize trainer and pipeline
    trainer = AutomotiveModelTrainer(lora_config)
    collector = TrainingDataCollector()
    pipeline = AutomatedTrainingPipeline(collector, trainer)
    
    # Check readiness and execute training
    ready, message = pipeline.check_training_readiness()
    print(f"🔍 Training readiness: {message}")
    
    if not ready:
        return False
    
    # Execute training pipeline
    result = pipeline.execute_training_pipeline()
    
    if result["status"] == "success":
        print(f"🎉 Training completed successfully!")
        print(f"📦 New model: {result['model_name']}")
        print(f"💡 Use with: --model {result['model_name']}")
        return True
    else:
        print(f"❌ Training failed: {result.get('reason', 'Unknown error')}")
        return False


def main():
    parser = create_training_management_cli()
    args = parser.parse_args()
    
    # Handle training management commands
    if args.validate_data:
        validate_training_data()
        return
    
    if args.train_model:
        success = train_custom_model()
        sys.exit(0 if success else 1)
    
    if args.export_training_data:
        collector = TrainingDataCollector()
        training_file = collector.export_training_dataset()
        print(f"✅ Training data exported to: {training_file}")
        return
    
    if args.training_stats:
        collector = TrainingDataCollector()
        stats = collector.get_collection_stats()
        print(json.dumps(stats, indent=2))
        return
    
    # Standard processing with optional training
    if not args.input_path:
        parser.print_help()
        return
    
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"❌ Input path does not exist: {input_path}")
        sys.exit(1)
    
    # Initialize enhanced processor
    processor = TrainingEnhancedProcessor(
        model_name=args.model,
        training_enabled=args.training_mode
    )
    
    # Process files
    if input_path.is_file():
        success = processor.process_single_file(input_path)
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    else:
        # Process directory
        reqifz_files = list(input_path.glob("*.reqifz"))
        if not reqifz_files:
            print(f"❌ No .reqifz files found in {input_path}")
            sys.exit(1)
        
        successful = 0
        for reqifz_file in reqifz_files:
            if processor.process_single_file(reqifz_file):
                successful += 1
        
        print(f"\n📊 Processed {successful}/{len(reqifz_files)} files successfully")
    
    print("🎯 Processing complete!")


if __name__ == "__main__":
    main()