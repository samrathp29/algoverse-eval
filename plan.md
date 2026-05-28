# What Reviewers Look for in AI Safety Fellowship Evaluations Submissions

## Overview
This document analyzes what reviewers will prioritize when grading your Algoverse AI Safety Fellowship take-home challenge submission for the **ARC-Challenge Evaluation** (accuracy, calibration, and error footprint analysis).

## The Assignment
- **Part A**: Accuracy on ARC-Challenge (299 validation questions)
- **Part B**: Calibration analysis using Brier score
- **Part C**: Error footprint (selective accuracy and coverage with 0.99 threshold)

## Assignment-Specific Critical Points

### Part A: Accuracy Measurement - What Can Go Wrong
**Common errors reviewers will catch:**
1. **Wrong dataset split**: Must use validation split (299 questions), not train/test
2. **Incorrect prompt format**: Must exactly match the specified format with letters (A, B, C, D...)
3. **Flexible choice handling**: Some questions have >4 choices - must handle E, F, etc.
4. **Answer extraction bugs**:
   - Model might output "A." or "A)" or just "A" or "The answer is A"
   - Must robustly extract the letter from various formats
   - What if model outputs explanation before/after the letter?
5. **Wrong temperature**: Must use temperature=0 (deterministic)
6. **Accuracy calculation**: Should be (correct / total) * 100, rounded to 1 decimal
7. **API key security**: Should NOT be hardcoded (already a red flag that it's in the instructions)

**What impresses reviewers:**
- Handles all answer extraction edge cases gracefully
- Clear logging showing which questions were answered correctly/incorrectly
- Verification that you loaded exactly 299 questions
- Proper error handling for API failures
- Progress tracking for long-running evaluation

### Part B: Calibration (Brier Score) - Critical Details
**Key technical requirements:**
1. **Correct API parameter**: Use `logprobs=True` in the API call (or similar based on OpenAI's current API)
2. **First token extraction**: Instructions say "log probability of first output token" - not the answer letter specifically
   - What if model outputs "The answer is A"? First token is "The", not "A"
   - This is a potential ambiguity - reviewers want to see you handle this thoughtfully
3. **Probability conversion**: logprob to prob is `prob = exp(logprob)`
4. **Binary outcome**: o = 1 if correct, 0 if incorrect (exact match to ground truth)
5. **Brier score formula**: BS = (1/N) * Σ(confidence - o)²
   - This is mean squared error between confidence and outcome
   - Must accumulate over ALL 299 questions
6. **Rounding**: Report to 4 decimal places (e.g., 0.1234)

**What reviewers are testing:**
- Understanding of calibration concepts
- Ability to work with API's logprobs feature
- Correct mathematical implementation
- Awareness that Brier score measures confidence calibration, not just accuracy

**Potential gotcha:**
- If first token is not the answer letter, you might need to interpret the instruction
- Best approach: document your interpretation clearly in comments

### Part C: Error Footprint - Safety Thinking
**Technical requirements:**
1. **Threshold logic**: confidence >= 0.99 → answer; confidence < 0.99 → abstain
2. **Selective Accuracy**: accuracy computed ONLY on answered questions
   - If model answered 200/299 questions and got 180 correct: 180/200 = 90.0%
3. **Coverage**: percentage of questions answered
   - If model answered 200/299 questions: 200/299 = 66.9%
4. **Rounding**: Both to 1 decimal place

**What this tests (AI Safety perspective):**
- Understanding of selective prediction / abstention
- Tradeoff between coverage and accuracy
- Practical deployment considerations for reliable AI systems
- Ability to analyze model confidence calibration

**What impresses reviewers:**
- Clear explanation that this tests safety-relevant behavior
- Commentary on the coverage/accuracy tradeoff
- Recognition that well-calibrated models should have high selective accuracy
- Optional: analyzing how many abstentions were correct decisions

## IMPORTANT: The Shared/Public API Key Situation

### Why This Matters
The API key was provided in the public assignment document, meaning:
- **All applicants have access to the same key**
- It's a temporary/shared key for this challenge only
- Multiple people are using it simultaneously
- Higher risk of hitting rate limits
- Algoverse will revoke it after the application period

### What Reviewers Are REALLY Testing
This is actually a **clever test** - reviewers want to see if you'll:
1. **Follow best practices anyway** - Use .env even though the key is public
2. **Build resilient code** - Handle rate limits from shared usage
3. **Understand security context** - Recognize this is temporary, but show you know proper practices

### The Paradox: Public Key, But Still Handle Properly
**Even though the key is public, you should:**
- ✅ Use environment variables or .env file
- ✅ Add robust error handling for rate limits
- ✅ Include retry logic with exponential backoff
- ✅ Add small delays between requests to be courteous

**This demonstrates:**
- Professional habits regardless of context
- Understanding: "This is acceptable for a challenge, but not for production"
- Awareness of shared resource constraints
- Ability to write resilient code

### Recommended Implementation for Shared Key

```python
import os
import time
import random
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv

# Load API key from .env (proper practice even for shared key)
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_model_with_retry(prompt, max_retries=5):
    """
    Query with exponential backoff - CRITICAL for shared API key.

    With multiple applicants using the same key, rate limits are likely.
    This handles them gracefully rather than crashing the entire eval.
    """
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                logprobs=True,
                top_logprobs=5  # Get top 5 logprobs for first token
            )
            return response

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise  # Give up after max retries
            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limit hit (attempt {attempt + 1}/{max_retries}), "
                  f"waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

        except APIError as e:
            print(f"API error: {e}, retrying...")
            time.sleep(1)

    raise Exception("Max retries exceeded")

# Optional: Add small delay between requests to be courteous
# time.sleep(0.1)  # 100ms delay
```

### .env File Setup
Create `.env` file:
```
OPENAI_API_KEY=your-openai-api-key-here
```

Add to `.gitignore`:
```
.env
```

### Why This Impresses Reviewers
1. **Security awareness**: You know credentials shouldn't be in code
2. **Professional habits**: You follow best practices even when unnecessary
3. **Engineering maturity**: You understand context but maintain standards
4. **Resilience**: Your code handles real-world constraints (shared resources)
5. **Thoughtfulness**: You recognize the shared key implications

**Bottom line:** The public key makes proper handling MORE important, not less!

## Critical Success Factors

### 1. **Technical Correctness** (Highest Priority)
**What reviewers want to see:**
- Accurate implementation of evaluation metrics
- Proper use of LLM APIs (correct parameter handling, error management)
- Correct statistical analysis if required
- Bug-free code that runs successfully

**Red flags to avoid:**
- Off-by-one errors in accuracy calculations
- Incorrect interpretation of evaluation metrics
- API calls that fail due to improper parameter formatting
- Code that crashes on edge cases

### 2. **Understanding of AI Safety Evaluation Principles**
**What reviewers want to see:**
- Clear understanding of what you're evaluating and why it matters for safety
- Appropriate choice of test cases that probe model behavior
- Recognition of evaluation limitations
- Awareness of potential failure modes

**Demonstrates competence:**
- Well-chosen diverse test cases (not just happy path)
- Comments explaining why specific test cases matter
- Discussion of what the evaluation does/doesn't tell you
- Understanding of evaluation brittleness or gaming potential

### 3. **Code Quality and Organization**
**What reviewers want to see:**
- Clean, readable code with logical structure
- Meaningful variable/function names
- Appropriate code comments (not excessive, but explanatory where needed)
- Modular design with clear separation of concerns

**Structure that impresses:**
```python
# Good structure example:
def load_test_cases(filepath):
    """Load evaluation dataset."""
    ...

def query_model(prompt, model_name="gpt-4"):
    """Query LLM API with error handling."""
    ...

def evaluate_response(response, expected):
    """Score individual response."""
    ...

def run_evaluation():
    """Main evaluation loop."""
    ...

if __name__ == "__main__":
    results = run_evaluation()
    print_summary(results)
```

### 4. **Practical Engineering Skills**
**What reviewers want to see:**
- Proper error handling (API failures, rate limits, malformed responses)
- Configuration management (API keys in .env, not hardcoded)
- Efficient code (batch processing, caching where appropriate)
- Clear output/results presentation

**Best practices:**
- Use environment variables for API keys
- Handle rate limiting gracefully (retries with backoff)
- Cache expensive API calls during development
- Print progress indicators for long-running evaluations
- Save results to file (JSON/CSV) for later analysis

### 5. **Thoughtful Test Design**
**What reviewers want to see:**
- Test cases that actually probe meaningful model behavior
- Diversity in test cases (different difficulty levels, edge cases)
- Clear success criteria for each test
- Understanding of what makes a good evaluation

**Examples of thoughtful test design:**
- Including adversarial examples, not just straightforward cases
- Testing robustness (e.g., typos, unusual formatting)
- Probing safety-relevant behaviors (truthfulness, harmfulness, bias)
- Including cases where you expect the model to refuse or abstain

## Recommended Code Structure

```python
# arc_evaluation.py
"""
ARC-Challenge Evaluation Suite
Evaluates fine-tuned GPT model on accuracy, calibration, and selective prediction.
"""

import os
from openai import OpenAI
from datasets import load_dataset
import math

# Configuration
MODEL_ID = "ft:gpt-4.1-nano-2025-04-14:algoverse-ai-safety:arc-v2:CrBuBGfj"
CONFIDENCE_THRESHOLD = 0.99

def load_arc_dataset():
    """Load ARC-Challenge validation split."""
    dataset = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="validation")
    assert len(dataset) == 299, f"Expected 299 questions, got {len(dataset)}"
    return dataset

def format_prompt(question_data):
    """Format question in required multiple-choice format."""
    # Handle variable number of choices (A, B, C, D, E, ...)
    ...

def query_model(prompt, client):
    """Query OpenAI API with error handling and logprobs."""
    # Include temperature=0 and logprobs request
    ...

def extract_answer(response_text):
    """Robustly extract answer letter from model output."""
    # Handle various formats: "A", "A.", "A)", "The answer is A"
    ...

def get_confidence_from_logprobs(logprobs_data):
    """Extract probability of first token."""
    # Convert logprob to probability
    ...

def calculate_brier_score(confidences, outcomes):
    """Calculate Brier score for calibration."""
    ...

def run_evaluation():
    """Main evaluation loop."""
    # Part A: Accuracy
    # Part B: Collect confidences
    # Part C: Apply threshold and compute metrics
    ...

if __name__ == "__main__":
    results = run_evaluation()
    print_results(results)
```

## What Distinguishes Strong Submissions for THIS Task

### Tier 1 (Exceptional) - What gets you noticed:
1. **Code quality:**
   - Clean modular functions with clear single responsibilities
   - Comprehensive error handling (API rate limits, malformed responses)
   - Progress tracking (e.g., tqdm progress bar for 299 questions)
   - Results saved to JSON file for reproducibility

2. **Technical correctness:**
   - All three metrics calculated correctly
   - Robust answer extraction that handles edge cases
   - Proper logprobs handling
   - Correct mathematical implementations

3. **Documentation:**
   - Clear docstrings explaining each function
   - Comments on non-obvious choices (e.g., first token interpretation)
   - Results clearly formatted and labeled
   - Brief analysis of what the metrics indicate

4. **Going slightly beyond (optional but impressive):**
   - Simple error analysis (which types of questions were hardest?)
   - Confidence distribution histogram
   - Comparison of abstained vs. answered questions
   - Discussion of calibration quality

5. **Professional touches:**
   - requirements.txt file
   - .env file for API key (not hardcoded)
   - Clear output format showing all required metrics
   - Code runs without modification

### Tier 2 (Strong) - Solid submission:
1. All three parts implemented correctly
2. Clean, readable code with basic structure
3. Handles most edge cases
4. Basic error handling
5. Outputs all required metrics with correct precision
6. API key in .env or documented as needed
7. Code runs successfully

### Tier 3 (Acceptable) - Meets requirements:
1. All three parts complete and mostly correct
2. May have minor bugs in edge cases
3. Basic organization but not polished
4. Minimal error handling
5. Outputs required numbers
6. Works but needs some cleanup

### Red Flags (What loses points):
1. **Incorrect metrics** - wrong formula implementations
2. **Hardcoded API key** in source code
3. **Wrong dataset split** - using test instead of validation
4. **Prompt format errors** - not matching exact specification
5. **No error handling** - crashes on API failures
6. **Unclear output** - reviewers can't find your answers
7. **Code doesn't run** - missing dependencies, syntax errors
8. **Wrong precision** - not rounding as specified

## Documentation Recommendations

### Code Comments - Where to Add Them:
1. **Top of file**: Brief description of what evaluation does
2. **Complex logic**: Explain non-obvious algorithmic choices
3. **Safety-relevant decisions**: Why certain test cases or thresholds matter
4. **API parameters**: Document important parameter choices

### What NOT to comment:
- Obvious code (`x = x + 1  # increment x`)
- Standard library usage
- Self-explanatory variable assignments

### Consider including:
```python
"""
Evaluation: [Name of What You're Testing]

This evaluation measures [specific capability/safety property].
Test cases include [brief description].

Expected runtime: ~[X] minutes
API calls: ~[Y] tokens
"""
```

## Time Management and Completeness

### Reviewers understand time constraints
- **Partial solutions are acceptable** - they say so explicitly
- Better to do one section very well than both poorly
- Show your best work on what you complete

### What to prioritize:
1. **Core functionality working** (can run and get results)
2. **Correctness** (right answers)
3. **Code clarity** (reviewable code)
4. **Error handling** (doesn't crash)
5. **Advanced features** (nice-to-have)

### If running out of time:
- Focus on getting basic evaluation working correctly
- Add TODO comments for improvements you'd make
- Document known limitations
- Clean up what you have rather than rushing to add more

## Common Pitfalls to Avoid (Assignment-Specific)

### Data Loading Issues:
1. **Wrong split**: Using train or test instead of validation (299 questions)
2. **Wrong dataset**: Loading ARC-Easy instead of ARC-Challenge
3. **Not verifying count**: Should confirm 299 questions loaded

### Prompt Formatting Issues:
4. **Fixed choice count**: Assuming exactly 4 choices (some have 5!)
5. **Missing letters**: Not handling choices E, F, etc.
6. **Format deviation**: Not exactly matching the required format
   ```
   <question text>
   A. <choice A>
   B. <choice B>
   ...
   ```

### API Call Issues:
7. **Missing temperature=0**: Results won't be deterministic
8. **Missing logprobs**: Part B requires logprobs=True
9. **Wrong logprobs parameter**: Check current OpenAI API documentation
10. **API key in code**: Should use environment variable or .env file
11. **No rate limiting**: Making 299 API calls too fast may hit limits
12. **No retry logic**: Single API failure causes entire eval to crash

### Answer Extraction Issues:
13. **Brittle parsing**: Only handles "A" but model outputs "A."
14. **No fallback**: What if model refuses to answer or says "unclear"?
15. **Case sensitivity**: Model outputs lowercase "a" instead of "A"

### Metric Calculation Issues:
16. **Wrong Brier formula**: Using max probability instead of first token probability
17. **Log/probability confusion**: Forgetting to convert logprob with exp()
18. **Integer division**: Using / instead of // or vice versa
19. **Off-by-one**: Accuracy as 0-100 integer instead of percentage
20. **Wrong threshold comparison**: Using > instead of >= for 0.99
21. **Selective accuracy on wrong set**: Including abstentions in denominator

### Output Issues:
22. **Wrong precision**: Not rounding to specified decimal places
23. **Unlabeled numbers**: Printing "85.2" without saying what it is
24. **Missing metrics**: Forgetting to print one of the required values

## Final Impression Factors

### Strong positive signals:
- Code runs on first try
- Clear README or docstring explaining what it does
- Sensible project structure
- Evidence of testing (code works, handles errors)
- Thoughtful test case selection
- Clear understanding of evaluation's purpose

### Negative signals:
- Code doesn't run
- No error handling
- Hardcoded API keys in code
- Unclear what evaluation is testing
- No comments or documentation
- Sloppy code organization
- Incorrect metric calculations

## Recommended Workflow

1. **Understand requirements thoroughly**
2. **Start with simple working version**
3. **Test incrementally** (don't write everything then test)
4. **Refactor for clarity** once working
5. **Add error handling** to critical paths
6. **Document key decisions** in comments
7. **Review your code** as if you're the reviewer
8. **Test one more time** before submission

## Pre-Submission Checklist

### Functionality:
- [ ] Loads exactly 299 questions from ARC-Challenge validation split
- [ ] Prompt format exactly matches specification (with A., B., C., etc.)
- [ ] Handles questions with >4 answer choices (E, F, etc.)
- [ ] API calls use temperature=0
- [ ] API calls request logprobs
- [ ] Robustly extracts answer letter from various output formats
- [ ] Correctly calculates accuracy (as percentage, 1 decimal)
- [ ] Correctly calculates Brier score (4 decimals)
- [ ] Correctly applies 0.99 threshold for abstention
- [ ] Correctly calculates selective accuracy (only on answered questions)
- [ ] Correctly calculates coverage (percentage answered)

### Code Quality:
- [ ] Functions have clear single purposes
- [ ] Meaningful variable names
- [ ] Key decisions commented (e.g., first token interpretation)
- [ ] No hardcoded API key in source code
- [ ] API key loaded from .env file using python-dotenv
- [ ] .env added to .gitignore
- [ ] Retry logic with exponential backoff for rate limits
- [ ] Basic error handling for API failures
- [ ] Code is organized and readable

### Output:
- [ ] All five metrics clearly labeled:
  - Part A: Accuracy (X.X%)
  - Part B: Brier Score (0.XXXX)
  - Part C: Selective Accuracy (X.X%)
  - Part C: Coverage (X.X%)
- [ ] Output is easy for reviewers to read and verify
- [ ] Consider saving results to JSON for reproducibility

### Professional Touches (Nice to Have):
- [ ] requirements.txt with dependencies (openai, datasets, python-dotenv, tqdm)
- [ ] .env file for API key with .env.example template
- [ ] Progress indicator for long-running evaluation (e.g., tqdm)
- [ ] Brief comment explaining what evaluation measures
- [ ] Code runs without modification
- [ ] Handles shared API key gracefully (retry logic for rate limits)

### Final Test:
- [ ] Run your code from scratch in a fresh environment
- [ ] Verify all metrics are calculated correctly
- [ ] Check that output matches required format and precision
- [ ] Confirm code handles edge cases (model outputs unusual formats)

## Remember

This is a **selective program** - reviewers are assessing:
- Technical competence with ML/AI tools
- Understanding of evaluation and calibration concepts
- Code quality and engineering practices
- Alignment with AI safety thinking (e.g., understanding selective prediction)
- Ability to complete work independently

Your submission is a work sample that demonstrates you can contribute meaningfully to AI safety research.

## Key Takeaways

**What matters most for THIS specific assignment:**

1. **Correctness** - All three parts correctly implemented
2. **Attention to detail** - Exact prompt format, right precision, right dataset split
3. **Robustness** - Handles edge cases in answer extraction
4. **Code clarity** - Easy to read and understand
5. **Understanding** - Shows you grasp calibration and selective prediction concepts
6. **Professionalism** - Clean code, proper API key handling, clear output

**The winning formula:**
- Start simple, get it working correctly first
- Test thoroughly (especially answer extraction edge cases)
- Clean up and organize code
- Add error handling for API calls
- Document non-obvious choices
- Format output clearly
- Run one final test before submitting
