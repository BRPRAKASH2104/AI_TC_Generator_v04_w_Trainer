While the training functionality is not yet implemented in the current version of the application, it is designed to follow a straightforward, user-centric approach. Here’s how you would approach training the model once the feature is complete:

### The Training Philosophy: Human-in-the-Loop

The training process is designed as a **human-in-the-loop** system. This means your expertise is essential for teaching the AI to generate high-quality test cases that meet your specific needs. You will act as a reviewer, validating or rejecting the AI-generated test cases, and this feedback will be used to fine-tune the model.

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

**Step 3: Review and Curate the Training Data**

This is the most critical step where your expertise comes into play. The application will save the generated test cases in the `training_data/collected` directory. Your task is to review these files and sort them:

*   **If a generated test case is accurate, well-structured, and useful**, you would move it to the `training_data/validated` directory.
*   **If a generated test case is incorrect, poorly formatted, or not useful**, you would move it to the `training_data/rejected` directory.

This manual validation process creates a high-quality dataset that will be used to teach the model what a "good" test case looks like for your specific domain.

**Step 4: Run the Training Process (Future Feature)**

Once you have collected a sufficient number of examples in the `training_data/validated` directory (the `min_examples_for_training` setting in `TrainingConfig` defaults to 50), you would initiate the training process. This would likely be a new command:

```bash
# Hypothetical training command
python main.py --train --model <base_model_to_fine_tune> --new-model-name <your_custom_model_name>
```

This command would:
1.  Use the data in `training_data/validated` to fine-tune the base model (e.g., `llama3.1:8b`).
2.  Employ **LoRA (Low-Rank Adaptation)**, a technique that efficiently creates a specialized "adapter" for the base model.
3.  Save the newly trained custom model with the name you provided.

**Step 5: Use Your Custom-Trained Model**

After the training is complete, you can use your new, specialized model for generating test cases by simply passing its name to the `--model` argument:

```bash
python main.py <path_to_your_reqifz_file> --model <your_custom_model_name>
```

You should see a significant improvement in the quality and relevance of the generated test cases, as the model is now fine-tuned on your own data and expert feedback.

### What You Can Do Now

Even though the training feature is not yet implemented, you can start preparing for it:
*   **Think about your criteria:** Define what constitutes a "good" and "bad" test case for your project. This will make the review process faster and more consistent.
*   **Collect examples:** You can start running the generator and manually saving the output files that you consider good examples. This will give you a head start on building your validated dataset.
