# Fake E-commerce Website Detection (Backend)

FastAPI backend for the Multi-Fake Detection Platform's hero module: Fake E-commerce Site Risk Detection.

## Features
- 5-layer heuristic scoring: domain/infra, content/UX, visual/brand, threat intel, user feedback.
- Explainable results with reasons and actionable advice.
- Pre- and post-purchase flow with user feedback to update scores over time.
- SQLite via SQLModel for persistence.

## Quickstart

1. Create a virtual environment and install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the API

```powershell
uvicorn app.main:app --reload --port 8000
```

3. Try it
- POST http://localhost:8000/api/check-site { "url": "https://example.com" }
- POST http://localhost:8000/api/feedback { "url": "https://example.com", "delivered": true }
- GET  http://localhost:8000/api/site-history?url=https://example.com

Open http://localhost:8000/docs for Swagger UI.

## Configuration
Environment variables (optional):
- DB_URL (default: sqlite:///data/app.db)
- RISK_WEIGHTS_JSON (override default layer weights as JSON)
- SAFE_BROWSING_API_KEY, PHISHTANK_API_KEY (optional; threat intel stubs will use when present)

## Project Structure
```
app/
  main.py            # FastAPI app, routers include
  config.py          # Settings & weights
  db.py              # SQLModel engine/session
  models/
    schemas.py       # Pydantic models (requests/responses)
    tables.py        # SQLModel tables
  routers/
    site.py          # /api endpoints
  services/
    scoring.py       # Combines layers + explainability
    layers/
      domain_infra.py
      content_ux.py
      visual_brand.py
      threat_intel.py
      user_feedback.py
  utils/
    parsing.py
    validators.py

```

## Tests
Run unit tests:
```powershell
pytest -q
```

## Notes
- This is a production-ready scaffold with sensible defaults and clear extension points.
- External threat intel calls are mocked/stubbed by default; add API keys to enable.
