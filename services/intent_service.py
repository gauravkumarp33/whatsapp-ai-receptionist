"""
intent_service.py
-----------------
Lightweight rule-based intent detector.

Supported intents:
    - IMAGE_REQUEST   : User wants to see photos / images of a room or facility.
    - BOOKING_REQUEST : User wants to make a reservation / booking.
    - TEXT_QUERY      : Catch-all for everything else.

Detection strategy: simple keyword matching on a normalised (lower-cased,
punctuation-stripped) copy of the incoming message.  No ML, no external APIs.
"""

from __future__ import annotations

import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Intent enum
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    IMAGE_REQUEST   = "IMAGE_REQUEST"
    BOOKING_REQUEST = "BOOKING_REQUEST"
    TEXT_QUERY      = "TEXT_QUERY"


# ---------------------------------------------------------------------------
# Keyword lists  (order matters: more-specific checks run first)
# ---------------------------------------------------------------------------

# Triggers for IMAGE_REQUEST
_IMAGE_KEYWORDS: list[str] = [
    "photo",
    "photos",
    "picture",
    "pictures",
    "image",
    "images",
    "pic",
    "pics",
    "show me",
    "look like",
    "snapshot",
    "gallery",
    "view",
]

# Triggers for BOOKING_REQUEST
_BOOKING_KEYWORDS: list[str] = [
    "book",
    "booking",
    "reserve",
    "reservation",
    "i want to book",
    "i'd like to book",
    "make a booking",
    "make a reservation",
    "availability",
    "available",
    "schedule",
    "appointment",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lower-case and strip punctuation from *text* for reliable matching."""
    text = text.lower()
    # Replace punctuation (except hyphens, kept for "check-in") with spaces
    text = re.sub(r"[^\w\s\-]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _contains_any(normalized_text: str, keywords: list[str]) -> bool:
    """Return True if *normalized_text* contains any keyword as a substring."""
    for kw in keywords:
        # Match the keyword surrounded by word-boundaries or string edges so
        # that "booking" does not falsely match inside unrelated words.
        pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
        if re.search(pattern, normalized_text):
            logger.debug("Keyword matched: %r", kw)
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_intent(message: str) -> Intent:
    """
    Detect the intent of an incoming WhatsApp *message*.

    Detection priority (first match wins):
        1. IMAGE_REQUEST
        2. BOOKING_REQUEST
        3. TEXT_QUERY  (default)

    Parameters
    ----------
    message:
        Raw message text received from the user.

    Returns
    -------
    Intent
        One of ``Intent.IMAGE_REQUEST``, ``Intent.BOOKING_REQUEST``, or
        ``Intent.TEXT_QUERY``.

    Examples
    --------
    >>> detect_intent("Show deluxe room photos")
    <Intent.IMAGE_REQUEST: 'IMAGE_REQUEST'>
    >>> detect_intent("I want to book a room")
    <Intent.BOOKING_REQUEST: 'BOOKING_REQUEST'>
    >>> detect_intent("What is the check-out time?")
    <Intent.TEXT_QUERY: 'TEXT_QUERY'>
    """
    if not message or not message.strip():
        logger.debug("Empty message received; defaulting to TEXT_QUERY")
        return Intent.TEXT_QUERY

    normalized = _normalize(message)
    logger.debug("Normalised message: %r", normalized)

    # 1. IMAGE_REQUEST takes highest priority
    if _contains_any(normalized, _IMAGE_KEYWORDS):
        logger.info("Intent detected: IMAGE_REQUEST")
        return Intent.IMAGE_REQUEST

    # 2. BOOKING_REQUEST
    if _contains_any(normalized, _BOOKING_KEYWORDS):
        logger.info("Intent detected: BOOKING_REQUEST")
        return Intent.BOOKING_REQUEST

    # 3. Default
    logger.info("Intent detected: TEXT_QUERY (default)")
    return Intent.TEXT_QUERY
