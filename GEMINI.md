# Gemini Code Assistant Context

## Project Overview

This project is a Python-based **AI Test Case Generator** designed to automatically create test cases from requirements specified in REQIFZ files, a format common in the automotive industry. The generated test cases are exported to Excel files.

The project has a strong focus on performance and includes a high-performance version that leverages multi-threading, asynchronous operations, and other optimizations to maximize CPU utilization.

The core of the test case generation is an AI model, which is accessed through an Ollama server. The prompts used to interact with the AI model are managed in YAML files, allowing for easy customization and versioning.

The project also includes a framework for **training custom models**. It provides scripts for collecting training data from the test case generation process and for fine-tuning models using Low-Rank Adaptation (LoRA).

## Building and Running

### Installation

The project uses `pip` for dependency management. The main dependencies are defined in `pyproject.toml` and `utilities/requirements.txt`.

To install the core dependencies, run:

```bash
pip install -r utilities/requirements.txt
```

For the high-performance version, which includes additional libraries for parallel processing and speed, run:

```bash
pip install -r utilities/requirements-highperformance.txt
```

### Running the Application

The main scripts for running the test case generation are located in the `src` directory.

*   **Standard Version:**
    ```bash
    python src/generate_contextual_tests_v002_w_Logging_WIP.py <path_to_reqifz_file_or_directory>
    ```

*   **High-Performance Version:**
    ```bash
    python src/generate_contextual_tests_v003_HighPerformance.py <path_to_reqifz_file_or_directory> --hp
    ```

### Running Tests

The project uses `pytest` for testing. The tests are organized into `unit`, `integration`, and `performance` categories within the `tests` directory.

To run all tests, execute:

```bash
pytest
```

The `pyproject.toml` file contains the detailed pytest configuration, including coverage reporting.

## Development Conventions

### Code Style and Quality

*   **Linting and Formatting:** The project uses `ruff` for both linting and code formatting, ensuring a consistent code style. The configuration can be found in the `pyproject.toml` file.
*   **Type Checking:** `mypy` is used for static type checking, and the codebase includes type hints. The `mypy` configuration is also in `pyproject.toml`.

### Prompt Management

The prompts for the AI model are defined in YAML files located in the `prompts` directory. The `prompts/config/prompt_config.yaml` file controls which prompt templates are used. This separation of prompts from code allows for easy experimentation and modification of the AI's behavior.

### Configuration

The application's configuration is managed by the `ConfigManager` class in `src/config.py`. It can be configured through environment variables or a YAML file.

### Logging

The project features a comprehensive logging system. The `FileProcessingLogger` in `src/file_processing_logger.py` is particularly important, as it generates a detailed JSON log for each REQIFZ file that is processed.

### Model Training

The project includes a pipeline for training custom models.

*   `src/training_data_collector.py`: This script collects data from the test case generation process to be used for training.
*   `src/custom_model_trainer.py`: This script uses the collected data to fine-tune a custom model using LoRA.
