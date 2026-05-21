from studdybuddy.crew import Studdybuddy
from studdybuddy.search import format_search_context, serper_search, should_use_search


DIRECT_ANSWER_PROMPT = """Answer the user's input directly.

Teach in this personality:
{personality_instruction}

Use this recent chat context to keep the answer consistent with the learner's
previous questions and your previous answers. If the new question refers to
"this", "that", "it", "same topic", "previous answer", or a related suggestion,
resolve it from the context. Do not repeat the whole context unless needed.

Recent chat context:
{conversation_context}

Live search context:
{search_context}

If live search context is present, use it for current facts and say "Live search:
used" near the end. If no live search context is present, do not mention live
search.

Start with the answer. If the question needs steps, include the shortest clear
step-by-step explanation. If the user made a mistake or misconception, explain
it briefly after the answer.

Then add:
- Suggestions: 2-3 concise, actionable things the user should review or try next.
- Exemplar questions: 2-3 similar questions that target the same doubt, with brief
  answer hints or final answers.

Keep the response focused on the user's exact doubt. Do not add unrelated
practice problems.

User input:
{query}
"""

PERSONALITY_INSTRUCTIONS = {
    "Teacher": (
        "Teacher - be clear, structured, patient, and slightly formal. Define key "
        "terms before using them and organize the explanation like a classroom note."
    ),
    "Friend": (
        "Friend - be warm, casual, encouraging, and simple. Use everyday language, "
        "short examples, and keep the learner comfortable."
    ),
}


def normalize_personality(personality: str | None) -> str:
    """Return a supported teaching personality."""
    if not personality:
        return "Teacher"
    cleaned = personality.strip()
    return cleaned if cleaned in PERSONALITY_INSTRUCTIONS else "Teacher"


def format_chat_context(messages: list[dict[str, str]] | None, limit: int = 8) -> str:
    """Format recent chat messages for the answer prompt."""
    if not messages:
        return "No previous messages yet."

    lines = []
    for message in messages[-limit:]:
        role = "Student" if message.get("role") == "user" else "StudyBuddy"
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n\n".join(lines) if lines else "No previous messages yet."


def get_live_search_results(query: str) -> list[dict[str, str]]:
    """Return live search results when available, without blocking normal chat."""
    if not should_use_search(query):
        return []
    try:
        return serper_search(query)
    except Exception:
        return []


def answer_user(
    query: str,
    personality: str | None = None,
    messages: list[dict[str, str]] | None = None,
) -> str:
    """Return a direct answer to the user's typed input."""
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Please enter a question.")

    selected_personality = normalize_personality(personality)
    conversation_context = format_chat_context(messages)
    search_results = get_live_search_results(cleaned_query)
    search_context = format_search_context(search_results)
    result = Studdybuddy().learning_guide().kickoff(
        DIRECT_ANSWER_PROMPT.format(
            personality_instruction=PERSONALITY_INSTRUCTIONS[selected_personality],
            conversation_context=conversation_context,
            search_context=search_context,
            query=cleaned_query,
        )
    )
    return result.raw.strip()


def answer_user_with_search_status(
    query: str,
    personality: str | None = None,
    messages: list[dict[str, str]] | None = None,
) -> tuple[str, bool]:
    """Return an answer plus whether live search snippets were supplied."""
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Please enter a question.")

    selected_personality = normalize_personality(personality)
    conversation_context = format_chat_context(messages)
    search_results = get_live_search_results(cleaned_query)
    search_context = format_search_context(search_results)
    result = Studdybuddy().learning_guide().kickoff(
        DIRECT_ANSWER_PROMPT.format(
            personality_instruction=PERSONALITY_INSTRUCTIONS[selected_personality],
            conversation_context=conversation_context,
            search_context=search_context,
            query=cleaned_query,
        )
    )
    return result.raw.strip(), bool(search_results)
