import traceback
from pathlib import Path
from src.core.extractors import REQIFArtifactExtractor
from src.core.prompt_builder import PromptBuilder
from src.yaml_prompt_manager import YAMLPromptManager

def main():
    extractor = REQIFArtifactExtractor()
    objects = extractor.extract_reqifz_content(Path("input/REQIFZ_Files/TFDCX32348_GUI_Analog Speed Gauge for Lexus_d54516.reqifz"))
    
    manager = YAMLPromptManager()
    prompt_builder = PromptBuilder(manager)
    
    for req in objects:
        req_id = req.get("id", "")
        if "137299" in req_id:
            try:
                prompt = prompt_builder.build_prompt(req)
                print(f"=== {req_id} ===")
                print(prompt)
                print("=================")
            except Exception as e:
                print("Exception caught:")
                traceback.print_exc()

if __name__ == "__main__":
    main()
