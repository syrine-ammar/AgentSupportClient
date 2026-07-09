import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "chroma_data"
COLLECTION_NAME = "techmarket_docs"

client = chromadb.PersistentClient(path=CHROMA_PATH)

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = client.get_collection(
    COLLECTION_NAME,
    embedding_function=embedding_fn
)

results = collection.query(
    query_texts=["Combien de temps ai-je pour retourner un produit ?"],
    n_results=2,
    include=["documents", "metadatas", "distances", "embeddings"]
)

print(results)