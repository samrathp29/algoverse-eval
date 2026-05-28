import os
import time
import random
import math
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError
from datasets import load_dataset

load_dotenv()

MODEL_ID = "ft:gpt-4.1-nano-2025-04-14:algoverse-ai-safety:arc-v2:CrBuBGfj"
CONFIDENCE_THRESHOLD = 0.99
EXPECTED_DATASET_SIZE = 299
TEMPERATURE = 0
MAX_RETRIES = 5

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_arc_dataset():
    """Load ARC-Challenge validation split (299 questions)."""
    try:
        dataset = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="validation")
        actual_size = len(dataset)
        assert actual_size == EXPECTED_DATASET_SIZE, \
            f"Expected {EXPECTED_DATASET_SIZE} questions, got {actual_size}"
        return dataset
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise


def format_prompt(question_item: Dict[str, Any]) -> str:
    """
    Format question in required multiple-choice format.

    Handles variable number of choices (some questions have 5+ choices).
    Returns prompt with no trailing newline.
    """
    question_text = question_item["question"]
    choices = question_item["choices"]
    labels = choices["label"]
    texts = choices["text"]

    prompt_parts = [question_text]
    for label, text in zip(labels, texts):
        prompt_parts.append(f"{label}. {text}")

    return "\n".join(prompt_parts)


def query_model_with_retry(prompt: str) -> Any:
    """
    Query OpenAI API with exponential backoff retry logic.

    Shared API key means rate limits are highly likely - this handles them
    gracefully to prevent the evaluation from crashing.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE,
                logprobs=True,
                top_logprobs=5
            )
            return response

        except RateLimitError as e:
            if attempt == MAX_RETRIES - 1:
                print(f"Rate limit exceeded after {MAX_RETRIES} attempts")
                raise

            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}), "
                  f"waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

        except APIError as e:
            if attempt == MAX_RETRIES - 1:
                print(f"API error after {MAX_RETRIES} attempts: {e}")
                raise

            print(f"API error: {e}, retrying...")
            time.sleep(1)

    raise Exception("Max retries exceeded")


def extract_answer_letter(response_text: str) -> Optional[str]:
    """
    Extract answer letter from model response.

    Handles various formats: "A", "A.", "The answer is A", lowercase, etc.
    Uses multiple extraction strategies in order of specificity.
    """
    import re

    if not response_text:
        return None

    text = response_text.strip()

    if len(text) == 1 and text.upper() in "ABCDEFGHIJ":
        return text.upper()

    match = re.match(r'^([A-Ja-j])[.)\s]', text)
    if match:
        return match.group(1).upper()

    match = re.search(r'(?:answer is|answer:|is)\s+([A-Ja-j])\b', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.search(r'\b([A-J])\b', text)
    if match:
        return match.group(1)

    match = re.search(r'([A-J])', text)
    if match:
        return match.group(1)

    return None


def extract_first_token_confidence(response: Any) -> float:
    """
    Extract probability from first output token's logprob.

    CLARIFICATION FOR SELF: Uses the FIRST token's logprob, 
    regardless of whether that token is the answer letter. 
    e.g., if model outputs "The answer is A", we use the
    logprob of "The", NOT "A".
    """
    try:
        logprobs_data = response.choices[0].logprobs

        if not logprobs_data or not logprobs_data.content:
            raise Exception("Logprobs not available in response")

        first_token_logprob = logprobs_data.content[0].logprob
        probability = math.exp(first_token_logprob)

        return probability

    except (AttributeError, IndexError, TypeError) as e:
        raise Exception(f"Failed to extract confidence from logprobs: {e}")


def run_evaluation(dataset) -> List[Dict[str, Any]]:
    """
    Run evaluation on all 299 questions.

    Includes 0.1s delay between requests to reduce rate limit risk.
    Continues on extraction failures (marks as incorrect).
    """
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False

    results = []
    iterator = tqdm(dataset, desc="Evaluating questions") if use_tqdm else dataset

    for idx, question_item in enumerate(iterator):
        try:
            prompt = format_prompt(question_item)
            response = query_model_with_retry(prompt)
            response_text = response.choices[0].message.content
            predicted = extract_answer_letter(response_text)
            confidence = extract_first_token_confidence(response)
            ground_truth = question_item["answerKey"]
            is_correct = (predicted == ground_truth) if predicted else False
            above_threshold = confidence >= CONFIDENCE_THRESHOLD

            results.append({
                "idx": idx,
                "question": question_item["question"],
                "predicted": predicted,
                "ground_truth": ground_truth,
                "is_correct": is_correct,
                "confidence": confidence,
                "above_threshold": above_threshold,
                "response_text": response_text,
            })

            time.sleep(0.1)

        except Exception as e:
            print(f"Error on question {idx}: {e}")

            results.append({
                "idx": idx,
                "question": question_item["question"],
                "predicted": None,
                "ground_truth": question_item["answerKey"],
                "is_correct": False,
                "confidence": 0.0,
                "above_threshold": False,
                "response_text": "",
            })

    return results


def calculate_accuracy(results: List[Dict[str, Any]]) -> float:
    """Calculate overall accuracy as percentage (rounded to 1 decimal)."""
    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])
    accuracy = (correct / total) * 100 if total > 0 else 0.0
    return round(accuracy, 1)


def calculate_brier_score(results: List[Dict[str, Any]]) -> float:
    """
    Calculate Brier score

    Measures calibration quality (lower is better, range 0.0-1.0).
    """
    total = len(results)
    if total == 0:
        return 0.0

    squared_errors = []
    for r in results:
        confidence = r["confidence"]
        outcome = 1.0 if r["is_correct"] else 0.0
        squared_error = (confidence - outcome) ** 2
        squared_errors.append(squared_error)

    brier_score = sum(squared_errors) / total
    return round(brier_score, 4)


def calculate_selective_metrics(
    results: List[Dict[str, Any]],
    threshold: float = 0.99
) -> tuple[float, float]:
    """
    Calculate selective accuracy and coverage.

    Model "answers" when confidence >= threshold, otherwise "abstains".
    Returns (selective_accuracy, coverage) as percentages.
    """
    total = len(results)
    if total == 0:
        return 0.0, 0.0

    answered = [r for r in results if r["confidence"] >= threshold]

    if len(answered) > 0:
        correct_answered = sum(1 for r in answered if r["is_correct"])
        selective_accuracy = (correct_answered / len(answered)) * 100
    else:
        selective_accuracy = 0.0

    coverage = (len(answered) / total) * 100
    return round(selective_accuracy, 1), round(coverage, 1)


def main():
    """Main execution function."""
    dataset = load_arc_dataset()
    results = run_evaluation(dataset)

    accuracy = calculate_accuracy(results)
    brier_score = calculate_brier_score(results)
    selective_accuracy, coverage = calculate_selective_metrics(
        results,
        threshold=CONFIDENCE_THRESHOLD
    )

    print()
    print(f"Accuracy: {accuracy}")
    print(f"Brier Score: {brier_score}")
    print(f"Selective Accuracy: {selective_accuracy}")
    print(f"Coverage: {coverage}")


if __name__ == "__main__":
    main()
