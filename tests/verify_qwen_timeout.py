
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("c:/GitHub/AI_TC_Generator_v04_w_Trainer")))

from src.config import ConfigManager

def verify_qwen_timeout():
    print("Verifying 'qwen_vision' preset applies timeout...")
    
    # Initialize config
    base_config = ConfigManager()
    base_config.load_cli_config()
    
    # Simulate main.py preset application logic
    preset_name = "qwen_vision"
    preset_config = base_config.get_preset_config(preset_name)
    
    if not preset_config:
        print("❌ Preset not found")
        return False
        
    # Map keys (logic copied from main.py)
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
    
    for key, value in preset_config.items():
        if key in key_mapping:
            temp_dict = {}
            set_nested(temp_dict, key_mapping[key], value)
            ConfigManager._deep_merge_dict(nested_update, temp_dict)
        else:
            temp_dict = {key: value}
            ConfigManager._deep_merge_dict(nested_update, temp_dict)

    current_data = base_config.model_dump()
    ConfigManager._deep_merge_dict(current_data, nested_update)
    base_config = ConfigManager.model_validate(current_data)
    
    # Now verify apply_cli_overrides applies the timeout
    # We pass empty kwargs because preset already set the model in base_config
    effective_config = base_config.apply_cli_overrides()
    
    expected_timeout = 1500
    actual_timeout = effective_config.ollama.timeout
    
    print(f"Model: {effective_config.ollama.synthesizer_model}")
    print(f"Timeout: {actual_timeout} (Expected: {expected_timeout})")
    
    if actual_timeout != expected_timeout:
        print(f"❌ Timeout mismatch! Got {actual_timeout}, expected {expected_timeout}")
        return False
        
    print("✅ Timeout verified!")
    return True

if __name__ == "__main__":
    success = verify_qwen_timeout()
    sys.exit(0 if success else 1)
