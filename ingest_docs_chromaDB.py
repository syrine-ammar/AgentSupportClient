"""
ingest_docs_chromaDB.py
------------------------
Reads all markdown docs in /docs, chunks them, and indexes them into ChromaDB.
Run this once (or whenever docs change) to (re)build the vector store.

Usage:
    python ingest_docs_chromaDB.py
"""

import os
import glob
import chromadb
from chromadb.utils import embedding_functions

DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_data")
COLLECTION_NAME = "techmarket_docs"

CHUNK_SIZE = 500       # caractères par chunk (volontairement simple)
CHUNK_OVERLAP = 100    # overlap entre chunks pour ne pas couper le contexte
#This means the next chunk starts 100 characters before the previous chunk ends.


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Découpe un texte en chunks avec overlap.
    Stratégie simple par caractères.
    on peux remplacer ça par un chunking par sections markdown (## headers).
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]  # enlève les chunks vides


def chunk_by_markdown_sections(text: str, source_name: str) -> list[dict]:
    """
    Stratégie plus intelligente : découpe par sections "## titre".
    Garde le contexte du titre dans chaque chunk -> meilleure pertinence RAG.
    """
    sections = text.split("\n## ")
    chunks = []
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        # Remet le "##" qu'on a enlevé avec le split (sauf pour le 1er bloc = titre principal)
        content = section if i == 0 else "## " + section
        content = content.strip()
        if len(content) < 20:
            continue
        chunks.append(content)
    return chunks


def load_documents() -> list[dict]:
    """
    Lit tous les fichiers .md du dossier docs/ et retourne une liste de chunks
    avec leurs métadonnées (source, chunk_index).
    """
    documents = []
    md_files = glob.glob(os.path.join(DOCS_FOLDER, "*.md"))

    if not md_files:
        print(f"⚠️  Aucun fichier .md trouvé dans {DOCS_FOLDER}")
        return documents

    for filepath in md_files:
        source_name = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_by_markdown_sections(text, source_name)

        for idx, chunk in enumerate(chunks):
            documents.append({
                "id": f"{source_name}_{idx}",
                "content": chunk,
                "source": source_name,
                "chunk_index": idx,
                #idx → the chunk number
            })

    return documents


def build_chroma_collection():
    """Crée (ou recrée) la collection ChromaDB et y insère tous les documents."""

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Embedding function par défaut de Chroma (all-MiniLM-L6-v2, local, gratuit)
    # NOTE: ce modèle est téléchargé automatiquement au premier lancement (~80MB).
    # Si tu es derrière un réseau restrictif et que le téléchargement échoue,

    #embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    # Recrée la collection à chaque run pour éviter les doublons en dev
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' existante supprimée.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"description": "TechMarket support docs (policies, FAQ)"},
    )

    documents = load_documents()

    if not documents:
        print("Aucun document à indexer.")
        return

    collection.add(
        ids=[d["id"] for d in documents],
        documents=[d["content"] for d in documents],
        metadatas=[{"source": d["source"], "chunk_index": d["chunk_index"]} for d in documents],
    )

    print(f"✅ {len(documents)} chunks indexés dans la collection '{COLLECTION_NAME}'.")
    print(f"   Stockage persistant : {CHROMA_PATH}")

    # Petit récap par source
    sources = {}
    for d in documents:
        sources[d["source"]] = sources.get(d["source"], 0) + 1
    for source, count in sources.items():
        print(f"   - {source}: {count} chunks")


def add_single_document(content: str, source: str = "manual_entry"):
    """
    Permet d'ajouter un document à la volée (utilisé plus tard par l'Escalation
    Agent quand une nouvelle question/réponse validée doit enrichir la base).
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    existing_count = collection.count()
    doc_id = f"{source}_{existing_count}"

    collection.add(
        ids=[doc_id],
        documents=[content],
        metadatas=[{"source": source, "chunk_index": existing_count}],
    )
    print(f"Document ajouté avec l'id: {doc_id}")


if __name__ == "__main__":
    build_chroma_collection()

    # Petit test de query pour vérifier que ça marche
    print("\n--- Test de recherche ---")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_collection(COLLECTION_NAME, embedding_function=embedding_fn)

    results = collection.query(
        query_texts=["Combien de temps ai-je pour retourner un produit ?"],
        n_results=2,
    )
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"\n[Source: {meta['source']}]")
        print(doc[:200], "...")
