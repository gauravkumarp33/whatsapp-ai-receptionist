"""
services/booking_service.py
----------------------------
State-based booking *inquiry* flow for the WhatsApp AI Receptionist.

Each customer (keyed by WhatsApp phone number) gets an independent session.
All sessions are kept in memory; data is lost on server restart.

Fields collected (in order)
----------------------------
1. Customer Name
2. Item required
3. Item required by (Date)

Public API
----------
start_booking(phone_number)          -> str   – begins the flow, returns first prompt
process_booking_message(phone, msg)  -> str   – advances the flow, returns next prompt
                                                or confirmation when complete
is_booking_active(phone_number)      -> bool  – True while a session is in progress
cancel_booking(phone_number)         -> None  – discards the active session

Rules
-----
* One field collected at a time.
* Empty / whitespace-only answers are rejected (user is re-prompted).
* No reservations are created.
* No availability is checked.
* No external services or databases are used.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Booking step definitions
# ---------------------------------------------------------------------------

class _Step(Enum):
    NAME     = auto()   # Step 1 – customer name
    ITEM     = auto()   # Step 2 – item required
    DATE     = auto()   # Step 3 – item required by (date)
    COMPLETE = auto()   # Terminal state


# Ordered sequence of steps (excluding COMPLETE)
_STEPS_ORDER: list[_Step] = [_Step.NAME, _Step.ITEM, _Step.DATE]

# Human-readable prompts shown to the customer at each step
_PROMPTS: dict[_Step, str] = {
    _Step.NAME: "Sure! Let's get your inquiry started.\n\nFirst, could I have your *full name*?",
    _Step.ITEM: "Thank you! What *item* would you like to inquire about?",
    _Step.DATE: "Got it! By what *date* do you need this item? (e.g. 15 July 2025)",
}

# Field labels used in the booking summary
_LABELS: dict[_Step, str] = {
    _Step.NAME: "Customer Name",
    _Step.ITEM: "Item Required",
    _Step.DATE: "Required By",
}


# ---------------------------------------------------------------------------
# Session dataclass
# ---------------------------------------------------------------------------

@dataclass
class _BookingSession:
    """Holds the state for one in-progress booking inquiry."""
    current_step: _Step = _Step.NAME
    collected:    dict[_Step, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# In-memory store   {phone_number: _BookingSession}
# ---------------------------------------------------------------------------

_sessions: dict[str, _BookingSession] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _next_step(current: _Step) -> _Step:
    """Return the step that follows *current*, or _Step.COMPLETE."""
    idx = _STEPS_ORDER.index(current)
    next_idx = idx + 1
    return _STEPS_ORDER[next_idx] if next_idx < len(_STEPS_ORDER) else _Step.COMPLETE


def _build_summary(session: _BookingSession) -> str:
    """Format a human-readable summary of the completed booking fields."""
    lines = ["📋 *Booking Inquiry Summary*\n"]
    for step in _STEPS_ORDER:
        label = _LABELS[step]
        value = session.collected.get(step, "—")
        lines.append(f"• *{label}:* {value}")
    return "\n".join(lines)


def _confirmation_message(session: _BookingSession) -> str:
    """Return the full confirmation reply sent when all fields are collected."""
    summary = _build_summary(session)
    return (
        f"{summary}\n\n"
        "✅ Your inquiry has been sent to the property. "
        "A team member will get back to you as soon as possible. "
        "Thank you! 🙏"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_booking_active(phone_number: str) -> bool:
    """Return True if *phone_number* has an active booking session in progress."""
    return phone_number in _sessions


def start_booking(phone_number: str) -> str:
    """
    Begin a new booking inquiry session for *phone_number*.

    If a session already exists for this customer it is reset and a fresh
    session is started.

    Returns
    -------
    str
        The first prompt to send to the customer.
    """
    _sessions[phone_number] = _BookingSession()
    logger.info("Booking session started for %s", phone_number)
    return _PROMPTS[_Step.NAME]


def process_booking_message(phone_number: str, message: str) -> str:
    """
    Advance the booking flow for *phone_number* with the customer's *message*.

    Behaviour
    ---------
    * Empty / whitespace-only messages are rejected; the current prompt is
      repeated with a gentle reminder.
    * Valid answers are stored and the next field's prompt is returned.
    * When all fields are collected the session is removed from memory and a
      confirmation message is returned.

    Parameters
    ----------
    phone_number:
        The customer's WhatsApp phone number.
    message:
        The customer's raw reply text.

    Returns
    -------
    str
        The next prompt, a validation error message, or the final confirmation.

    Raises
    ------
    KeyError
        If called for a *phone_number* that has no active session.  Callers
        should check ``is_booking_active`` first.
    """
    if phone_number not in _sessions:
        raise KeyError(
            f"No active booking session for {phone_number!r}. "
            "Call start_booking() first."
        )

    session = _sessions[phone_number]
    answer  = message.strip() if message else ""

    # Reject empty answers
    if not answer:
        logger.debug(
            "Empty answer from %s at step %s; re-prompting.",
            phone_number, session.current_step.name,
        )
        return (
            "I didn't catch that. 😊 Please provide a valid answer.\n\n"
            + _PROMPTS[session.current_step]
        )

    # Store the valid answer
    session.collected[session.current_step] = answer
    logger.info(
        "Booking [%s] step %s collected: %r",
        phone_number, session.current_step.name, answer,
    )

    # Advance to the next step
    session.current_step = _next_step(session.current_step)

    if session.current_step is _Step.COMPLETE:
        # All fields collected – build confirmation and clean up
        confirmation = _confirmation_message(session)
        del _sessions[phone_number]
        logger.info("Booking inquiry complete and session closed for %s", phone_number)
        return confirmation

    # More fields to collect
    return _PROMPTS[session.current_step]


def cancel_booking(phone_number: str) -> None:
    """
    Discard the active booking session for *phone_number*.

    Safe to call even if no session exists (no-op in that case).
    """
    if phone_number in _sessions:
        del _sessions[phone_number]
        logger.info("Booking session cancelled for %s", phone_number)
    else:
        logger.debug("cancel_booking called but no session found for %s", phone_number)
