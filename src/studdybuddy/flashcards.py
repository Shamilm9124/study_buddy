import json
import re
from pathlib import Path
from typing import Any

from studdybuddy.crew import Studdybuddy


CHECK_MARK = "\u2713"

FLASHCARD_PROMPT = """Create an on-demand study summary and flashcards from this CURRENT conversation only.

Return only valid JSON. Do not include markdown fences or commentary.

Required shape:
{
  "summary": ["Concept 1", "Concept 2", "Concept 3"],
  "cards": [
    {
      "title": "Short concept title",
      "question": "Clear flashcard question",
      "answer": "Concise answer"
    }
  ]
}

Rules:
- Include 4 to 5 summary concepts.
- Include 3 to 5 flashcards.
- Each card must have title, question, and answer.
- Base every item only on the conversation below.

Conversation:
{conversation}
"""

QUIZ_PROMPT = """Create an on-demand multiple-choice quiz from this CURRENT conversation only.

Return only valid JSON. Do not include markdown fences or commentary.

Required shape:
{
  "summary": ["Concept 1", "Concept 2", "Concept 3"],
  "questions": [
    {
      "title": "Short concept title",
      "question": "Clear multiple-choice question",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Concise explanation of why the answer is correct"
    }
  ]
}

Rules:
- Include 2 to 3 summary concepts.
- Include exactly 5 MCQ questions.
- Each question must have exactly 4 options.
- correct_index must be 0, 1, 2, or 3.
- Make distractors plausible but clearly incorrect.
- Base every item only on the conversation below.

Conversation:
{conversation}
"""

OUTPUT_DIR = Path("output")
FLASHCARDS_PATH = OUTPUT_DIR / "flashcards.json"


def conversation_to_text(messages: list[dict[str, str]]) -> str:
    """Format Streamlit chat history for the flashcard-generation prompt."""
    lines = []
    for message in messages:
        role = "Student" if message.get("role") == "user" else "StudyBuddy"
        content = message.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n\n".join(lines)


def generate_flashcards(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Generate flashcards on demand from the supplied conversation."""
    conversation = conversation_to_text(messages)
    if not conversation:
        raise ValueError("No conversation is available for flashcards yet.")

    prompt = FLASHCARD_PROMPT.replace("{conversation}", conversation)
    result = Studdybuddy().learning_guide().kickoff(prompt)
    return normalize_flashcards(parse_flashcards_json(result.raw.strip()))


def generate_quiz(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Generate MCQ quiz items on demand from the supplied conversation."""
    conversation = conversation_to_text(messages)
    if not conversation:
        raise ValueError("No conversation is available for a quiz yet.")

    prompt = QUIZ_PROMPT.replace("{conversation}", conversation)
    result = Studdybuddy().learning_guide().kickoff(prompt)
    return normalize_quiz(parse_flashcards_json(result.raw.strip()))


def parse_flashcards_json(raw_output: str) -> dict[str, Any]:
    """Parse CrewAI output, accepting plain JSON or a single fenced JSON block."""
    cleaned = raw_output.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("Flashcard generation did not return JSON.")
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Flashcard generation returned an invalid format.")
    return parsed


def normalize_flashcards(data: dict[str, Any]) -> dict[str, Any]:
    """Keep the stored shape predictable for the Streamlit UI and JSON file."""
    summary = data.get("summary", [])
    cards = data.get("cards", [])

    if not isinstance(summary, list):
        summary = []
    if not isinstance(cards, list):
        cards = []

    clean_summary = [
        str(item).strip()
        for item in summary
        if str(item).strip()
    ][:3]

    clean_cards = []
    for card in cards[:3]:
        if not isinstance(card, dict):
            continue
        clean_cards.append(
            {
                "title": str(card.get("title", "")).strip(),
                "question": str(card.get("question", "")).strip(),
                "answer": str(card.get("answer", "")).strip(),
            }
        )

    if not clean_summary:
        clean_summary = ["Conversation review"]
    if not clean_cards:
        raise ValueError("Flashcard generation did not produce any cards.")

    return {"summary": clean_summary, "cards": clean_cards}


def normalize_quiz(data: dict[str, Any]) -> dict[str, Any]:
    """Keep MCQ quiz output predictable for the browser UI."""
    summary = data.get("summary", [])
    questions = data.get("questions", [])

    if not isinstance(summary, list):
        summary = []
    if not isinstance(questions, list):
        questions = []

    clean_summary = [
        str(item).strip()
        for item in summary
        if str(item).strip()
    ][:3]

    clean_questions = []
    for question in questions[:5]:
        if not isinstance(question, dict):
            continue

        options = question.get("options", [])
        if not isinstance(options, list):
            options = []
        clean_options = [
            str(option).strip()
            for option in options
            if str(option).strip()
        ][:4]
        if len(clean_options) != 4:
            continue

        try:
            correct_index = int(question.get("correct_index", 0))
        except (TypeError, ValueError):
            correct_index = 0
        correct_index = max(0, min(3, correct_index))

        clean_questions.append(
            {
                "title": str(question.get("title", "")).strip(),
                "question": str(question.get("question", "")).strip(),
                "options": clean_options,
                "correct_index": correct_index,
                "explanation": str(question.get("explanation", "")).strip(),
            }
        )

    if not clean_summary:
        clean_summary = ["Conversation quiz"]
    if len(clean_questions) < 5:
        raise ValueError("Quiz generation did not produce valid MCQ questions.")

    return {"summary": clean_summary, "questions": clean_questions}


def save_flashcards(data: dict[str, Any], path: Path = FLASHCARDS_PATH) -> Path:
    """Persist flashcards only after the user explicitly requests them."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path
