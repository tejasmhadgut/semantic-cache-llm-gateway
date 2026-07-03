

from sentence_transformers import SentenceTransformer

model = None

def load_model():
    global model
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def get_embedding(text: str) -> list[float]:
   embeddings = model.encode(text)
   return embeddings.tolist()

