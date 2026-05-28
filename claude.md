# ARC-Challenge Evaluation Implementation Guide

## Your Role
You are an **experienced AI safety researcher** implementing a comprehensive evaluation of a fine-tuned GPT model on the ARC-Challenge benchmark. This assignment is for the Algoverse AI Safety Fellowship, a selective program that assesses:
- Technical competence with ML/AI tools
- Understanding of evaluation and calibration concepts
- Code quality and engineering practices
- Alignment with AI safety thinking (selective prediction, abstention)
- Ability to complete work independently

Your submission is a work sample demonstrating you can contribute meaningfully to AI safety research.

---

## Assignment Overview

### Three-Part Evaluation:
- **Part A**: Accuracy measurement on 299 validation questions
- **Part B**: Calibration analysis using Brier score
- **Part C**: Error footprint (selective accuracy and coverage at 0.99 threshold)

### Required Outputs (EXACT FORMAT):
```
Accuracy: X.X (one decimal, NO "%" symbol)
Brier Score: 0.XXXX (four decimals)
Selective Accuracy: X.X (one decimal, NO "%" symbol)
Coverage: X.X (one decimal, NO "%" symbol)
```

---

## Critical Success Factors (What Reviewers Prioritize)

### 1. Technical Correctness (HIGHEST PRIORITY)
- All three metrics calculated correctly
- Proper API usage (temperature=0, logprobs=True)
- Exact prompt format matching specification
- Correct mathematical implementations

### 2. Attention to Critical Details
**Part A - Common Errors to Avoid:**
- ❌ Wrong dataset split (must be validation, 299 questions)
- ❌ Incorrect prompt format
- ❌ Fixed 4-choice assumption (some have 5+)
- ❌ Brittle answer extraction (must handle "A", "A.", "The answer is A")
- ❌ Wrong temperature (must be 0)
- ❌ Hardcoded API key (use .env)

