# RAG Security Gateway

A defensive starter project for scanning documents and placing policy gates around a Retrieval-Augmented Generation (RAG) or OpenAI-compatible chat endpoint. It combines a browser-only dashboard (`index.html`) with a separate FastAPI backend (`main.py`). The dashboard and backend are **not automatically connected**; the backend API can be tested separately through `/docs`.

## What is included

- Regex-based detectors for prompt-injection patterns, common credentials/tokens, PII, payment-card candidates (Luhn validation), and sensitive business data.
- Allow/redact/block policy gate and bounded Base64 decoding for detection (decoded content is never executed).
- FastAPI authentication using Argon2 password hashes and expiring JWTs, first-admin bootstrap, login throttling, and optional TOTP MFA setup.
- Upload size/type/extraction limits; sensitive-data redaction before document text is persisted; risk-scored documents are excluded from retrieval at risk >= 70.
- RAG retrieval with a server-side instruction to treat retrieved documents as untrusted data.
- OpenAI-compatible `POST /v1/chat/completions`, document listing/deletion, trace lookup, health endpoint, and hash-linked audit verification.
- Regression tests under `tests/`.

## Run locally (Python)

Python 3.11+ is recommended. Install Tesseract OCR separately if you need image scanning.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

For tests, install the development dependency set with `pip install -r requirements-dev.txt`.

Set a persistent secret before starting. On PowerShell:

```powershell
$env:JWT_SECRET = "replace-with-a-long-random-secret"
uvicorn main:app --reload --port 8000
```

On macOS/Linux:

```bash
export JWT_SECRET="replace-with-a-long-random-secret"
uvicorn main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs`. The first `/auth/register` call creates the initial admin account; public registration is closed after that. Use a password of at least 12 characters. Log in at `/auth/login` and send the returned token as `Authorization: Bearer <token>`.

To use a hosted OpenAI-compatible provider, set `UPSTREAM_URL`, `MODEL`, and the provider key environment variable expected by your deployment (`GROQ_API_KEY` for the default Groq URL). For local Ollama, set `UPSTREAM_URL=http://localhost:11434/v1` and `MODEL=llama3.1`; ensure Ollama is running and the model is downloaded.

## Docker Compose

Copy `.env.example` to `.env`, replace both passwords with long random values, and then run:

```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.1
```

The API binds to `127.0.0.1:8000` by default. Put it behind an authenticated TLS reverse proxy before exposing it to a network. Do not commit `.env` or real credentials.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Important limitations / production checklist

- Regex rules are heuristic and can have false positives and false negatives. They are not a proof against prompt injection or data exfiltration.
- Login throttling is process-local. Use a shared limiter (for example Redis) for multi-worker/multi-instance deployments.
- Audit hash chaining detects some tampering but is not immutable storage; forward audit events to a separately controlled logging service.
- The starter uses additive schema migration for compatibility. Use Alembic or another reviewed migration process for production schema changes.
- TOTP secrets are stored in the database; encrypt them at rest and provide a secure recovery process before production use.
- OCR requires the Tesseract system binary. PDFs/DOCX and image parsing should be run with resource limits in a sandbox for hostile uploads.
- Retrieval uses simple SQL substring matching, not a vector database or document-level ACL system. Add tenant/permission filtering before use with real confidential corpora.
- There is no SSO, production key rotation, comprehensive admin user-management UI, distributed rate limiting, or full penetration-test coverage yet.
- `index.html` is a browser-only dashboard with its own local encrypted storage; it does not call this API by default. Do not treat browser-side controls as server-side security enforcement.
