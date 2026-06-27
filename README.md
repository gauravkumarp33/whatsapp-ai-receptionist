# WhatsApp AI Receptionist

An AI-powered receptionist that automatically handles incoming WhatsApp messages using the **Meta Cloud API** and an **OpenAI** language model.

---

## Project Structure

```
whatsapp-ai-receptionist/
├── prompts/          # System-prompt text files for the AI
├── data/             # Static reference data (FAQs, business hours, etc.)
├── services/         # Business-logic modules (whatsapp_service, ai_service, …)
├── main.py           # FastAPI application & webhook endpoints
├── config.py         # Centralised settings via Pydantic BaseSettings
├── requirements.txt  # Python dependencies
├── Dockerfile        # Multi-stage container build
└── README.md         # This file
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Docker (optional) | 24+ |
| Meta Developer Account | — |
| OpenAI API Key | — |

---

## Quick Start

### 1. Clone & install dependencies

```bash
git clone https://github.com/your-org/whatsapp-ai-receptionist.git
cd whatsapp-ai-receptionist

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root (never commit this file):

```dotenv
# WhatsApp / Meta Cloud API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
WHATSAPP_VERIFY_TOKEN=my_verify_token   # Must match what you set in Meta dashboard

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# App
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

### 3. Run locally

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 4. Expose locally with a tunnel (for Meta webhook registration)

```bash
# Using ngrok
ngrok http 8000
```

Copy the HTTPS URL and register it in the **Meta Developer Console** under  
**WhatsApp → Configuration → Webhook URL**: `https://<your-ngrok-id>.ngrok.io/webhook`

---

## Running with Docker

```bash
# Build
docker build -t whatsapp-ai-receptionist .

# Run
docker run -p 8000:8000 --env-file .env whatsapp-ai-receptionist
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/webhook` | Meta webhook verification handshake |
| `POST` | `/webhook` | Receive incoming WhatsApp messages |

---

## Configuration Reference

All configuration lives in [`config.py`](config.py) and is read from environment variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `WHATSAPP_PHONE_NUMBER_ID` | `""` | Your WhatsApp phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | `""` | Meta permanent / long-lived access token |
| `WHATSAPP_VERIFY_TOKEN` | `my_verify_token` | Webhook verification token |
| `WHATSAPP_API_VERSION` | `v19.0` | Meta Graph API version |
| `OPENAI_API_KEY` | `""` | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model to use |
| `APP_HOST` | `0.0.0.0` | Uvicorn host |
| `APP_PORT` | `8000` | Uvicorn port |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Next Steps

- **`services/`** – Implement `whatsapp_service.py` (send messages) and `ai_service.py` (call OpenAI).
- **`prompts/`** – Add `system_prompt.txt` with your receptionist persona and instructions.
- **`data/`** – Add business info, FAQs, or any static context the AI should reference.

---

## License

MIT
