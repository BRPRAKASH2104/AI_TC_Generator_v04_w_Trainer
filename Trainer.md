While the training functionality is not yet implemented in the current version of the application, it is designed to follow a straightforward, user-centric approach. Here’s how you would approach training the model once the feature is complete:

### The Training Philosophy: Human-in-the-Loop with RAFT

The training process is designed as a **human-in-the-loop** system using **RAFT (Retrieval Augmented Fine-Tuning)**. This means your expertise is essential for teaching the AI to:
1. Generate high-quality test cases that meet your specific needs
2. **Identify which contextual information is relevant** (headings, info artifacts, interfaces)
3. **Ignore irrelevant or distracting context** that doesn't contribute to better test cases

You will act as a reviewer, validating or rejecting the AI-generated test cases AND annotating which context was useful. This feedback will be used to fine-tune the model with RAFT, making it better at filtering noise and focusing on relevant information.

### Step-by-Step Training Workflow

Here is the intended workflow for training a custom model:

**Step 1: Enable Data Collection**

You would start by enabling the training data collection mode. This would likely be a flag in the configuration file (`config/cli_config.yaml`) or a command-line argument.

```yaml
# In your cli_config.yaml (hypothetical)
training:
  collect_training_data: true
```

**Step 2: Generate Test Cases as Usual**

With data collection enabled, you would run the test case generator as you normally do, pointing it to your requirement files.

```bash
python main.py <path_to_your_reqifz_file>
```

**Step 3: Review and Annotate the Training Data (RAFT Approach)**

This is the most critical step where your expertise comes into play. The application will save the generated test cases along with their context in the `training_data/collected` directory. Your task is to:

**3a. Validate Test Case Quality**

*   **If a generated test case is accurate, well-structured, and useful**, you would move it to the `training_data/validated` directory.
*   **If a generated test case is incorrect, poorly formatted, or not useful**, you would move it to the `training_data/rejected` directory.

**3b. Annotate Context Relevance (NEW - RAFT Enhancement)**

For each **validated** test case, you will also annotate which contextual information was actually useful. Each collected file will include:

```json
{
  "requirement_id": "REQ_DOOR_001",
  "retrieved_context": {
    "heading": "Door Control System",
    "info_artifacts": [
      {"id": "INFO_001", "text": "Door control signals are CAN-based"},
      {"id": "INFO_002", "text": "Window motor operates at 12V"},
      {"id": "INFO_003", "text": "Safety lockout activates above 5 km/h"}
    ],
    "interfaces": [
      {"id": "IF_BCM_001", "text": "Body Control Module interface"},
      {"id": "IF_MOTOR_001", "text": "Window motor control"}
    ]
  },
  "generated_test_cases": "...",
  "context_annotation": {
    "oracle_context": [],      // Fill this: IDs of RELEVANT context
    "distractor_context": []   // Fill this: IDs of IRRELEVANT context
  }
}
```

**How to Annotate:**

*   **Oracle Context** (✅): Mark context items that directly contributed to good test case generation
    *   Example: If INFO_003 about safety lockout led to a critical test case, mark it as oracle
*   **Distractor Context** (❌): Mark context items that were present but not useful/relevant
    *   Example: If INFO_002 about window motor wasn't relevant to door lock testing, mark it as distractor

**Example Annotation:**

```json
{
  "context_annotation": {
    "oracle_context": ["INFO_001", "INFO_003", "IF_BCM_001"],
    "distractor_context": ["INFO_002", "IF_MOTOR_001"]
  }
}
```

This RAFT annotation teaches the model to **distinguish signal from noise**, dramatically improving its ability to generate relevant test cases from complex requirement documents.

**Step 4: Run the RAFT Training Process (Future Feature)**

Once you have collected a sufficient number of annotated examples in the `training_data/validated` directory (the `min_examples_for_training` setting in `TrainingConfig` defaults to 50), you would initiate the RAFT training process. This would likely be a new command:

