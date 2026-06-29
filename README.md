# WhatsApp AI Receptionist

An AI-powered receptionist that automatically handles incoming WhatsApp messages using the **Meta Cloud API**, **Gemini API** for natural language understanding, and **Cloudinary** for image processing.

---

## Project Overview

This project provides a complete solution to automate WhatsApp interactions:
- Handles user queries intelligently using Gemini.
- Supports an automated booking flow.
- Fetches and serves images via Cloudinary based on user intent.
- Human handoff capability to pause the bot when manual intervention is needed.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Docker (optional) | 24+ |
| Meta Developer Account | — |
| Gemini API Key | — |
| Cloudinary Account | — |

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

Create a `.env` file in the project root:

```dotenv
# WhatsApp / Meta Cloud API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
VERIFY_TOKEN=my_verify_token

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Cloudinary (Images)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret
```

### 3. Run locally

Run the application using `uvicorn`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 4. Expose locally with a tunnel

```bash
# Using ngrok
ngrok http 8000
```
Register the `https://<your-ngrok-id>.ngrok-free.app/webhook` URL in the Meta Developer Console under webhook configurations.

---

## Running with Docker

### Docker Build

Build the optimized container image:

```bash
docker build -t whatsapp-ai-receptionist .
```

### Docker Run

Run the container, passing the `.env` file and exposing the correct port:

```bash
docker run -p 8000:8000 --env-file .env whatsapp-ai-receptionist
```

You can optionally override the port using the `PORT` environment variable:

```bash
docker run -p 8080:8080 -e PORT=8080 --env-file .env whatsapp-ai-receptionist
```

---

## Environment Variables Reference

| Variable | Description |
|----------|-------------|
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | Meta permanent / long-lived access token |
| `VERIFY_TOKEN` | Webhook verification token |
| `GEMINI_API_KEY` | Gemini API key |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary Cloud Name |
| `CLOUDINARY_API_KEY` | Cloudinary API Key |
| `CLOUDINARY_API_SECRET` | Cloudinary API Secret |
| `PORT` | The port the application will run on (Default: 8000) |

---

## License

MIT
