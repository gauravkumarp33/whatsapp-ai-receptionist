"""
WhatsApp AI Receptionist - Main Application Entry Point
"""

import logging
from fastapi import FastAPI, Request, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, JSONResponse

from config import settings
from services.gemini_service import generate_response
from services.memory_service import get_mode, ConversationMode, get_history, add_message
from services.booking_service import is_booking_active, process_booking_message, start_booking
from services.intent_service import detect_intent, Intent
from services.image_service import get_images
from services.whatsapp_service import send_text_message, send_image_message

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="WhatsApp AI Receptionist",
    description="An AI-powered receptionist that handles WhatsApp messages via the Meta Cloud API.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns service health status."""
    return {"status": "ok", "service": "whatsapp-ai-receptionist"}


# ---------------------------------------------------------------------------
# Internal message orchestration helper
# ---------------------------------------------------------------------------
def process_message_logic(sender: str, text: str) -> dict:
    mode = get_mode(sender)
    if mode == ConversationMode.HUMAN_HANDOFF:
        logger.info("Customer %s is in HUMAN_HANDOFF mode. Ignoring.", sender)
        return {"type": "handoff", "response": "Conversation is currently under human control."}
        
    if is_booking_active(sender):
        logger.info("Customer %s has an active booking session.", sender)
        response_text = process_booking_message(sender, text)
        return {"type": "booking", "response": response_text}
        
    intent = detect_intent(text)
    
    if intent == Intent.IMAGE_REQUEST:
        image_urls = get_images(text)
        return {"type": "image", "images": image_urls}
            
    elif intent == Intent.BOOKING_REQUEST:
        response_text = start_booking(sender)
        return {"type": "booking", "response": response_text}
        
    elif intent == Intent.TEXT_QUERY:
        history = get_history(sender)
        response_text = generate_response(text, history)
        
        # Store history on success
        add_message(sender, "user", text)
        add_message(sender, "model", response_text)
        return {"type": "text", "response": response_text}

    return {"type": "text", "response": ""}


# ---------------------------------------------------------------------------
# DEV ONLY – Test chatbot orchestration directly
# ---------------------------------------------------------------------------
class TestChatRequest(BaseModel):
    phone_number: str
    message: str


# Development testing endpoint. Remove or disable before production deployment.
@app.post("/test-gemini", tags=["Dev"])
async def test_gemini(payload: TestChatRequest):
    """
    Development-only endpoint to test the full chatbot orchestration logic
    without hitting the WhatsApp API.
    """
    try:
        result = process_message_logic(payload.phone_number, payload.message)
        return JSONResponse(content=result, status_code=200)
    except Exception as exc:
        logger.exception("Error in orchestration logic: %s", exc)
        raise HTTPException(status_code=500, detail="Orchestration error. See server logs for details.")


# ---------------------------------------------------------------------------
# WhatsApp Webhook – GET (verification handshake)
# ---------------------------------------------------------------------------
@app.get("/webhook", tags=["Webhook"])
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Meta webhook verification endpoint.
    Meta sends a GET request with hub.mode, hub.challenge, and hub.verify_token.
    We must echo back hub.challenge when the token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return PlainTextResponse(content=hub_challenge, status_code=200)

    logger.warning("Webhook verification failed – token mismatch or wrong mode.")
    raise HTTPException(status_code=403, detail="Verification token mismatch.")


# ---------------------------------------------------------------------------
# WhatsApp Webhook – POST (incoming messages)
# ---------------------------------------------------------------------------
@app.post("/webhook", tags=["Webhook"])
async def receive_message(request: Request):
    """
    Receives incoming WhatsApp messages from Meta's Cloud API.
    Parses the payload and delegates to the message handler service.
    """
    try:
        body = await request.json()
        logger.info("Incoming webhook payload: %s", body)

        # Validate it is a WhatsApp business account event
        if body.get("object") != "whatsapp_business_account":
            return JSONResponse(content={"status": "ignored"}, status_code=200)

        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for message in messages:
                    await handle_incoming_message(message, value)

        return JSONResponse(content={"status": "received"}, status_code=200)

    except Exception as exc:
        logger.exception("Error processing webhook: %s", exc)
        # Always return 200 to Meta to prevent retries
        return JSONResponse(content={"status": "error"}, status_code=200)


# ---------------------------------------------------------------------------
# Internal message handler (placeholder – replace with service calls)
# ---------------------------------------------------------------------------
async def handle_incoming_message(message: dict, context: dict):
    """
    Processes a single incoming WhatsApp message.
    Extend this function to call your AI and send a reply.

    Args:
        message: The message object from the webhook payload.
        context:  The parent 'value' object containing metadata (phone number id, etc.).
    """
    sender = message.get("from")
    msg_type = message.get("type")
    msg_id = message.get("id")

    logger.info("Message from %s | type=%s | id=%s", sender, msg_type, msg_id)

    if msg_type == "text":
        text = message.get("text", {}).get("body", "")
        logger.info("Text content: %s", text)
        
        result = process_message_logic(sender, text)
        
        if result["type"] in ("text", "booking"):
            send_text_message(sender, result["response"])
        elif result["type"] == "image":
            for url in result["images"]:
                send_image_message(sender, url)
