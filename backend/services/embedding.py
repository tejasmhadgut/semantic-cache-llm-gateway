

from sentence_transformers import SentenceTransformer
from functools import lru_cache
model = None

def load_model():
    global model
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
@lru_cache(maxsize=1000)
def get_embedding(text: str) -> tuple[float]:
   return tuple(model.encode(text).tolist())

