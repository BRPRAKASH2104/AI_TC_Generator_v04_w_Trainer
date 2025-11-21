# Proposal: Integrating Logprobs for Confidence Scoring and Hallucination Detection

## 1. Objective
Enhance the reliability of the AI Test Case Generator by leveraging Ollama 0.13.0's `logprobs` feature. This will allow the system to:
1.  Assign a **Confidence Score** to each generated test case.
2.  Detect potential **Hallucinations** (especially in signal names).
3.  Identify **Ambiguous Requirements** based on model uncertainty.

## 2. Implementation Strategy

### 2.1. Core Client Updates (`src/core/ollama_client.py`)
The `OllamaClient` and `AsyncOllamaClient` must be updated to request and process log probabilities.

*   **DO**:
    *   Update `generate_response` methods to accept a `request_logprobs` boolean flag.
    *   Modify the API payload to include `"logprobs": True` (or a specific integer like `10` if top-k logprobs are needed, though boolean `True` is usually sufficient for token-level confidence).
    *   Update the return type to include metadata. Instead of returning just `str`, return a `GenerationResult` object or a tuple `(text, metadata)` where metadata contains the logprobs.
    *   Handle backward compatibility: If the Ollama version doesn't support logprobs (older than 0.13.0), gracefully fallback to standard generation without crashing.

*   **DON'T**:
    *   Don't make `logprobs` mandatory for every call. It adds overhead. Only enable it for test case generation, not for simple tasks like summarization.
    *   Don't break the existing `generate_response` signature for all callers. Use optional arguments or a new method if necessary to maintain backward compatibility.

### 2.2. Response Processing (`src/core/generators.py`)
The generator logic needs to calculate scores based on the raw logprobs.

*   **DO**:
    *   Implement a scoring algorithm. A geometric mean of probabilities (exp(average_logprob)) is recommended for a 0-1 confidence score.
    *   Store the calculated `confidence_score` in the test case dictionary.
    *   Implement "Critical Token Analysis": Specifically check the logprobs of tokens that correspond to Signal Names or key actions. If these specific tokens have low probability (e.g., < 0.5), flag the test case as "Potential Hallucination".

*   **DON'T**:
    *   Don't rely solely on the average score. A long response might have a high average score but a single critical hallucinated word with very low probability.
    *   Don't discard low-confidence test cases automatically. Flag them for human review instead.

### 2.3. Output Integration (`src/processors/`)
The confidence scores should be visible to the user.

*   **DO**:
    *   Add a `Confidence` column to the Excel output.
    *   Add a `Review Reason` column to indicate *why* confidence is low (e.g., "Low Signal Probability", "Ambiguous Requirement").
    *   Update the `SemanticValidator` to consider confidence scores as an additional validation signal.

*   **DON'T**:
    *   Don't clutter the CLI output with raw logprob data. Keep it user-friendly (e.g., "High/Medium/Low" or a percentage).

## 3. Technical Specifications

### Data Structures
```python
class TokenLogprob(BaseModel):
    token: str
    logprob: float
    top_logprobs: list[dict] | None = None

class GenerationResult(BaseModel):
    text: str
    logprobs: list[TokenLogprob] | None = None
    confidence_score: float = 0.0
```

### Scoring Logic
```python
def calculate_confidence(logprobs: list[TokenLogprob]) -> float:
    if not logprobs:
        return 0.0
    # Geometric mean of probabilities
    avg_logprob = sum(lp.logprob for lp in logprobs) / len(logprobs)
    return math.exp(avg_logprob)
```

## 4. Verification Plan
1.  **Unit Tests**: Mock Ollama responses with specific logprob patterns to verify scoring logic.
2.  **Integration Tests**: Run against a local Ollama 0.13.0 instance to verify the API payload and response parsing.
3.  **Hallucination Test**: Feed a nonsense requirement and verify that the resulting confidence score is low.

## 5. Migration Guide
1.  Update `OllamaClient` first.
2.  Update `TestCaseGenerator` to use the new client features.
3.  Update Exporters (Excel/JSON) to include the new fields.
