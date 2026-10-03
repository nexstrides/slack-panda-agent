import logging
import os
import time
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from history_store import slack_ts_to_iso, upsert_message

logger = logging.getLogger(__name__)

HISTORY_DAYS = int(os.getenv("HISTORY_DAYS", "21"))
MESSAGES_PER_CHANNEL = int(os.getenv("HISTORY_MESSAGES_PER_CHANNEL", "200"))


class SlackDirectory:
    def __init__(self, token: str | None):
        self.client = WebClient(token=token) if token else None
        self._users: dict[str, str] = {}
        self._channels: dict[str, dict[str, str]] = {}

    def user_name(self, user_id: str | None) -> str:
        if not user_id or not self.client:
            return user_id or "unknown"
        if user_id in self._users:
            return self._users[user_id]
        try:
            info = self.client.users_info(user=user_id)
            profile = info.get("user") or {}
            name = (
                (profile.get("profile") or {}).get("display_name")
                or profile.get("real_name")
                or profile.get("name")
                or user_id
            )
            self._users[user_id] = name
            return name
        except SlackApiError as exc:
            logger.warning("users.info failed for %s: %s", user_id, exc.response.get("error"))
            return user_id

    def channel_meta(self, channel_id: str | None) -> dict[str, str]:
        if not channel_id:
            return {"name": "unknown", "type": "unknown"}
        if channel_id in self._channels:
            return self._channels[channel_id]
        meta = {"name": channel_id, "type": _guess_channel_type(channel_id)}
        if self.client:
            try:
                info = self.client.conversations_info(channel=channel_id)
                ch = info.get("channel") or {}
                if ch.get("is_im"):
                    other = ch.get("user")
                    meta = {
                        "name": f"dm:{self.user_name(other)}",
                        "type": "im",
                    }
                else:
                    meta = {
                        "name": ch.get("name") or channel_id,
                        "type": "channel" if ch.get("is_channel") else "group" if ch.get("is_group") else "mpim" if ch.get("is_mpim") else _guess_channel_type(channel_id),
                    }
            except SlackApiError as exc:
                logger.warning(
                    "conversations.info failed for %s: %s",
                    channel_id,
                    exc.response.get("error"),
                )
        self._channels[channel_id] = meta
        return meta


def _guess_channel_type(channel_id: str) -> str:
    if channel_id.startswith("D"):
        return "im"
    if channel_id.startswith("G"):
        return "group"
    return "channel"


def record_event(directory: SlackDirectory, payload: dict[str, Any]) -> None:
    channel_id = payload.get("channel_id") or payload.get("channel")
    user_id = payload.get("user_id") or payload.get("user")
    meta = directory.channel_meta(channel_id)
    upsert_message(
        {
            "channel_id": channel_id,
            "ts": payload.get("ts"),
            "user_id": user_id,
            "user_name": payload.get("user_name") or directory.user_name(user_id),
            "channel_name": payload.get("channel_name") or meta.get("name"),
            "channel_type": payload.get("channel_type") or meta.get("type"),
            "text": payload.get("text") or "",
            "thread_ts": payload.get("thread_ts"),
            "created_at": slack_ts_to_iso(payload.get("ts") or ""),
        }
    )


def backfill(directory: SlackDirectory) -> int:
    if not directory.client:
        logger.warning("Skipping Slack backfill; SLACK_BOT_TOKEN is not set")
        return 0

    oldest = str(time.time() - HISTORY_DAYS * 86400)
    stored = 0
    cursor = None
    while True:
        try:
            result = directory.client.conversations_list(
                types="public_channel,private_channel,mpim,im",
                exclude_archived=True,
                limit=200,
                cursor=cursor,
            )
        except SlackApiError as exc:
            logger.error("conversations.list failed: %s", exc.response.get("error"))
            break

        for channel in result.get("channels") or []:
            stored += _backfill_channel(directory, channel, oldest)

        cursor = (result.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.5)

    logger.info("Backfilled %s Slack messages", stored)
    return stored


def _backfill_channel(directory: SlackDirectory, channel: dict[str, Any], oldest: str) -> int:
    channel_id = channel.get("id")
    if not channel_id:
        return 0
    meta = directory.channel_meta(channel_id)
    stored = 0
    cursor = None
    fetched = 0
    while fetched < MESSAGES_PER_CHANNEL:
        try:
            result = directory.client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                limit=min(200, MESSAGES_PER_CHANNEL - fetched),
                cursor=cursor,
            )
        except SlackApiError as exc:
            error = exc.response.get("error")
            if error not in {"not_in_channel", "channel_not_found", "missing_scope"}:
                logger.warning("history failed for %s: %s", channel_id, error)
            return stored

        messages = result.get("messages") or []
        if not messages:
            break
        for message in messages:
            if message.get("subtype") in {"bot_message", "message_changed", "message_deleted"}:
                continue
            if message.get("bot_id") and not message.get("user"):
                continue
            user_id = message.get("user")
            record_event(
                directory,
                {
                    "channel_id": channel_id,
                    "channel_name": meta.get("name"),
                    "channel_type": meta.get("type"),
                    "ts": message.get("ts"),
                    "user_id": user_id,
                    "text": message.get("text") or "",
                    "thread_ts": message.get("thread_ts"),
                },
            )
            stored += 1
            fetched += 1
        cursor = (result.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.3)
    return stored
