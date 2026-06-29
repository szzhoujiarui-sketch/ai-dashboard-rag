from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
import uuid
from time import perf_counter
from typing import Optional
from ...config import settings

class RAGEngine:
    def __init__(self):
        self.vectorstore: Optional[Chroma] = None
        self.qa_chain: Optional[RetrievalQA] = None
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url
        )
        self.llm = ChatOpenAI(
            model_name=settings.llm_model_name,
            temperature=0.7,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url
        )

    async def initialize(self):
        os.makedirs(settings.upload_dir, exist_ok=True)
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        
        self.vectorstore = Chroma(
            persist_directory=settings.chroma_persist_dir,
            embedding_function=self.embeddings,
            collection_name="documents"
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=True
        )

    async def ingest_document(self, file_path: str) -> dict:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, autodetect_encoding=True)
        
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        document_id = str(uuid.uuid4())
        for chunk in chunks:
            chunk.metadata['document_id'] = document_id
        
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        self.vectorstore.add_texts(
            texts=[chunk.page_content for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            ids=ids
        )
        
        from app.modules.dashboard.metrics import metrics_collector
        metrics_collector.increment_documents()
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": os.path.basename(file_path),
            "chunks": len(chunks),
            "pages": len(documents) if hasattr(documents, '__len__') else 1
        }

    async def query(self, question: str, k: int = 4) -> dict:
        if not self.qa_chain:
            raise RuntimeError("RAG engine not initialized")
        
        started_at = perf_counter()
        result = self.qa_chain.invoke({"query": question})
        response_time = perf_counter() - started_at
        
        from app.modules.dashboard.metrics import metrics_collector
        metrics_collector.increment_queries(response_time)
        
        return {
            "answer": result['result'],
            "sources": [
                {
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                }
                for doc in result['source_documents']
            ]
        }

    async def delete_document(self, document_id: str) -> bool:
        if not self.vectorstore:
            return False
        self.vectorstore.delete(where={"document_id": document_id})
        return True

    async def cleanup(self):
        if self.vectorstore:
            self.vectorstore.persist()