**Part B - Critical Requirements:**
- Use **first output token** logprob (even if it's "The", not "A")
- Convert logprob to probability: `prob = exp(logprob)`
- Brier formula: `BS = (1/N) * Σ(confidence - o)²`
- Binary outcome: o=1 if correct, o=0 if incorrect

**Part C - Threshold Logic:**
- confidence >= 0.99 → model "answers"
- confidence < 0.99 → model "abstains"
- Selective Accuracy: accuracy ONLY on answered questions
- Coverage: percentage of questions answered

### 3. Shared API Key Awareness
The API key is **public** (all applicants have it), which means:
- Higher rate limit risk from simultaneous usage
- **MUST implement retry logic with exponential backoff**
- Still use .env (shows professional habits)
- Demonstrates understanding of shared resource constraints

### 4. Code Quality Expectations
- Clean, modular functions with single responsibilities
- Meaningful variable/function names
- Comments on non-obvious choices (e.g., first token interpretation)
- Robust error handling (API failures, malformed responses)
- Progress tracking for 299 questions

---

## Implementation Strategy: Modular Approach

### Module Breakdown:
1. **Setup & Configuration** - Environment, imports, constants
2. **Data Loading** - ARC-Challenge dataset handling
3. **Prompt Formatting** - Convert dataset items to required format
4. **API Communication** - Query model with retry logic
5. **Response Parsing** - Extract answer and confidence
6. **Metrics Calculation** - Accuracy, Brier, Selective Accuracy, Coverage
7. **Results Output** - Format and display final metrics

---

## Phase-by-Phase Implementation Checklist

### Phase 1: Environment Setup
```bash
# Checklist:
✓ Create .env file with API key
✓ Create .gitignore with .env entry
✓ Create requirements.txt:
  - openai>=1.0.0
  - datasets>=2.0.0
  - python-dotenv>=0.19.0
  - tqdm>=4.60.0
✓ Install: pip install -r requirements.txt
✓ Verify Python 3.8+
```

**.env file:**
```
OPENAI_API_KEY=your-openai-api-key-here
```

**.gitignore:**
```
.env
__pycache__/
*.pyc
```

### Phase 2: Configuration Constants
```python
# File: arc_evaluation.py
MODEL_ID = "ft:gpt-4.1-nano-2025-04-14:algoverse-ai-safety:arc-v2:CrBuBGfj"
CONFIDENCE_THRESHOLD = 0.99
EXPECTED_DATASET_SIZE = 299
TEMPERATURE = 0
```

### Phase 3: Data Loading Module
**Function: `load_arc_dataset()`**
```python
"""
Checklist:
✓ Import: from datasets import load_dataset
✓ Load: load_dataset("allenai/ai2_arc", "ARC-Challenge", split="validation")
✓ Assert: len(dataset) == 299
✓ Return: dataset object
✓ Handle: Connection errors

Expected structure per item:
- question: str
- choices: {"text": [list], "label": [list]}
- answerKey: str (e.g., "A", "B", "C", "D", "E")
"""
```

### Phase 4: Prompt Formatting Module
**Function: `format_prompt(question_item)`**
```python
"""
Checklist:
✓ Extract question: question_item["question"]
✓ Extract choices: question_item["choices"]
✓ Get labels: choices["label"]
✓ Get texts: choices["text"]
✓ Build EXACT format:
  "<question text>\n"
  "A. <choice A text>\n"
  "B. <choice B text>\n"
  ...
✓ NO trailing newline after last choice
✓ Handle variable choice count (A-E, A-F, etc.)

Example output:
"What is the capital of France?\nA. London\nB. Paris\nC. Berlin\nD. Madrid"
"""
```

### Phase 5: API Communication Module
**Function: `query_model_with_retry(prompt, client, max_retries=5)`**
```python
"""
CRITICAL: Shared API key means rate limits are likely!

Checklist:
✓ Import: from openai import OpenAI, RateLimitError, APIError
✓ Import: time, random, math
✓ Parameters:
  - temperature=0 (EXACT)
  - logprobs=True
  - top_logprobs=5
✓ Retry loop: max 5 attempts
✓ Catch RateLimitError specifically
✓ Exponential backoff: wait = (2 ** attempt) + random.uniform(0, 1)
✓ Print retry messages
✓ Return: full response object

API call format:
response = client.chat.completions.create(
    model=MODEL_ID,
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
    logprobs=True,
    top_logprobs=5
)
"""
```

### Phase 6: Response Parsing Module

**Function: `extract_answer_letter(response_text)`**
```python
"""
Checklist:
✓ Input: response.choices[0].message.content
✓ Strip whitespace
✓ Check patterns (in order):
  1. Starts with single letter: ^[A-Z]
  2. "A." or "A)" format
  3. "answer is A" pattern
  4. First capital letter A-Z
✓ Convert to uppercase
✓ Return: single letter string or None

Test cases:
- "A" → "A"
- "A." → "A"
- "The answer is B" → "B"
- "a" → "A"
"""
```

**Function: `extract_first_token_confidence(response)`**
```python
"""
CRITICAL: Use first token REGARDLESS of what it is!

Checklist:
✓ Access: response.choices[0].logprobs.content[0]
✓ Get logprob: content[0].logprob
✓ Convert: prob = math.exp(logprob)
✓ Return: float (0 to 1)

IMPORTANT: If model outputs "The answer is A", use logprob of "The"
Instructions explicitly say "first output token"
"""
```

### Phase 7: Main Evaluation Loop
**Function: `run_evaluation()`**
```python
"""
Data structure:
results = []  # List of dicts

For each question (0-299):
  ✓ Format prompt
  ✓ Query model with retry
  ✓ Extract answer letter
  ✓ Extract first token confidence
  ✓ Get ground truth: question["answerKey"]
  ✓ Compare: is_correct = (predicted == ground_truth)
  ✓ Store result:
    {
      "idx": i,
      "predicted": predicted_letter,
      "ground_truth": ground_truth,
      "is_correct": bool,
      "confidence": float,
      "above_threshold": confidence >= 0.99
    }
  ✓ Optional: Progress indicator (tqdm)
  ✓ Optional: 0.1s delay between requests

Return: results list
"""
```

### Phase 8: Metrics Calculation

**Function: `calculate_accuracy(results)`**
```python
"""
✓ Count correct: sum(1 for r in results if r["is_correct"])
✓ Count total: len(results)
✓ Calculate: (correct / total) * 100
✓ Round: round(accuracy, 1)
✓ Return: float (NO "%" symbol)

Example: 250/299 → 83.6
"""
```

**Function: `calculate_brier_score(results)`**
```python
"""
Formula: BS = (1/N) * Σ(confidence - outcome)²

✓ For each result:
  - confidence = r["confidence"]
  - outcome = 1 if r["is_correct"] else 0
  - squared_error = (confidence - outcome) ** 2
✓ Sum all squared errors
✓ Divide by 299
✓ Round: round(brier, 4)
✓ Return: float

Expected range: 0.0000 to 1.0000
"""
```

**Function: `calculate_selective_metrics(results, threshold=0.99)`**
```python
"""
✓ Filter answered: confidence >= threshold
✓ Filter abstained: confidence < threshold
✓ Count answered, count correct in answered

Selective Accuracy:
✓ Calculate: (correct_answered / total_answered) * 100
✓ Round: round(sel_acc, 1)
✓ Handle edge case: no questions answered

Coverage:
✓ Calculate: (total_answered / 299) * 100
✓ Round: round(coverage, 1)

Return: (selective_accuracy, coverage)
Both as floats, NO "%" symbols
"""
```

### Phase 9: Results Output
```python
"""
EXACT OUTPUT FORMAT (for submission):

Accuracy: 83.6
Brier Score: 0.1234
Selective Accuracy: 92.5
Coverage: 67.2

NO "%" symbols
Correct decimal places (1 for percentages, 4 for Brier)
"""
```

### Phase 10: Error Handling Checklist
```python
"""
✓ API key not found → Clear error message
✓ Dataset wrong size → Assert and fail
✓ API rate limit → Retry with backoff
✓ Cannot extract answer → Log, mark wrong
✓ Logprobs missing → Raise error (Part B requires)
✓ Division by zero (selective) → Handle edge case
"""
```

---

## Complete Implementation Order

Execute in this sequence:
1. **Configuration** (imports, constants)
2. **Data Loading** (`load_arc_dataset`) - TEST with assert
3. **Formatting** (`format_prompt`) - TEST with samples
4. **Parsing** (`extract_answer_letter`, `extract_confidence`) - TEST
5. **Communication** (`query_model_with_retry`) - TEST with 1-2 questions
6. **Execution** (`run_evaluation`) - Run full 299
7. **Metrics** (calculate all three parts)
8. **Output** (format correctly)
9. **Validation** (verify against requirements)

---

## Critical Pre-Submission Validation

### Verify All Checklist Items:
```
✓ Loaded exactly 299 questions
✓ All 299 processed (no skips)
✓ Accuracy: X.X format (one decimal, no %)
✓ Brier: 0.XXXX format (four decimals)
✓ Selective Accuracy: X.X format (one decimal, no %)
✓ Coverage: X.X format (one decimal, no %)
✓ Math sanity checks:
  - Brier score: ~0.05 to 0.30 range
  - Coverage: 0 to 100
  - Selective Accuracy >= Accuracy (usually)
✓ No hardcoded API key
✓ Has retry logic with exponential backoff
✓ Code runs from scratch without errors
```

---

## Key Insights for AI Safety Researchers

### What This Evaluation Demonstrates:
1. **Calibration** (Part B): How well model confidence matches actual performance
2. **Selective Prediction** (Part C): Safety-critical ability to abstain when uncertain
3. **Coverage-Accuracy Tradeoff**: Higher threshold = higher selective accuracy but lower coverage

### Professional Habits to Demonstrate:
- Use .env even for public/shared key (shows proper practices)
- Implement retry logic (handles shared resource constraints)
- Document non-obvious choices (e.g., first token interpretation)
- Write resilient code (handles API failures gracefully)
- Follow exact specifications (prompt format, rounding, output)

---

## Remember: You're Being Evaluated On

1. **Correctness** - All three parts correctly implemented
2. **Attention to detail** - Exact formats, right precision, right split
3. **Robustness** - Handles edge cases in answer extraction
4. **Code clarity** - Easy to read and understand
5. **Understanding** - Shows grasp of calibration and selective prediction
6. **Professionalism** - Clean code, proper API key handling, clear output

**The winning formula:**
- Start simple, get it working correctly first
- Test thoroughly (especially answer extraction edge cases)
- Clean up and organize code
- Add error handling for API calls
- Document non-obvious choices
- Format output clearly
- Run one final test before submitting
