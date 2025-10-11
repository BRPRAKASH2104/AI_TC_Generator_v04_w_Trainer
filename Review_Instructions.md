# Codebase Review Instructions

1. Preparation and Scope:
-   **Understand the Project:** Familiarize yourself with the project's purpose, architecture, and relevant documentation (e.g.,  `README`,  `Copilot instructions`, `CLAUDE.md` guidelines, `System_Intructions.md`, design documents).
- **Run the Project:** Set up the development environment and run the application to understand its functionality and dependencies.    
-   **Define Review Scope:** Determine whether the review will focus on specific aspects like performance, security, or compliance with coding standards (e.g., PEP 8).    


2. Code Structure and Organization:

-   **Project Layout:** Verify a logical project structure (e.g.,  `src/`,  `tests/`,  `docs/`).  Identify files that are not used, redundant and suggest for removal.
-   **Modularity:** Ensure separation of concerns and appropriate modularization of business logic, data handling, and presentation layers.    
-   **File and Module Size:** Assess if files and functions are appropriately sized; suggest breaking down large components for better readability and testability.    
-   **Naming Conventions:** Confirm adherence to Python's naming conventions (e.g.,  `snake_case`  for variables and functions,  `PascalCase`  for classes).
    

3. Readability and Style:

-   **PEP 8 Compliance:** Check for adherence to PEP 8 style guidelines, including indentation (4 spaces), line length (max 79 characters), blank lines, and import ordering. Perform additional checks for PEP 649, PEP 737, type hints.
-   **Descriptive Naming:** Evaluate if variables, functions, and classes have clear, concise, and informative names.    
-   **Comments and Docstrings:** Verify the presence and clarity of comments and docstrings, explaining complex logic or module/function purpose.
    

4. Functionality and Correctness:

-   **Requirements Fulfillment:** Confirm that the code correctly implements the intended requirements.
-   **Edge Cases and Error Handling:** Evaluate handling of edge cases, invalid inputs, and potential errors.
-   **Test Coverage:** Assess the adequacy of unit and integration tests, ensuring comprehensive testing of functionality.

5. Analyze Python
- **Version complaince:** Check for python specific version compliance.
- **Optimization opportunities:** CHeck for version specific optimisations.
- **Dependencies:** Check for compatibility and usage of libraries. Ensure the latest version is used for maximum benefits.
- **Backward Compatibility:** Backward compatibility is not encouraged. Look for older version dependencies and suggest for removal.
 
6. Performance and Efficiency:

-   **Algorithm Efficiency:** Review algorithms for time and space complexity, identifying potential performance bottlenecks.    
-   **Resource Management:** Check for proper resource management, including file handling, database connections, and memory usage.
-   **Error Management:** Check for logical error, calculation error.
-   **Coding Efficiently:** Check for function call, data structures.
-   **Review resource utilization:** Check for Memory, CPU and GPU usage patterns.

7. AI Model

- **Usage:** Check for model usage properties. Look for the Ollama version specfic API calls for maximum efficiency.
	- llama3.1:8b
	- deepseek-coder-v2:16b

8. Prompt and Context Engineering:

- **Prompt efficiency:** Check for the prompts used and suggest for improvements.
- **Context efficiency:** Check for the prompts used and suggest for improvements.	

9. Security:

-   **Input Sanitization:** Verify proper sanitization of user inputs to prevent vulnerabilities like injection attacks.
-   **Security Best Practices:** Identify and address potential security risks or deviations from secure coding practices.
    
10. Maintainability and Extensibility:

-   **Code Duplication:** Identify and suggest refactoring of duplicate code segments.
-   **Design Patterns:** Evaluate the appropriate and correct implementation of design patterns.
-   **Reusability:** Look for opportunities to promote code reuse through well-designed functions and modules.

11. Automation and Tooling:
-   **Linters and Formatters:** Encourage the use of tools like Black, Flake8, or Pylint to enforce style and identify potential issues automatically.    
-   **Static Type Checkers:** Recommend using tools like MyPy for static type checking to catch type-related errors early.

12. Report
- **Report:** Create comprehensive review report with recommendations
