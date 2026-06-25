# AI Dashboard + RAG MVP

> A modular AI dashboard with RAG (Retrieval-Augmented Generation) Q&A system.

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
- **Dashboard**: Query trends, accuracy, system metrics
- **Modular design**: RAG engine, vector store, and frontend components are independently replaceable

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
# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd frontend
npm run build
npm run preview
```

## License

MIT
