"""
services/memory_service.py

In-memory conversation store for the WhatsApp AI Receptionist.
Each customer is keyed by their WhatsApp phone number.

Stores per customer:
  - conversation_history : list[dict]  – rolling window of the last 26 messages
  - mode                 : ConversationMode – current handling mode

NOTE: All data is lost on server restart (no persistence layer).
"""

from enum import Enum
from typing import TypedDict


# ---------------------------------------------------------------------------
# Conversation mode
# ---------------------------------------------------------------------------
class ConversationMode(str, Enum):
    ACTIVE_BOT    = "ACTIVE_BOT"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"


# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------
MAX_HISTORY = 26  # Maximum number of messages retained per customer


class _CustomerState(TypedDict):
    history: list[dict]
    mode: ConversationMode


# ---------------------------------------------------------------------------
# In-memory store  {phone_number: _CustomerState}
# ---------------------------------------------------------------------------
_store: dict[str, _CustomerState] = {}


def _get_or_create(phone_number: str) -> _CustomerState:
    """Return existing state for *phone_number*, creating it if absent."""
    if phone_number not in _store:
        _store[phone_number] = {
            "history": [],
            "mode": ConversationMode.ACTIVE_BOT,
        }
    return _store[phone_number]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_history(phone_number: str) -> list[dict]:
    """
    Return the conversation history for *phone_number*.

    Each item is a dict: {"role": "user"|"model", "parts": "<text>"}.
    Returns an empty list if the customer has no recorded history.
    """
    return _get_or_create(phone_number)["history"]


def add_message(phone_number: str, role: str, content: str) -> None:
    """
    Append a message to the conversation history for *phone_number*.

    Args:
        phone_number: The customer's WhatsApp phone number.
        role:         "user" or "model".
        content:      The text content of the message.

    Enforces a rolling window: if the history exceeds MAX_HISTORY messages
    the oldest message is discarded.
    """
    state = _get_or_create(phone_number)
    state["history"].append({"role": role, "parts": content})

    # Trim to the most recent MAX_HISTORY messages
    if len(state["history"]) > MAX_HISTORY:
        state["history"] = state["history"][-MAX_HISTORY:]


def clear_history(phone_number: str) -> None:
    """
    Erase all conversation history for *phone_number*.
    The customer's mode is preserved.
    """
    _get_or_create(phone_number)["history"] = []


def get_mode(phone_number: str) -> ConversationMode:
    """
    Return the current ConversationMode for *phone_number*.
    Defaults to ConversationMode.ACTIVE_BOT for new customers.
    """
    return _get_or_create(phone_number)["mode"]


def set_mode(phone_number: str, mode: ConversationMode) -> None:
    """
    Set the ConversationMode for *phone_number*.

    Args:
        phone_number: The customer's WhatsApp phone number.
        mode:         The new ConversationMode to assign.
    """
    _get_or_create(phone_number)["mode"] = mode
