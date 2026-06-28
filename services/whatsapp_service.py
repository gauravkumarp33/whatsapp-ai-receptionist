"""
whatsapp_service.py
-------------------
Thin wrapper around the Meta WhatsApp Cloud API.

Responsibilities
----------------
* send_text_message(phone_number, message)  – send a plain-text reply
* send_image_message(phone_number, image_url) – send an image by URL

This module is intentionally limited to *sending* messages only.
Webhook parsing, chatbot logic, and routing live elsewhere.

Credentials are read from config.settings:
    WHATSAPP_ACCESS_TOKEN    – Bearer token issued by Meta
    WHATSAPP_PHONE_NUMBER_ID – Phone Number ID from the Meta Developer dashboard
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API constants
# ---------------------------------------------------------------------------

_API_VERSION = "v19.0"
_BASE_URL = f"https://graph.facebook.com/{_API_VERSION}"
_REQUEST_TIMEOUT = 10   # seconds


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _endpoint() -> str:
    """Return the fully-qualified messages endpoint for the configured phone number."""
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    if not phone_number_id:
        raise ValueError(
            "WHATSAPP_PHONE_NUMBER_ID is not set. "
            "Check your .env file or environment variables."
        )
    return f"{_BASE_URL}/{phone_number_id}/messages"


def _headers() -> dict[str, str]:
    """Return the HTTP headers required by the Cloud API."""
    token = settings.WHATSAPP_ACCESS_TOKEN
    if not token:
        raise ValueError(
            "WHATSAPP_ACCESS_TOKEN is not set. "
            "Check your .env file or environment variables."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _post(payload: dict[str, Any]) -> dict[str, Any]:
    """
    POST *payload* to the WhatsApp Cloud API messages endpoint.

    Returns the parsed JSON response on success.

    Raises
    ------
    requests.HTTPError
        When the API returns a 4xx / 5xx status code.
    requests.ConnectionError
        When the network is unreachable.
    requests.Timeout
        When the request exceeds *_REQUEST_TIMEOUT* seconds.
    ValueError
        When credentials are missing.
    """
    url = _endpoint()
    headers = _headers()

    logger.debug("POST %s | payload: %s", url, payload)

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=_REQUEST_TIMEOUT,
        )
    except requests.Timeout:
        logger.error("WhatsApp API request timed out after %ss", _REQUEST_TIMEOUT)
        raise
    except requests.ConnectionError as exc:
        logger.error("Network failure while calling WhatsApp API: %s", exc)
        raise

    # Surface API-level errors (4xx / 5xx) as exceptions with a clear log
    if not response.ok:
        logger.error(
            "WhatsApp API error %s: %s",
            response.status_code,
            response.text,
        )
        response.raise_for_status()

    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        logger.error("Invalid JSON in WhatsApp API response: %s", response.text)
        raise ValueError(
            f"WhatsApp API returned non-JSON response: {response.text}"
        ) from exc

    logger.debug("WhatsApp API response: %s", data)
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_text_message(phone_number: str, message: str) -> dict[str, Any]:
    """
    Send a plain-text WhatsApp message to *phone_number*.

    Parameters
    ----------
    phone_number:
        Recipient's phone number in E.164 format (e.g. ``"15551234567"``).
    message:
        The text body to send (max 4 096 characters per Meta's limits).

    Returns
    -------
    dict
        The parsed API response from Meta (contains ``messages[].id`` on
        success).

    Raises
    ------
    ValueError
        Missing credentials or empty arguments.
    requests.HTTPError
        API returned 4xx / 5xx.
    requests.ConnectionError
        Network unreachable.
    requests.Timeout
        Request timed out.

    Examples
    --------
    >>> send_text_message("15551234567", "Hello! How can I help you today?")
    {'messaging_product': 'whatsapp', 'messages': [{'id': 'wamid.xxx'}]}
    """
    if not phone_number or not phone_number.strip():
        raise ValueError("phone_number must not be empty.")
    if not message or not message.strip():
        raise ValueError("message must not be empty.")

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number.strip(),
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message,
        },
    }

    logger.info("Sending text message to %s", phone_number)
    result = _post(payload)
    logger.info("Text message sent to %s | response: %s", phone_number, result)
    return result


def send_image_message(phone_number: str, image_url: str) -> dict[str, Any]:
    """
    Send an image (by URL) as a WhatsApp message to *phone_number*.

    The image must be publicly accessible; Meta fetches it directly from
    *image_url*.  Supported formats: JPEG, PNG, WEBP, GIF (static).

    Parameters
    ----------
    phone_number:
        Recipient's phone number in E.164 format.
    image_url:
        Publicly reachable URL of the image to send.

    Returns
    -------
    dict
        The parsed API response from Meta.

    Raises
    ------
    ValueError
        Missing credentials or empty arguments.
    requests.HTTPError
        API returned 4xx / 5xx.
    requests.ConnectionError
        Network unreachable.
    requests.Timeout
        Request timed out.

    Examples
    --------
    >>> send_image_message("15551234567", "https://example.com/room.jpg")
    {'messaging_product': 'whatsapp', 'messages': [{'id': 'wamid.xxx'}]}
    """
    if not phone_number or not phone_number.strip():
        raise ValueError("phone_number must not be empty.")
    if not image_url or not image_url.strip():
        raise ValueError("image_url must not be empty.")

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number.strip(),
        "type": "image",
        "image": {
            "link": image_url.strip(),
        },
    }

    logger.info("Sending image message to %s | url: %s", phone_number, image_url)
    result = _post(payload)
    logger.info("Image message sent to %s | response: %s", phone_number, result)
    return result
