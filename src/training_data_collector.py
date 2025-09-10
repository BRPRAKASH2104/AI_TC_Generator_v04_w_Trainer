#!/usr/bin/env python3
"""
Training Data Collection System for Custom Automotive Model Training
Integrates with existing FileProcessingLogger to collect training examples
"""

import json
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from file_processing_logger import FileProcessingLogger


@dataclass
class TrainingExample:
    """Single training example for fine-tuning"""
    requirement_id: str
    requirement_text: str
    table_data: str
    generated_output: Dict[str, Any]
    validation_status: str  # "pending", "approved", "rejected"
    correction: Optional[Dict[str, Any]] = None
    domain: str = "automotive"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class TrainingDataCollector:
    """Collects training data during normal processing for future model fine-tuning"""
    
    __slots__ = ('output_dir', 'examples', 'session_id', 'collection_enabled')
    
    def __init__(self, output_dir: str = "training_data", collection_enabled: bool = True):
        self.output_dir = Path(output_dir)
        self.examples: List[TrainingExample] = []
        self.session_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.collection_enabled = collection_enabled
        
        if self.collection_enabled:
            self.output_dir.mkdir(exist_ok=True)
            (self.output_dir / "collected").mkdir(exist_ok=True)
            (self.output_dir / "validated").mkdir(exist_ok=True)
            (self.output_dir / "rejected").mkdir(exist_ok=True)
    
    def collect_example(
        self,
        requirement_id: str,
        requirement_text: str,
        table_data: str,
        generated_output: Dict[str, Any],
        validation_status: str = "pending"
    ) -> None:
        """Collect a training example during processing"""
        if not self.collection_enabled:
            return
            
        example = TrainingExample(
            requirement_id=requirement_id,
            requirement_text=requirement_text,
            table_data=table_data,
            generated_output=generated_output,
            validation_status=validation_status
        )
        
        self.examples.append(example)
        self._save_example(example)
    
    def _save_example(self, example: TrainingExample) -> None:
        """Save individual example to file"""
        filename = f"{example.requirement_id}_{self.session_id}.json"
        filepath = self.output_dir / "collected" / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                "requirement_id": example.requirement_id,
                "requirement_text": example.requirement_text,
                "table_data": example.table_data,
                "generated_output": example.generated_output,
                "validation_status": example.validation_status,
                "correction": example.correction,
                "domain": example.domain,
                "timestamp": example.timestamp
            }, f, indent=2)
    
    def approve_example(self, requirement_id: str, correction: Optional[Dict[str, Any]] = None) -> bool:
        """Approve an example for training (optionally with corrections)"""
        for example in self.examples:
            if example.requirement_id == requirement_id:
                example.validation_status = "approved"
                if correction:
                    example.correction = correction
                
                # Move to validated directory
                self._move_example(example, "validated")
                return True
        return False
    
    def reject_example(self, requirement_id: str, reason: str = "") -> bool:
        """Reject an example from training"""
        for example in self.examples:
            if example.requirement_id == requirement_id:
                example.validation_status = "rejected"
                example.correction = {"rejection_reason": reason}
                
                # Move to rejected directory  
                self._move_example(example, "rejected")
                return True
        return False
    
    def _move_example(self, example: TrainingExample, status_dir: str) -> None:
        """Move example to appropriate validation directory"""
        old_path = self.output_dir / "collected" / f"{example.requirement_id}_{self.session_id}.json"
        new_path = self.output_dir / status_dir / f"{example.requirement_id}_{self.session_id}.json"
        
        if old_path.exists():
            # Update example data before moving
            with open(new_path, 'w') as f:
                json.dump({
                    "requirement_id": example.requirement_id,
                    "requirement_text": example.requirement_text,
                    "table_data": example.table_data,
                    "generated_output": example.generated_output,
                    "validation_status": example.validation_status,
                    "correction": example.correction,
                    "domain": example.domain,
                    "timestamp": example.timestamp
                }, f, indent=2)
            
            old_path.unlink()  # Remove from collected
    
    def export_training_dataset(self, output_file: Optional[str] = None) -> str:
        """Export validated examples in format suitable for LoRA fine-tuning"""
        if not output_file:
            output_file = f"automotive_training_{self.session_id}.jsonl"
        
        output_path = self.output_dir / output_file
        training_count = 0
        
        # Collect all validated examples
        validated_dir = self.output_dir / "validated"
        
        with open(output_path, 'w') as f:
            for example_file in validated_dir.glob("*.json"):
                with open(example_file) as ef:
                    example = json.load(ef)
                
                # Format for fine-tuning (using ChatML format)
                training_item = {
                    "messages": [
                        {
                            "role": "system", 
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": self._format_user_input(
                                example["requirement_text"], 
                                example["table_data"]
                            )
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(
                                example["correction"] if example["correction"] else example["generated_output"]
                            )
                        }
                    ]
                }
                
                f.write(json.dumps(training_item) + "\n")
                training_count += 1
        
        print(f"✅ Exported {training_count} training examples to {output_path}")
        return str(output_path)
    
    def _get_system_prompt(self) -> str:
        """System prompt for fine-tuning"""
        return """You are an expert automotive test engineer specializing in REQIF-based test case generation. Generate comprehensive test cases that follow automotive industry standards with:

- Valid automotive signal names and interfaces
- Realistic value ranges and units (speed in km/h, voltage in V, etc.)
- Proper error handling and safety-critical scenarios
- Both positive and negative test cases
- JSON format output with test_type field"""
    
    def _format_user_input(self, requirement_text: str, table_data: str) -> str:
        """Format requirement and table data for training input"""
        return f"""Generate automotive test cases for this requirement:

REQUIREMENT: {requirement_text}

TABLE DATA: {table_data}

Generate comprehensive test cases in JSON format with both positive and negative scenarios."""
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about collected training data"""
        stats = {
            "total_collected": len(self.examples),
            "pending_validation": len([e for e in self.examples if e.validation_status == "pending"]),
            "approved": len([e for e in self.examples if e.validation_status == "approved"]),
            "rejected": len([e for e in self.examples if e.validation_status == "rejected"])
        }
        
        # Count files in directories
        if self.output_dir.exists():
            stats["files_validated"] = len(list((self.output_dir / "validated").glob("*.json")))
            stats["files_rejected"] = len(list((self.output_dir / "rejected").glob("*.json")))
            stats["files_pending"] = len(list((self.output_dir / "collected").glob("*.json")))
        
        return stats
    
    def save_session_summary(self) -> str:
        """Save summary of current collection session"""
        summary_file = self.output_dir / f"session_summary_{self.session_id}.json"
        
        with open(summary_file, 'w') as f:
            json.dump({
                "session_id": self.session_id,
                "collection_enabled": self.collection_enabled,
                "stats": self.get_collection_stats(),
                "timestamp": datetime.now(UTC).isoformat()
            }, f, indent=2)
        
        return str(summary_file)


# Integration with existing FileProcessingLogger
class TrainingAwareFileProcessor(FileProcessingLogger):
    """Extended FileProcessingLogger that also collects training data"""
    
    def __init__(self, *args, collect_training_data: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.training_collector = TrainingDataCollector(collection_enabled=collect_training_data)
    
    def log_test_case_generation(
        self, 
        requirement_id: str,
        requirement_text: str,
        table_data: str,
        generated_output: Dict[str, Any],
        success: bool = True
    ) -> None:
        """Log test case generation and collect for training"""
        # Regular logging
        super().add_test_cases(len(generated_output.get("test_cases", [])))
        
        # Training data collection
        if success:
            self.training_collector.collect_example(
                requirement_id=requirement_id,
                requirement_text=requirement_text,
                table_data=table_data,
                generated_output=generated_output,
                validation_status="pending"
            )
    
    def finalize_training_collection(self) -> Dict[str, Any]:
        """Finalize training data collection and return summary"""
        stats = self.training_collector.get_collection_stats()
        summary_file = self.training_collector.save_session_summary()
        
        return {
            "training_data_stats": stats,
            "summary_file": summary_file,
            "ready_for_export": stats["files_validated"] > 0
        }


if __name__ == "__main__":
    # Test the training data collector
    collector = TrainingDataCollector()
    
    # Simulate collecting an example
    collector.collect_example(
        requirement_id="REQ_TEST_001",
        requirement_text="Door lock shall activate when speed > 15 km/h",
        table_data="speed > 15 -> door_lock = ON",
        generated_output={
            "test_cases": [
                {
                    "summary_suffix": "Door lock activation test",
                    "action": "Set ignition to ON",
                    "data": "1) Set vehicle_speed = 16 km/h",
                    "expected_result": "Verify door_lock_status = LOCKED",
                    "test_type": "positive"
                }
            ]
        }
    )
    
    # Approve the example
    collector.approve_example("REQ_TEST_001")
    
    # Export training dataset
    training_file = collector.export_training_dataset()
    print(f"Training dataset exported to: {training_file}")
    
    # Show stats
    stats = collector.get_collection_stats()
    print(f"Collection stats: {stats}")