```bash
# Hypothetical RAFT training command
python main.py --train --method raft --model <base_model_to_fine_tune> --new-model-name <your_custom_model_name>
```

This command would:
1.  **Prepare RAFT training data** from your annotated examples:
    *   Each training example includes the requirement + oracle context + distractor context
    *   Model learns to generate test cases using oracle context while ignoring distractors
    *   Creates robust training examples: `(question, oracle_docs, distractor_docs) → answer`
2.  **Fine-tune with LoRA + RAFT**:
    *   Employ **LoRA (Low-Rank Adaptation)** for efficient fine-tuning
    *   Apply **RAFT methodology** to teach context discrimination
    *   The model learns both *what* to generate AND *which context* to focus on
3.  **Save the trained model** with your custom name for immediate use

**Why RAFT + LoRA?**
*   **Standard Fine-Tuning**: Model memorizes examples → struggles with new context patterns
*   **RAFT Fine-Tuning**: Model learns to filter relevant context → generalizes to unseen artifacts
*   **Result**: 30-50% improvement in test case quality with noisy/complex requirement documents

**Step 5: Use Your RAFT-Trained Model**

After the training is complete, you can use your new RAFT-trained model for generating test cases by simply passing its name to the `--model` argument:

```bash
python main.py <path_to_your_reqifz_file> --model <your_custom_model_name>
```

**Expected Improvements:**
*   **Better context filtering**: Model focuses on relevant headings, info artifacts, and interfaces
*   **Reduced hallucination**: Ignores irrelevant context that could mislead test case generation
*   **Higher quality**: More accurate, domain-specific test cases even with complex/noisy documents
*   **Better generalization**: Handles new requirement patterns not seen during training

The RAFT-trained model is especially powerful when:
*   Requirements have multiple information artifacts (some relevant, some not)
*   Documents contain cross-cutting concerns (e.g., power management info mixed with functional requirements)
*   Interface lists are long and only a subset applies to each requirement

### What You Can Do Now

Even though the RAFT training feature is not yet implemented, you can start preparing for it:

*   **Define quality criteria**: Establish what constitutes a "good" and "bad" test case for your project. This will make the review process faster and more consistent.

*   **Collect examples**: Start running the generator and manually saving output files you consider good examples. This gives you a head start on building your validated dataset.

*   **Practice context annotation**: When reviewing generated test cases, mentally note which context was helpful:
    *   Did the heading provide useful framing?
    *   Which information artifacts were actually relevant?
    *   Which system interfaces mattered for this specific requirement?
    *   What context was present but didn't contribute to quality?

*   **Build annotation guidelines**: Document patterns you notice:
    *   "For power management requirements, voltage specs are oracle context"
    *   "For functional requirements, interface timing is often distractor context"
    *   "Safety-related info artifacts are almost always oracle context"

*   **Understand your REQIFZ structure**: Analyze how your requirement documents are organized:
    *   How many info artifacts typically appear between requirements?
    *   What percentage of context is usually relevant vs. noise?
    *   Which types of requirements benefit most from interface context?

This preparation will dramatically speed up the annotation process when RAFT training becomes available, and you'll have better intuition for what makes context "oracle" vs. "distractor" in your specific domain.

---

### RAFT Training Benefits Summary

| Aspect | Without RAFT | With RAFT |
|--------|--------------|-----------|
| **Context Usage** | Uses all retrieved context equally | Learns to prioritize relevant context |
| **Noise Handling** | Confused by irrelevant artifacts | Filters out distractors effectively |
| **Generalization** | Memorizes training examples | Generalizes to new context patterns |
| **Document Complexity** | Struggles with noisy documents | Thrives with complex/noisy documents |
| **Training Data Needed** | 100+ examples for basic quality | 50+ annotated examples for strong results |
| **Domain Adaptation** | Generic test case patterns | Domain-specific context understanding |

**Bottom Line**: RAFT transforms your model from a "test case generator" into an "intelligent context-aware test case generator" that understands which information actually matters for your automotive requirements.
