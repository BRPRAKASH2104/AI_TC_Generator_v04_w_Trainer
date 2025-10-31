# GEMINI.md - AI Test Case Generator

## Project Overview

This project is a Python-based AI Test Case Generator designed to process REQIFZ files, which are common in the automotive industry for managing requirements. The application extracts requirements from these files, uses AI models (via Ollama) to generate test cases, and then formats the test cases into Excel files.

The project is built with a modular architecture, separating concerns into core components (extractors, generators, formatters), processors (for standard and high-performance workflows), and a CLI interface. It supports both synchronous and asynchronous processing, with the high-performance mode offering significant speed improvements.

**Key Technologies:**

*   **Python 3.14+**
*   **Ollama**: For AI model inference (e.g., Llama 3.1, DeepSeek Coder v2).
*   **Click**: For the command-line interface.
*   **Pydantic**: For configuration management.
*   **Pandas** and **Openpyxl**: For creating Excel reports.
*   **Asyncio** and **AIOHTTP**: For high-performance asynchronous processing.
*   **Pytest**: For testing.
*   **Ruff** and **MyPy**: For linting and static type checking.

## Building and Running

### Installation

The project uses `pyproject.toml` for dependency management. To install the required dependencies, you can use pip:

```bash
pip install -e .[dev]
```

This will install the project in editable mode along with the development dependencies.

### Running the Application

The main entry point is `main.py`. You can run the application using the following command:

```bash
python3 main.py [OPTIONS] INPUT_PATH
```

**Common Commands:**

*   **Standard Processing:**

    ```bash
    python3 main.py input/your_file.reqifz
    ```

*   **High-Performance Processing:**

    ```bash
    python3 main.py input/your_file.reqifz --hp --performance
    ```

*   **Using a specific model:**

    ```bash
    python3 main.py input/your_file.reqifz --model deepseek-coder-v2:16b
    ```

### Running Tests

The project uses `pytest` for testing. To run the tests, use the following command:

```bash
pytest
```

To run the tests with coverage, use:

```bash
pytest --cov=src
```

## Development Conventions

*   **Coding Style**: The project uses **Ruff** for linting and formatting, with a line length of 100 characters. The configuration is in `pyproject.toml`.
*   **Type Checking**: **MyPy** is used for static type checking. The configuration is in `pyproject.toml`.
*   **Testing**: The project has a well-structured `tests` directory with unit, integration, and performance tests. Mocking is used to isolate components and test them independently.
*   **Configuration**: Application configuration is managed through `pydantic` models in `src/config.py`. A `ConfigManager` handles loading configurations from files and environment variables.
*   **Entry Points**: The main entry point is `main.py` in the root directory. The `[project.scripts]` in `pyproject.toml` defines the `ai-tc-generator` and `ai-tc-gen` commands.
