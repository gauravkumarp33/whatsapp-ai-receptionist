"""
image_service.py
----------------
Returns image URLs for a requested room or facility based on keyword matching
against the mappings defined in data/images.json.

Rules
-----
* No Gemini / ML calls.
* data/images.json is read-only; never modified.
* No databases — the JSON file is the single source of truth.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path to the image catalogue
# ---------------------------------------------------------------------------

_IMAGES_JSON = Path(__file__).parent.parent / "data" / "images.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_catalogue() -> dict[str, list[str]]:
    """Load and return the image catalogue from *images.json*.

    The file is read on every call so that live edits to images.json are
    picked up without restarting the server.
    """
    try:
        with open(_IMAGES_JSON, encoding="utf-8") as fh:
            catalogue = json.load(fh)
        logger.debug("Loaded %d categories from %s", len(catalogue), _IMAGES_JSON)
        return catalogue
    except FileNotFoundError:
        logger.error("images.json not found at %s", _IMAGES_JSON)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse images.json: %s", exc)
        return {}


def _normalize(text: str) -> str:
    """Lower-case and collapse whitespace in *text*."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)   # strip punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _variants(token: str) -> list[str]:
    """Return *token* plus simple singular/plural variants.

    e.g. "lithopanes" -> ["lithopanes", "lithopane"]
         "photo"      -> ["photo", "photos"]
    """
    forms = [token]
    if token.endswith("s") and len(token) > 3:
        forms.append(token[:-1])          # strip trailing 's'
    else:
        forms.append(token + "s")         # add trailing 's'
    return forms


def _key_matches(normalized_message: str, category_key: str) -> bool:
    """Return True if *category_key* (or any of its individual words, including
    simple singular/plural variants) appears in *normalized_message* as a whole
    word/phrase.

    Matching strategy (in order):
    1. Full category key phrase — e.g. "custom models"
    2. Each individual word in the key (>2 chars) plus its plural/singular
       variant — e.g. "lithopanes" also matches message token "lithopane"
    """
    # 1. Full phrase match
    pattern = r"(?<!\w)" + re.escape(_normalize(category_key)) + r"(?!\w)"
    if re.search(pattern, normalized_message):
        logger.debug("Full-phrase match on key %r", category_key)
        return True

    # 2. Individual token match (skip very short stop-words)
    for token in _normalize(category_key).split():
        if len(token) > 2:
            for form in _variants(token):
                pattern = r"(?<!\w)" + re.escape(form) + r"(?!\w)"
                if re.search(pattern, normalized_message):
                    logger.debug("Token match: %r (form %r) matched key %r", token, form, category_key)
                    return True

    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_images(user_message: str) -> list[str]:
    """Return a list of image URLs matching the room / facility mentioned in
    *user_message*.

    The function performs keyword matching against the keys of ``data/images.json``.
    The first matching category wins.  An empty list is returned when no
    category matches.

    Parameters
    ----------
    user_message:
        Raw text message from the WhatsApp user.

    Returns
    -------
    list[str]
        Matching image URLs, or ``[]`` if no category matched.

    Examples
    --------
    >>> get_images("Show me custom model photos")
    ['https://...', 'https://...', ...]
    >>> get_images("Do you have lithopane pictures?")
    ['https://...']
    >>> get_images("What are your prices?")
    []
    """
    if not user_message or not user_message.strip():
        return []

    catalogue = _load_catalogue()
    if not catalogue:
        return []

    normalized_msg = _normalize(user_message)
    logger.debug("Normalized user message: %r", normalized_msg)

    for category, urls in catalogue.items():
        if _key_matches(normalized_msg, category):
            logger.info("Matched category: %r (%d image(s))", category, len(urls))
            return list(urls)   # return a copy; never expose the internal list

    logger.info("No image category matched for message: %r", user_message)
    return []
