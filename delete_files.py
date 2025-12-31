import os
import shutil

files = [
    "REQIFZ_ANALYSIS_REPORT.json",
    "test_output.txt",
    "test_report_20251231_171150.json",
    "test_report_20251231_171405.json",
    "coverage.xml",
    "reproduce_issue.py"
]
dirs = ["htmlcov"]

log = []
try:
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
                log.append(f"Deleted {f}")
            except Exception as e:
                log.append(f"Failed to delete {f}: {e}")
        else:
            log.append(f"File not found: {f}")

    for d in dirs:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                log.append(f"Deleted dir {d}")
            except Exception as e:
                log.append(f"Failed to delete dir {d}: {e}")
        else:
            log.append(f"Dir not found: {d}")
            
    # Also clean TEMP/images
    temp_images = "TEMP/images"
    if os.path.exists(temp_images):
        for item in os.listdir(temp_images):
            item_path = os.path.join(temp_images, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                    log.append(f"Deleted {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    log.append(f"Deleted dir {item_path}")
            except Exception as e:
                log.append(f"Failed to delete {item_path}: {e}")

except Exception as e:
    log.append(f"Global error: {e}")

with open("deletion.log", "w") as f:
    f.write("\n".join(log))
