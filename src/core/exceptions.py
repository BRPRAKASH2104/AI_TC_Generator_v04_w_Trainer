"""
Custom exceptions for AI Test Case Generator.

Provides structured error handling with proper context and error types.
"""



class AITestCaseGeneratorError(Exception):
    """Base exception for all AI Test Case Generator errors"""
    pass


class OllamaError(AITestCaseGeneratorError):
    """Base exception for Ollama client errors"""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when connection to Ollama API fails"""

    def __init__(self, message: str, host: str | None = None, port: int | None = None):
        self.host = host
        self.port = port
        super().__init__(message)


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama API request times out"""

    def __init__(self, message: str, timeout: int | None = None):
        self.timeout = timeout
        super().__init__(message)


class OllamaModelNotFoundError(OllamaError):
    """Raised when requested model is not available"""

    def __init__(self, message: str, model: str | None = None):
        self.model = model
        super().__init__(message)


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns invalid response"""

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class REQIFParsingError(AITestCaseGeneratorError):
    """Raised when REQIF file parsing fails"""

    def __init__(self, message: str, file_path: str | None = None):
        self.file_path = file_path
        super().__init__(message)


class TestCaseGenerationError(AITestCaseGeneratorError):
    """Raised when test case generation fails"""

    def __init__(self, message: str, requirement_id: str | None = None):
        self.requirement_id = requirement_id
        super().__init__(message)


class ConfigurationError(AITestCaseGeneratorError):
    """Raised when configuration is invalid"""
    pass
