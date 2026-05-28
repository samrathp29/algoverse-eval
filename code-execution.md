Implementation Strategy: Modular Approach
This document outlines the systematic breakdown and hyper-specific checklist for evaluating the ARC-Challenge dataset against the specified GPT-4 fine-tuned model.

Module Breakdown
Setup & Configuration – Environment, imports, constants.

Data Loading – ARC-Challenge dataset handling.

Prompt Formatting – Convert dataset items to required format.

API Communication – Query model with retry logic.

Response Parsing – Extract answer and confidence.

Metrics Calculation – Accuracy, Brier, Selective Accuracy, Coverage.

Results Output – Format and display final metrics.

Phase 1: Environment Setup
[x] Create .env file with API key (exact string from assignment).

[x] Create .gitignore with .env entry.

[x] Create requirements.txt with exact versions:

openai>=1.0.0

datasets>=2.0.0

python-dotenv>=0.19.0

tqdm>=4.60.0 (optional for progress)

[x] Install packages: pip install -r requirements.txt

[x] Verify Python 3.8+ (for OpenAI SDK).

Phase 2: Configuration Constants
File: arc_evaluation.py

Python
MODEL_ID = "ft:gpt-4.1-nano-2025-04-14:algoverse-ai-safety:arc-v2:CrBuBGfj"
CONFIDENCE_THRESHOLD = 0.99
EXPECTED_DATASET_SIZE = 299
TEMPERATURE = 0
Phase 3: Data Loading Module
Function: load_arc_dataset()

[x] Import: from datasets import load_dataset

[x] Call: load_dataset("allenai/ai2_arc", "ARC-Challenge", split="validation")

[x] Assert: len(dataset) == 299

[x] Return: dataset object

[x] Handle: Connection errors, dataset not found

Expected dataset structure per item:

question: str

choices: {"text": [list], "label": [list]}

answerKey: str (e.g., "A", "B", "C", "D", "E")

Phase 4: Prompt Formatting Module
Function: format_prompt(question_item)

[x] Extract question text: question_item["question"]

[x] Extract choices: question_item["choices"]

[x] Get labels: choices["label"] (e.g., ["A", "B", "C", "D"])

[x] Get texts: choices["text"]

[x] Build prompt EXACTLY as:

Plaintext
<question text>
A. <choice A text>
B. <choice B text>
...
[x] No trailing newline after last choice.

[x] Test with 4-choice and 5-choice questions.

Example output:

"What is the capital of France?\nA. London\nB. Paris\nC. Berlin\nD. Madrid"

Phase 5: API Communication Module
Function: query_model_with_retry(prompt, client, max_retries=5)

[x] Imports: from openai import OpenAI, RateLimitError, APIError, import time, random, math

[x] Parameters: temperature=0, logprobs=True, top_logprobs=5

[x] Retry Loop: Wrap in retry loop (max 5 attempts).

[x] Error Handling: Catch RateLimitError specifically.

[x] Backoff: wait = (2 ** attempt) + random.uniform(0, 1)

[x] Return: full response object.

Phase 6: Response Parsing Module
Function: extract_answer_letter(response_text)

[x] Input: response.choices[0].message.content

[x] Strip whitespace: text.strip()

[x] Check patterns:

Starts with single letter: ^[A-Z]

Starts with "A." or "A)" format

Contains "answer is A" or "is A"

Look for first capital letter A-Z

[x] Handle cases: Convert to uppercase; handle "The answer is A" → "A".

Function: extract_first_token_confidence(response)

[x] Access: response.choices[0].logprobs.content[0]

[x] Convert: math.exp(logprob)

[x] CRITICAL: Use first token REGARDLESS of content (e.g., if it starts with "The", use "The").

Phase 7: Main Evaluation Loop
Function: run_evaluation()

For each question (0–299):

Format prompt.

Query model with retry.

Extract answer letter & first token confidence.

Get ground truth: question["answerKey"].

Compare: is_correct = (predicted == ground_truth).

Store in results list of dicts.

Phase 8: Metrics Calculation
Accuracy

formula: (correct / total) * 100

Format: Round to 1 decimal (e.g., 83.6).

Brier Score

Formula: BS= 
N
1
​	
 ∑(confidence−outcome) 
2
 

Format: Round to 4 decimals (e.g., 0.1234).

Selective Metrics (Threshold = 0.99)

Selective Accuracy: Accuracy only on items where confidence >= 0.99.

Coverage: percentage of total items where confidence >= 0.99.

Phase 9: Results Output
Exact Submission Format (Numbers Only):

Accuracy: 83.6 Brier Score: 0.1234 Selective Accuracy: 92.5 Coverage: 67.2

Phase 10: Error Handling Checklist
[x] API key not found → Clear error message.

[x] Dataset wrong size → Assert and fail loudly.

[x] API rate limit → Retry with backoff.

[x] Cannot extract answer → Log warning, mark as wrong.

[x] Logprobs missing → Raise error (required for Part B).

Complete Implementation Order
Configuration (Imports, constants)

Data Loading (load_arc_dataset)

Formatting (format_prompt)

Parsing (extract_answer_letter & extract_confidence)

Communication (query_model_with_retry)

Execution (run_evaluation)

Math (Metric calculations)

Validation (Verify output against requirements)