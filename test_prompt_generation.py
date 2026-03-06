import yaml
from pathlib import Path
from src.core.extractors import REQIFArtifactExtractor
from src.core.prompt_builder import PromptBuilder

def main():
    extractor = REQIFArtifactExtractor()
    objects = extractor.extract_reqifz_content(Path("input/REQIFZ_Files/TFDCX32348_GUI_Analog Speed Gauge for Lexus_d54516.reqifz"))
    
    prompt_builder = PromptBuilder()
    
    with open("generated_prompts_debug.txt", "w", encoding="utf-8") as f:
        for req in objects:
            req_id = req.get("id", "")
            if "137299" in req_id or "137292" in req_id or "137314" in req_id:
                prompt = prompt_builder.build_prompt(req)
                f.write(f"=== {req_id} ===\n")
                f.write(prompt)
                f.write("\n\n")

if __name__ == "__main__":
    main()
