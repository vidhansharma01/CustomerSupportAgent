# Customer Support Agent 🤖

A production-grade AI customer support agent built with LangGraph, FastAPI, React, PostgreSQL, Pinecone, and OpenAI.

## Architecture

```
React UI  ──►  FastAPI  ──►  LangGraph Agent  ──►  OpenAI GPT-4o
                                   │
                    ┌──────────────┼──────────────────┐
                    ▼              ▼                   ▼
              KB Search     Customer Lookup    Action Executor
          (Pinecone + FTS)    (Postgres)      (Refund, Cancel…)
                    │              │                   ▼
                 Pinecone       Postgres          Escalate →
               (semantic)       (FTS +           SupportTicket
                                metadata)
```

## Features

| Feature | Implementation |
|---------|----------------|
| **Knowledge Base Q&A** | Pinecone semantic search + Postgres full-text search (hybrid) |
| **Customer Lookup** | Fetch account info, tier, order history |
| **Approved Actions** | `update_email`, `update_phone`, `request_refund`, `cancel_order`, `resend_invoice` |
| **Human Escalation** | Creates `SupportTicket` DB record + returns ticket ID |
| **Streaming** | Server-Sent Events from FastAPI → React `EventSource` |
| **LLM Testing** | DeepEval with AnswerRelevancy, Faithfulness, Hallucination metrics |

---

## Prerequisites

1. **Python 3.11+** — [python.org](https://www.python.org/downloads/)
2. **uv** — `pip install uv`
3. **Node.js 18+** — [nodejs.org](https://nodejs.org/)
4. **PostgreSQL 15 or 16** (plain install, no extensions needed)
   - Windows: [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
5. **Pinecone account** (free tier) — [app.pinecone.io](https://app.pinecone.io)

---

## Quick Start

### 1. Install dependencies

```powershell
uv sync
```

### 2. Configure environment

```powershell
copy .env.example .env
```

Open `.env` and fill in the required values:

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/customer_support
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/customer_support
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=customer-support-kb
PINECONE_NAMESPACE=documents
```

### 3. Create Pinecone index

1. Go to [app.pinecone.io](https://app.pinecone.io) → **Create Index**
2. Use these settings:

   | Setting | Value |
   |---------|-------|
   | Name | `customer-support-kb` |
   | Dimensions | `1536` |
   | Metric | `cosine` |
   | Cloud | `aws` |
   | Region | `us-east-1` |

3. Copy the **API key** from the Pinecone dashboard into `.env`

### 4. Create the Postgres database

In `psql` or pgAdmin — no extensions needed:

```sql
CREATE DATABASE customer_support;
```

### 5. Run database migrations

```powershell
uv run alembic upgrade head
```

### 6. Seed sample data

```powershell
# Seed 5 customers + 10 orders into Postgres
uv run python -m backend.seeds.customers

# Embed 10 KB documents → Pinecone (vectors) + Postgres (metadata for FTS)
# Requires OPENAI_API_KEY and PINECONE_API_KEY in .env
uv run python -m backend.seeds.documents
```

### 7. Start the backend

```powershell
uv run uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 8. Start the frontend *(new terminal)*

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Project Structure

```
CustomerSupportAgent/
├── pyproject.toml              ← uv/Python deps
├── alembic.ini                 ← DB migration config
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial.py      ← Schema migration
├── backend/
│   ├── main.py                 ← FastAPI app
│   ├── config.py               ← Settings (pydantic-settings)
│   ├── database.py             ← SQLAlchemy async engine
│   ├── models/
│   │   ├── customer.py         ← Customer, Order
│   │   ├── document.py         ← Document metadata (KB)
│   │   └── ticket.py           ← SupportTicket, ConversationMessage
│   ├── schemas/                ← Pydantic v2 request/response models
│   ├── agent/                  ← LangGraph agent
│   │   ├── graph.py            ← StateGraph definition
│   │   ├── state.py            ← AgentState TypedDict
│   │   ├── nodes.py            ← Node functions (llm, tools, escalate)
│   │   └── tools/
│   │       ├── kb_search.py    ← Pinecone semantic + Postgres FTS hybrid
│   │       ├── customer_lookup.py
│   │       ├── action_executor.py
│   │       └── escalate.py
│   ├── services/
│   │   ├── embedding.py        ← OpenAI embeddings
│   │   └── pinecone_service.py ← Pinecone upsert / query
│   └── seeds/
│       ├── customers.py
│       └── documents.py
├── frontend/                   ← Vite + React + Tailwind
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── ChatWindow.tsx
│       │   ├── MessageBubble.tsx
│       │   ├── ChatInput.tsx
│       │   ├── TypingIndicator.tsx
│       │   ├── EscalationBanner.tsx
│       │   └── SourcesList.tsx
│       └── hooks/
│           └── useChat.ts
└── tests/
    ├── conftest.py
    ├── test_agent.py           ← DeepEval LLM quality tests
    └── test_tools.py           ← Unit tests
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/chat` | Send a message, get agent response |
| GET | `/api/chat/history/{conversation_id}` | Conversation history |
| GET | `/api/admin/tickets` | List support tickets |
| PATCH | `/api/admin/tickets/{id}` | Update ticket status |
| GET | `/api/admin/customers` | List customers |

---

## Agent Tools

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | Pinecone semantic search + Postgres FTS, results merged |
| `lookup_customer` | Fetch customer account info and order history |
| `execute_customer_action` | Run an approved action (Pydantic-validated allowlist) |
| `escalate_to_human` | Create a support ticket and hand off to human agent |

## Approved Actions

| Action | Params | Validation |
|--------|--------|------------|
| `update_email` | `new_email` | Email format |
| `update_phone` | `new_phone` | String |
| `request_refund` | `amount`, `order_number`, `reason` | amount ≤ \$500 |
| `cancel_order` | `order_number` | Order must not be delivered/cancelled |
| `resend_invoice` | `order_number` | Order must exist |

---

## Running Tests

```powershell
# Unit + schema + tool logic tests
uv run pytest tests/test_tools.py -v

# LLM quality tests via DeepEval (makes real OpenAI calls — billed)
uv run pytest tests/test_agent.py -v

# Full suite with coverage report
uv run pytest --cov=backend --cov-report=html
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | **Required** |
| `OPENAI_MODEL` | Chat model | `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `DATABASE_URL` | Async Postgres URL (`asyncpg`) | **Required** |
| `SYNC_DATABASE_URL` | Sync Postgres URL (`psycopg2`, Alembic only) | **Required** |
| `PINECONE_API_KEY` | Pinecone API key | **Required** |
| `PINECONE_INDEX_NAME` | Pinecone index name | `customer-support-kb` |
| `PINECONE_NAMESPACE` | Pinecone namespace | `documents` |
| `REFUND_LIMIT_USD` | Max refund the agent can approve | `500.0` |
| `ESCALATION_THRESHOLD` | Tool call failures before auto-escalation | `3` |
