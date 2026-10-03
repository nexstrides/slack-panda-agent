import logging
import os
from datetime import datetime, timezone

import anthropic

from history_store import search_messages

logger = logging.getLogger(__name__)

claude_api_key = os.getenv("CLAUDE_API_KEY")
claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
client = anthropic.Anthropic(api_key=claude_api_key) if claude_api_key else None

SYSTEM_PROMPT = """You are PandaAgent, a helpful Slack teammate.

Answer the user's question using ONLY the provided Slack chat history.
When it helps, mention who said what, which channel, and when.
If they ask what they should do this week, infer tasks, deadlines, follow-ups, and requests directed at them.
If the history does not contain enough information, say so and suggest inviting the bot to more channels.
Reply in a concise Slack-friendly style. Do not invent messages that are not in the history.
"""


def format_history(messages: list[dict]) -> str:
    if not messages:
        return "(no matching chat history)"
    lines = []
    for msg in sorted(messages, key=lambda item: item.get("created_at") or ""):
        when = msg.get("created_at") or ""
        try:
            when = datetime.fromisoformat(when).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            pass
        channel = msg.get("channel_name") or msg.get("channel_id")
        author = msg.get("user_name") or msg.get("user_id")
        text = (msg.get("text") or "").replace("\n", " ")
        lines.append(f"[{when}] #{channel} {author}: {text}")
    return "\n".join(lines)


def answer_question(
    question: str,
    user_id: str | None,
    user_name: str | None,
    channel_id: str | None = None,
) -> str:
    history = search_messages(question, user_id=user_id, channel_id=channel_id)
    context = format_history(history)
    asker = user_name or user_id or "someone"

    if not client:
        if not history:
            return (
                "I do not have enough Slack history yet, and Claude is not configured. "
                "Invite me to the channels you care about, add history scopes, and set CLAUDE_API_KEY."
            )
        preview = context.split("\n")[:12]
        return (
            "Claude is not configured, so here is the recent history I would use:\n"
            + "\n".join(preview)
        )

    prompt = (
        f"Asker: {asker} (Slack user id {user_id})\n"
        f"Question: {question}\n\n"
        f"Chat history:\n{context}"
    )
    try:
        message = client.messages.create(
            model=claude_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in message.content if getattr(block, "type", "") == "text"]
        return "\n".join(parts).strip() or "I could not generate an answer from the current history."
    except Exception as exc:
        logger.error("Claude answer failed: %s", exc)
        return f"I found history, but answering failed: {exc}"
