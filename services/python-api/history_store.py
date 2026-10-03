import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

DB_PATH = os.getenv("HISTORY_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "history.db"))

_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    channel_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    user_id TEXT,
                    user_name TEXT,
                    channel_name TEXT,
                    channel_type TEXT,
                    text TEXT,
                    thread_ts TEXT,
                    created_at TEXT,
                    PRIMARY KEY (channel_id, ts)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)"
            )
            conn.commit()
        finally:
            conn.close()


def upsert_message(msg: dict[str, Any]) -> None:
    if not msg.get("channel_id") or not msg.get("ts"):
        return
    created_at = msg.get("created_at") or slack_ts_to_iso(msg.get("ts", ""))
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO messages (
                    channel_id, ts, user_id, user_name, channel_name,
                    channel_type, text, thread_ts, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(channel_id, ts) DO UPDATE SET
                    user_id=excluded.user_id,
                    user_name=excluded.user_name,
                    channel_name=excluded.channel_name,
                    channel_type=excluded.channel_type,
                    text=excluded.text,
                    thread_ts=excluded.thread_ts,
                    created_at=excluded.created_at
                """,
                (
                    msg.get("channel_id"),
                    msg.get("ts"),
                    msg.get("user_id"),
                    msg.get("user_name"),
                    msg.get("channel_name"),
                    msg.get("channel_type"),
                    msg.get("text") or "",
                    msg.get("thread_ts"),
                    created_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def slack_ts_to_iso(ts: str) -> str:
    try:
        seconds = float(ts)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).isoformat()


def search_messages(
    question: str,
    user_id: str | None = None,
    channel_id: str | None = None,
    limit: int = 80,
    days: int = 21,
) -> list[dict[str, Any]]:
    tokens = [t.lower() for t in question.replace("?", " ").split() if len(t) > 2]
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()

    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT 800
                """,
                (cutoff_iso,),
            ).fetchall()
        finally:
            conn.close()

    scored: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        item = dict(row)
        text = (item.get("text") or "").lower()
        score = 1
        if user_id and (
            item.get("user_id") == user_id or (user_id in (item.get("text") or ""))
        ):
            score += 8
        if channel_id and item.get("channel_id") == channel_id:
            score += 2
        for token in tokens:
            if token in text:
                score += 3
            if token in (item.get("channel_name") or "").lower():
                score += 1
            if token in (item.get("user_name") or "").lower():
                score += 1
        scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1].get("created_at") or ""))
    selected = [item for score, item in scored if score > 1 or user_id]
    return selected[:limit]


def count_messages() -> int:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM messages").fetchone()
            return int(row["n"] if row else 0)
        finally:
            conn.close()
