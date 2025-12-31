
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("c:/GitHub/AI_TC_Generator_v04_w_Trainer")))

from src.config import ConfigManager

def verify_qwen_preset():
    print("Verifying 'qwen_vision' preset...")
    
    # Initialize config
    config = ConfigManager()
    
    # Load CLI config (which contains the preset)
    # Load CLI config (simulating main.py call without args)
    # This verifies that default paths (config/cli_config.yaml) are correctly resolved
    config.load_cli_config()
    
    # Get the preset
    preset = config.get_preset_config("qwen_vision")
    
    if not preset:
        print("❌ Preset 'qwen_vision' not found!")
        return False
        
    print(f"Preset found: {preset}")
    
    # Verify values
    expected_model = "qwen3-vl:32b"
    expected_vision_model = "qwen3-vl:32b"
    
    if preset.get("model") != expected_model:
        print(f"❌ Incorrect model in preset: {preset.get('model')} (Expected: {expected_model})")
        return False
        
    if preset.get("ollama", {}).get("vision_model") != expected_vision_model:
        print(f"❌ Incorrect vision_model in preset: {preset.get('ollama', {}).get('vision_model')} (Expected: {expected_vision_model})")
        return False
        
    print("✅ Preset configuration verified!")
    return True

if __name__ == "__main__":
    success = verify_qwen_preset()
    sys.exit(0 if success else 1)
