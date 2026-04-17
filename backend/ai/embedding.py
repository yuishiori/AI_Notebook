from sentence_transformers import SentenceTransformer
import os

# Use bge-m3 as specified in the document
MODEL_NAME = "BAAI/bge-m3"

class EmbeddingModel:
    def __init__(self, model_name=MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str):
        return self.model.encode(text).tolist()

    def embed_documents(self, texts: list[str]):
        return self.model.encode(texts).tolist()

# Global instance
embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = EmbeddingModel()
    return embedding_model
