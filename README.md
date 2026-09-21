# Athena — Local AI Ticket Classifier

Classify support tickets on your machine. No cloud APIs, no keys.

**Stack:** Django + Django REST Framework (Poetry) · React + Vite (pnpm)  
**Classifier:** local TF-IDF model, with an optional Ollama adapter if you later install it.

## Quick start

```bash
make install
make migrate
make seed
```

Then run both processes:

```bash
make backend    # http://127.0.0.1:8000
make frontend   # http://127.0.0.1:5173
```

Open **http://127.0.0.1:5173**. The Vite dev server proxies `/api` to Django.

## How classification works

1. Title + body are scored against category prototypes (Spanish + English) with TF-IDF cosine similarity.
2. Keyword hits boost the matching category and extract tags.
3. Priority comes from urgency language (`outage`, `caído`, `breach`, …).
4. Confidence is the margin between the top two categories.

If Ollama is running on `localhost:11434`, Athena will try it first and fall back to the local model on any failure.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/categories/` | Category catalog |
| `GET` | `/api/tickets/` | Ticket inbox |
| `POST` | `/api/tickets/` | Create + classify |
| `POST` | `/api/classify/` | Preview without saving |
| `POST` | `/api/tickets/:id/correct/` | Human override |
| `GET` | `/api/stats/` | Inbox totals |
