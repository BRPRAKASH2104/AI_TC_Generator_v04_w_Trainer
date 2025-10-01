# GEMINI.md - AI Test Case Generator v1.4.0

## Project Overview

This project is a Python-based AI test case generator designed for automotive requirements specified in REQIFZ files. It leverages Ollama AI models to automatically generate test cases from these requirements, significantly speeding up the testing process.

The application is built with a modular and maintainable architecture, separating core logic (data extraction, generation, parsing) from high-level processing workflows. It features a unified command-line interface (CLI) that supports multiple operational modes, including a standard mode for reliable processing and a high-performance asynchronous mode for faster results.

A key feature of this application is its **context-aware processing** capability. The system intelligently gathers and utilizes contextual information such as headings, informational notes, and system interfaces from the REQIFZ file to generate more accurate and relevant test cases.

**Key Technologies:**

*   **Programming Language:** Python 3.13+
*   **AI Integration:** Ollama (with models like `llama3.1:8b` and `deepseek-coder-v2:16b`)
*   **Core Libraries:**
    *   `click`: For building the command-line interface.
    *   `pandas` & `openpyxl`: For data manipulation and Excel output.
    *   `requests` & `aiohttp`: For communicating with the Ollama API.
    *   `PyYAML`: For managing prompt templates.
    *   `pydantic`: For configuration management.
    *   `lxml`: For fast XML processing.
*   **Architecture:**
    *   **Modular Core (`src/core`):** Components for extraction, generation, formatting, and parsing.
    *   **Processors (`src/processors`):** Orchestrates the standard and high-performance workflows.
    *   **Prompts (`prompts`):** YAML-based prompt templates for the AI models.
    *   **Configuration (`config`):** Centralized configuration for the CLI and application settings.

## Building and Running

### 1. Installation

This project uses `pyproject.toml` to manage dependencies. It is recommended to install the project in editable mode with the development dependencies.

**Recommended Installation:**

```bash
pip install -e .[dev]
```

This command installs the project in editable mode (`-e`) and includes all development dependencies specified in `pyproject.toml` under the `[project.optional-dependencies]` table.

**Optional Installations:**

*   **Security scanning tools:** `pip install -e .[security]`
*   **ML training dependencies:** `pip install -e .[training]`
*   **All optional dependencies:** `pip install -e .[all]`

**Note on `requirements.txt`:**

The `requirements.txt` file is also present in the repository, but it is recommended to use `pyproject.toml` as the single source of truth for dependencies. The `requirements.txt` file may be deprecated in the future.

### 2. Running the Application

The main entry point for the application is `main.py`. You can run it with various options depending on the desired mode.

**Basic Usage (Standard Mode):**

```bash
python main.py <path_to_reqifz_file>
```

**High-Performance Mode:**

This mode uses asynchronous processing to generate test cases faster.

```bash
python main.py <path_to_reqifz_file> --hp
```

**Other Useful Commands:**

*   **Validate Prompts:** Check the syntax and structure of the prompt templates.
    ```bash
    python main.py --validate-prompts
    ```
*   **List Templates:** List all available prompt templates.
    ```bash
    python main.py --list-templates
    ```

### 3. Running Tests

The project uses `pytest` for testing. A convenience script `run_tests.py` is provided to run the test suite with coverage reporting.

```bash
python tests/run_tests.py
```

This will run all tests in the `tests/` directory and generate a coverage report in the `htmlcov/` directory.

## Development Conventions

*   **Coding Style:** The project follows modern Python conventions, including type hinting and a modular structure.
*   **Testing:** All new code should be accompanied by unit or integration tests in the `tests/` directory.
*   **Prompts:** AI prompts are defined in YAML files in the `prompts/templates/` directory. When adding new prompts, follow the existing structure.
*   **Configuration:** Application settings can be modified in `config/cli_config.yaml`. This file includes presets for different environments (e.g., `development`, `production`).
*   **Dependencies:** All project dependencies are listed in `pyproject.toml`.

## Architecture Overview

The application is designed with a modular architecture to ensure maintainability and extensibility.

*   **`main.py`:** The CLI entry point, built with `click`.
*   **`src/`:** The main source code directory.
    *   **`core/`:** Contains the core business logic components:
        *   `extractors.py`: Parses REQIFZ files.
        *   `generators.py`: Generates test cases using AI models.
        *   `formatters.py`: Formats test cases for output.
        *   `ollama_client.py`: Communicates with the Ollama API.
        *   `parsers.py`: Parses JSON and HTML.
    *   **`processors/`:** Orchestrates the processing workflows:
        *   `standard_processor.py`: Implements the standard, synchronous processing logic.
        *   `hp_processor.py`: Implements the high-performance, asynchronous processing logic.
    *   **`config.py`:** Manages application configuration using `pydantic`.
    *   **`app_logger.py`:** Provides centralized logging.
    *   **`yaml_prompt_manager.py`:** Manages YAML-based prompt templates.
*   **`prompts/`:** Contains the YAML prompt templates.
*   **`tests/`:** Contains the test suite.
*   **`utilities/`:** Contains utility scripts.

## Context-Aware Processing

The context-aware processing logic is a key feature of this application. It works as follows:

1.  The `REQIFArtifactExtractor` extracts all artifacts from the REQIFZ file, including headings, information, system interfaces, and system requirements.
2.  The processor iterates through the artifacts in order, building up a context of the current heading and any informational notes.
3.  When a system requirement is encountered, it is augmented with the current context (heading, information, and system interfaces).
4.  The augmented requirement is then passed to the `TestCaseGenerator`, which uses the context to generate more accurate and relevant test cases.

This ensures that the AI model has the necessary context to understand the requirement and generate high-quality test cases.