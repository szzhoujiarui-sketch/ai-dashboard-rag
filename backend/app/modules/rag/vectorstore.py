from typing import List, Dict, Any
import chromadb

class VectorStore:
    def __init__(self, persist_directory: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        ids = [str(hash(doc['content'])) for doc in documents]
        self.collection.add(
            documents=[doc['content'] for doc in documents],
            metadatas=[doc.get('metadata', {}) for doc in documents],
            ids=ids
        )
        return len(documents)

    def search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        return [
            {
                "content": doc,
                "metadata": meta,
                "distance": dist
            }
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]
