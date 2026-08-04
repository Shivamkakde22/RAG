from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-mpnet-base-v2"
EMBEDDING_DIM = 768

model = SentenceTransformer(MODEL_NAME)

def embed(text: str):
    return model.encode(text).tolist()

def embed_batch(texts: list[str]):
    return model.encode(texts).tolist()
