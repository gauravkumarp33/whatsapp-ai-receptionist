import google.generativeai as genai

from config import settings
from services.prompt_service import get_business_prompt

genai.configure(api_key=settings.GEMINI_API_KEY)

_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=get_business_prompt(),
)


def generate_response(user_message: str, conversation_history: list[dict]) -> str:
    """
    conversation_history: list of {"role": "user"|"model", "parts": "..."}
    """
    chat = _model.start_chat(history=conversation_history)
    response = chat.send_message(user_message)
    return response.text
