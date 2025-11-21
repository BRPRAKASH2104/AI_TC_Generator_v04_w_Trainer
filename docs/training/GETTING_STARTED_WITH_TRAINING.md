# Getting Started with AI Training: A Beginner's Guide

**Welcome!** This guide is designed for users who are new to AI training. It explains how to "teach" the AI Test Case Generator to understand your specific requirements and diagrams better.

---

## 🤔 What is "Training"?

Think of the default AI model as a generic engineer—it knows a lot about general engineering, but it might not know your company's specific abbreviations, diagram styles, or testing preferences.

**Training** is simply the process of giving the AI "examples" of good work so it can learn your specific style.

**Why should I do this?**
- **Better Accuracy**: The AI learns to interpret your specific diagrams correctly.
- **Less Noise**: It learns to ignore irrelevant information (distractors).
- **Custom Style**: It generates test cases that match your preferred format.

---

## 🛠️ The 3-Step Process

Training isn't a single button press; it's a cycle. We've made it as simple as possible:

1.  **Collect**: You run the tool normally, and it "takes notes."
2.  **Review**: You check the notes (tell the AI what was right/wrong).
3.  **Train**: The AI studies your feedback and creates a new, smarter version of itself.

---

### Phase 1: Collection (The "Passive" Phase)

You don't need to do anything special here other than turning on a setting. The tool will collect data while you work.

1.  **Enable Collection**:
    Open your terminal and run:
    ```bash
    export AI_TG_ENABLE_RAFT=true
    export AI_TG_COLLECT_TRAINING_DATA=true
    ```

2.  **Run as Usual**:
    Generate test cases for your requirements just like you always do:
    ```bash
    ai-tc-generator input/my_requirements.reqifz
    ```

    **What's happening?**
    In the background, the tool is saving copies of the requirements, the diagrams it saw, and the test cases it generated into a `training_data/collected` folder.

---

### Phase 2: Review (The "Teacher" Phase)

This is the most important part. The AI needs you to grade its homework.

1.  **Find the Data**:
    Go to the `training_data/collected` folder. You'll see JSON files (text files with data).

2.  **Annotate (Mark Good/Bad)**:
    *   *Note: This currently requires editing the text files, but it's straightforward.*
    *   Open a file.
    *   Look for `"images"`. If an image is relevant to the test case, mark its `relevance` as `"oracle"`. If it's just noise (like a logo or unrelated chart), mark it as `"distractor"`.
    *   Do the same for text context.

    *Tip: You don't need to do this for everything! Just 50-100 good examples are enough to make a big difference.*

3.  **Move to Validated**:
    Once you're happy with an example, move it to the `training_data/validated` folder. This tells the system "This is ready to be studied."

---

### Phase 3: Training (The "Learning" Phase)

Now that you have a stack of "validated" examples, it's time to let the AI study them.

1.  **Build the Textbook (Dataset)**:
    Run this command to organize your examples into a format the AI can read:
    ```bash
    python3 utilities/build_vision_dataset.py
    ```

2.  **Run the Class (Train)**:
    Run this command to create your custom model:
    ```bash
    python3 utilities/train_vision_model.py
    ```

    *This usually takes less than a minute!*

---

## 🚀 Using Your New Model

Once the training script finishes, it will give you the name of your new model (e.g., `automotive-tc-vision-raft-v1`).

To use it, simply specify it when you run the generator:

```bash
ai-tc-generator input/new_project.reqifz --model automotive-tc-vision-raft-v1
```

**Congratulations!** You are now using a custom-tailored AI model.

---

## ❓ Frequently Asked Questions

**Q: Do I need a supercomputer?**
A: No! The default training method (RAFT) is very lightweight. You can run it on a standard developer laptop (MacBook Pro, etc.).

**Q: How many examples do I need?**
A: Start with **50**. If you want it to be really smart, aim for **100+**.

**Q: Can I mess this up?**
A: Not really. The worst case is the new model isn't much better than the old one. You can always switch back to the default model (`llama3.1:8b`) at any time.

---

*For more technical details, please refer to the `TRAINING_GUIDE.md` in this folder.*
