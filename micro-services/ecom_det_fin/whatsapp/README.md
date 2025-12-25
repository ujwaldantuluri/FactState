# FactState WhatsApp Service (WPPConnect)

This is a standalone WhatsApp integration for FactState using [WPPConnect](https://wppconnect.io/).
It lives in `whatsapp/` and does NOT modify the Python backend.

## Features
- Start a WhatsApp session and expose endpoints:
  - `GET /health` — service status
  - `GET /qr` — fetch the latest QR code (base64 string); refresh to pair your phone
  - `POST /send` — send a custom message to a phone number
  - `POST /scan-and-send` — call FastAPI `/api/check-site` for a URL and WhatsApp the result
- Optional header token protection via `WHATSAPP_API_TOKEN`

## Setup (Windows PowerShell)

1. Install Node.js 18+ and enable corepack if needed.
2. Create env file:

```powershell
Copy-Item .env.example .env
# Then edit .env values as needed
```

3. Install dependencies:

```powershell
cd whatsapp
npm install
```

4. Start the WhatsApp service in dev mode:

```powershell
npm run dev
```

5. Pair WhatsApp:
- Visit `http://localhost:8088/qr` repeatedly until a large base64 block appears
- Copy the base64 and preview it (or add a small HTML page to embed it). On your phone, scan the QR via WhatsApp Web.

6. Test send:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8088/send -Headers @{"x-api-token"="$env:WHATSAPP_API_TOKEN"} -Body (@{ phone = "+15551234567"; message = "Hello from FactState" } | ConvertTo-Json) -ContentType 'application/json'
```

7. Scan and send a report:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8088/scan-and-send -Headers @{"x-api-token"="$env:WHATSAPP_API_TOKEN"} -Body (@{ url = "https://example.com"; phone = "+15551234567" } | ConvertTo-Json) -ContentType 'application/json'
```

## Configuration

Edit `.env`:

- `PORT` — service port (default `8088`)
- `FASTAPI_BASE_URL` — points to your FastAPI API prefix (default `http://127.0.0.1:8000/api`)
- `WHATSAPP_SESSION` — WPPConnect session name
- `WHATSAPP_API_TOKEN` — header token for basic protection

## Notes
- The service stores the latest QR string under `whatsapp/qr/latest.txt`.
- This project is isolated. It doesn’t alter the Python backend.
- For production, consider a persistent store for sessions and adding HTTPS + stronger auth.
