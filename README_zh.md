# AI Dashboard + RAG MVP

模块化 AI 仪表盘与 RAG（检索增强生成）问答系统。

## 技术栈

### 后端
- **FastAPI** - 高性能异步 Web 框架
- **LangChain** - LLM 应用框架
- **ChromaDB** - 本地向量数据库
- **OpenAI API** - LLM 与嵌入模型（兼容 OpenAI 接口）

### 前端
- **React 18** + **TypeScript**
- **Vite** - 构建工具
- **TailwindCSS** - 样式框架
- **Recharts** - 数据可视化

## 项目结构

```
ai-dashboard-rag/
├── backend/          # FastAPI 后端（可替换为 Flask/Django）
│   └── app/
│       ├── modules/
│       │   ├── rag/          # RAG 引擎（可替换向量数据库）
│       │   ├── dashboard/   # 指标收集（可替换数据源）
│       │   └── api/         # API 路由
│       └── utils/           # 工具函数
├── frontend/         # React 前端（可替换为 Vue/Next.js）
│   └── src/
│       ├── components/      # UI 组件
│       ├── services/        # API 服务
│       └── App.tsx
└── docker-compose.yml
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY
uvicorn app.main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### Docker 启动

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入 API Key
docker-compose up --build
```

## 功能特性

- **文档上传与解析**：支持 PDF、TXT、Markdown
- **向量检索**：基于 ChromaDB 的语义搜索
- **智能问答**：基于 RAG 的文档问答
- **数据仪表盘**：查询趋势、准确率、系统指标
- **模块化设计**：RAG 引擎、向量存储、前端组件均可独立替换

## 模块替换指南

### 替换向量数据库
修改 `backend/app/modules/rag/engine.py` 中的 `VectorStore` 实现：
- ChromaDB → Pinecone → Weaviate → Milvus

### 替换 LLM
修改 `backend/app/modules/rag/engine.py` 中的 `ChatOpenAI`：
- OpenAI → Anthropic → Local LLM (Ollama)

### 替换前端框架
前端为纯 React + Vite，可迁移至：
- Next.js
- Vue 3 + Vite
- SvelteKit

## 部署

### 生产环境
```bash
# 后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端
cd frontend
npm run build
npm run preview
```

## License

MIT
