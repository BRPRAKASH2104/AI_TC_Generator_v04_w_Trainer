# Input Directory

This directory is for organizing your REQIFZ input files for easy management.

## Usage

Place your `.reqifz` files here and reference them in commands:

```bash
# Process single file
python3 main.py input/your_file.reqifz

# Process all REQIFZ files in input directory
python3 main.py input/

# High-performance processing
python3 main.py input/your_file.reqifz --hp --performance
```

## Test Data

- `automotive_door_window_system.reqifz` - Generated test file with automotive door/window requirements

## File Organization

You can organize files in subdirectories:
```
input/
├── project1/
│   ├── requirements_v1.reqifz
│   └── requirements_v2.reqifz
├── project2/
│   └── specs.reqifz
└── test_data/
    └── automotive_door_window_system.reqifz
```

The system will process individual files or entire directories as specified in your command.