# AI Dashboard + RAG MVP

> A modular AI dashboard with RAG (Retrieval-Augmented Generation) Q&A system.

[中文](README_zh.md)

## Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **LangChain** - LLM application framework
- **ChromaDB** - Local vector database
- **OpenAI API** - LLM and embeddings (OpenAI-compatible)

### Frontend
- **React 18** + **TypeScript**
- **Vite** - Build tool
- **TailwindCSS** - Styling framework
- **Recharts** - Data visualization

## Project Structure

```
ai-dashboard-rag/
├── backend/          # FastAPI backend (replaceable with Flask/Django)
│   └── app/
│       ├── modules/
│       │   ├── rag/          # RAG engine (replaceable vector DB)
│       │   ├── dashboard/   # Metrics collector (replaceable data source)
│       │   └── api/         # API routes
│       └── utils/           # Utilities
├── frontend/         # React frontend (replaceable with Vue/Next.js)
│   └── src/
│       ├── components/      # UI components
│       ├── services/        # API services
│       └── App.tsx
└── docker-compose.yml
```

## Quick Start

### Requirements
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Edit .env and fill in OPENAI_API_KEY
uvicorn app.main:app --reload
```

### Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### Start with Docker

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and fill in API Key
docker-compose up --build
```

## Features

- **Document upload & parsing**: PDF, TXT, Markdown
- **Vector search**: ChromaDB-based semantic search
- **RAG-based Q&A**: Ask questions about uploaded documents
- **Dashboard**: Query trends, response time, system runtime metrics
- **Modular design**: RAG engine, vector store, and frontend components are independently replaceable

## Configuration

Backend environment variables are defined in `backend/.env.example`:

- `OPENAI_API_KEY`: required for LLM and embedding calls.
- `OPENAI_BASE_URL`: OpenAI-compatible API endpoint.
- `MODEL_NAME`: chat model used by LangChain.
- `CHROMA_PERSIST_DIR`: local ChromaDB persistence directory.
- `UPLOAD_DIR`: local uploaded-document directory.
- `ALLOWED_ORIGINS`: comma-separated CORS allowlist for the frontend.

## Testing

```bash
cd backend
pytest
```

The backend tests cover API health, request validation, document registry metadata, upload path boundaries, and dashboard metrics without calling external LLM services.

## Demo Caveats

This repository is an MVP/demo baseline. Production deployments should add authentication, tenant isolation, file scanning, access control, rate limiting, and managed secret storage.

## Module Replacement Guide

### Replace Vector Database
Modify `VectorStore` implementation in `backend/app/modules/rag/engine.py`:
- ChromaDB → Pinecone → Weaviate → Milvus

### Replace LLM
Modify `ChatOpenAI` in `backend/app/modules/rag/engine.py`:
- OpenAI → Anthropic → Local LLM (Ollama)

### Replace Frontend Framework
Frontend is pure React + Vite, can be migrated to:
- Next.js
- Vue 3 + Vite
- SvelteKit

## Deployment

### Production
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

cd frontend
npm run build
npm run preview
```

## License

MIT
