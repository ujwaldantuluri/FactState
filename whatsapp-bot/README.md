# FactState WhatsApp Bot

WhatsApp bot using wppconnect that integrates with the micro-services backend for:
- News fact-checking
- Image authenticity analysis
- E-commerce site risk checks (basic and advanced)

Behavioral rules:
- Only interact with contacts in ALLOWED_NUMBERS.
- Ignore all messages unless the exact phrase "factstate" (case-insensitive) is received.
- On "factstate" from an allowed number, show a consent/disclaimer and a "Start Assessment" button.
- All questions via interactive buttons when possible; numeric/text inputs are validated.
- Provide a "Restart" and "Help" button on every step.

## Setup

1. Ensure the backend is running:
   - From workspace root:
     - Start FastAPI: `uvicorn micro-services.main:app --reload --port 8000`
2. Install Node.js deps and configure env:
   - `cd whatsapp-bot`
   - `cp .env.example .env` and edit values (ALLOWED_NUMBERS, BACKEND_BASE_URL)
   - `npm install`
3. Start the bot:
   - `npm run start`
   - Scan the QR code with the allowed WhatsApp account.

## Flows
- Send exactly `factstate` to begin.
- Choose: News, Image, E-commerce (Basic), E-commerce (Advanced)
- Follow prompts. Restart/Help always available.

## Notes
- Image analysis requires sending an actual image after choosing Image.
- E-commerce requires a valid URL.
