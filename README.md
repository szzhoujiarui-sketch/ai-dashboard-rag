# AI Dashboard + RAG MVP / 模块化 AI 仪表盘与 RAG 问答系统

> A modular AI dashboard with RAG (Retrieval-Augmented Generation) Q&A system.

## 技术栈 / Tech Stack

### 后端 / Backend
- **FastAPI** - 高性能异步 Web 框架 / High-performance async web framework
- **LangChain** - LLM 应用框架 / LLM application framework
- **ChromaDB** - 本地向量数据库 / Local vector database
- **OpenAI API** - LLM 与嵌入模型（兼容 OpenAI 接口）/ LLM and embeddings (OpenAI-compatible)

### 前端 / Frontend
- **React 18** + **TypeScript**
- **Vite** - 构建工具 / Build tool
- **TailwindCSS** - 样式框架 / Styling framework
- **Recharts** - 数据可视化 / Data visualization

## 项目结构 / Project Structure

```
ai-dashboard-rag/
├── backend/          # FastAPI 后端（可替换为 Flask/Django）/ FastAPI backend (replaceable with Flask/Django)
│   └── app/
│       ├── modules/
│       │   ├── rag/          # RAG 引擎（可替换向量数据库）/ RAG engine (replaceable vector DB)
│       │   ├── dashboard/   # 指标收集（可替换数据源）/ Metrics collector (replaceable data source)
│       │   └── api/         # API 路由 / API routes
│       └── utils/           # 工具函数 / Utilities
├── frontend/         # React 前端（可替换为 Vue/Next.js）/ React frontend (replaceable with Vue/Next.js)
│   └── src/
│       ├── components/      # UI 组件 / UI components
│       ├── services/        # API 服务 / API services
│       └── App.tsx
└── docker-compose.yml
```

## 快速开始 / Quick Start

### 环境要求 / Requirements
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### 后端启动 / Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY / Edit .env and fill in OPENAI_API_KEY
uvicorn app.main:app --reload
```

### 前端启动 / Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker 启动 / Start with Docker

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入 API Key / Edit backend/.env and fill in API Key
docker-compose up --build
```

## 功能特性 / Features

- **文档上传与解析**：支持 PDF、TXT、Markdown / Document upload & parsing: PDF, TXT, Markdown
- **向量检索**：基于 ChromaDB 的语义搜索 / Vector search with ChromaDB
- **智能问答**：基于 RAG 的文档问答 / RAG-based document Q&A
- **数据仪表盘**：查询趋势、准确率、系统指标 / Dashboard with query trends, accuracy, system metrics
- **模块化设计**：RAG 引擎、向量存储、前端组件均可独立替换 / Modular design: RAG engine, vector store, and frontend components are independently replaceable

## 模块替换指南 / Module Replacement Guide

### 替换向量数据库 / Replace Vector Database
修改 `backend/app/modules/rag/engine.py` 中的 `VectorStore` 实现：
- ChromaDB → Pinecone → Weaviate → Milvus

### 替换 LLM / Replace LLM
修改 `backend/app/modules/rag/engine.py` 中的 `ChatOpenAI`：
- OpenAI → Anthropic → Local LLM (Ollama)

### 替换前端框架 / Replace Frontend Framework
前端为纯 React + Vite，可迁移至：
- Next.js
- Vue 3 + Vite
- SvelteKit

## 部署 / Deployment

### 生产环境 / Production

```bash
# 后端 / Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端 / Frontend
cd frontend
npm run build
npm run preview
```

## License

MIT
