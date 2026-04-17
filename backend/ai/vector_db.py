import chromadb
from chromadb.config import Settings as ChromaSettings
import os
from .embedding import get_embedding_model
from ..config import settings

# Use config settings for directory
CHROMA_DIR = os.path.join(settings.data_dir, "chroma")

class VectorDB:
    def __init__(self):
        if not os.path.exists(CHROMA_DIR):
            os.makedirs(CHROMA_DIR)
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.embedding_model = get_embedding_model()

    def get_collection(self, workspace_id: str):
        collection_name = f"kb_{workspace_id}".replace("-", "_")
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, workspace_id: str, documents: list[str], metadatas: list[dict], ids: list[str]):
        collection = self.get_collection(workspace_id)
        embeddings = self.embedding_model.embed_documents(documents)
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, workspace_id: str, query_text: str, n_results: int = 5, where: dict = None):
        collection = self.get_collection(workspace_id)
        query_embedding = self.embedding_model.embed_query(query_text)
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

# Global instance
vector_db = None

def get_vector_db():
    global vector_db
    if vector_db is None:
        vector_db = VectorDB()
    return vector_db
