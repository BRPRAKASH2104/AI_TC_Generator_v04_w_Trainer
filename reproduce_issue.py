
import sys
from pathlib import Path
import json

# Add project root to path so src package can be imported
sys.path.insert(0, str(Path(__file__).parent))

from src.config import ConfigManager

def test_config_fix():
    print("Initializing ConfigManager...")
    base_config = ConfigManager()
    
    # Load CLI config (this loads from config/cli_config.yaml)
    print("Loading CLI config...")
    base_config.load_cli_config()
    
    preset_name = "qwen_vision"
    print(f"\nGetting preset '{preset_name}'...")
    preset_config = base_config.get_preset_config(preset_name)
    
    # Simulate main.py logic (THE FIX)
    nested_update = {}
    
    def set_nested(d, path, value):
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    key_mapping = {
        "model": ["ollama", "synthesizer_model"],
        "mode": ["cli", "mode"],
        "verbose": ["cli", "verbose"],
        "debug": ["cli", "debug"],
        "performance": ["cli", "performance"],
        "max_concurrent": ["ollama", "concurrent_requests"]
    }
    
    print("\nProcessing preset items (WITH FIX):")
    for key, value in preset_config.items():
        if key in key_mapping:
            # Create a separate dict for this mapped key
            temp_dict = {}
            set_nested(temp_dict, key_mapping[key], value)
            ConfigManager._deep_merge_dict(nested_update, temp_dict)
            print(f"Mapped '{key}' -> {key_mapping[key]}")
        else:
            # Deep merge unmapped keys
            temp_dict = {key: value}
            ConfigManager._deep_merge_dict(nested_update, temp_dict)
            print(f"Merged '{key}' as is")

    print("\nResulting nested_update:")
    print(json.dumps(nested_update, indent=2, default=str))
    
    print("\nDeep merging...")
    current_data = base_config.model_dump()
    ConfigManager._deep_merge_dict(current_data, nested_update)
    
    print("\nValidating...")
    try:
        final_config = ConfigManager.model_validate(current_data)
        print("Validation SUCCESS")
        print(f"Synthesizer Model: {final_config.ollama.synthesizer_model}")
        print(f"Vision Model: {final_config.ollama.vision_model}")
        print(f"Mode: {final_config.cli.mode}")
        
        if final_config.ollama.synthesizer_model == "qwen3-vl:32b":
            print("✅ VERIFIED: Synthesizer Model correctly set (Overwrite bug fixed)")
        else:
            print(f"❌ FAILED: Synthesizer Model is {final_config.ollama.synthesizer_model} (Expected qwen3-vl:32b)")
            
    except Exception as e:
        print(f"Validation FAILED: {e}")

if __name__ == "__main__":
    test_config_fix()
