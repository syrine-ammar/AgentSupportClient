"""
ingest_docs_chromaDB.py
------------------------
Manages the ChromaDB knowledge base for NovaShop / TechMarket.

Features:
- Full rebuild of the collection
- Incremental add of one document (PDF / MD / TXT)
- Delete one document without touching the others
- Smart chunking (Markdown sections or classic chunking)
"""

import os
import glob
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

# ============================================================
# CONFIGURATION
# ============================================================
DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "data", "knowledge_docs")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_data")
COLLECTION_NAME = "techmarket_docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


# ============================================================
# CHUNKING FUNCTIONS
# ============================================================
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Classic chunking with overlap (for TXT and PDF)."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def chunk_by_markdown_sections(text: str) -> list[str]:
    """Smart chunking for Markdown files (split by ## headers)."""
    sections = text.split("\n## ")
    chunks = []
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        content = section if i == 0 else "## " + section
        content = content.strip()
        if len(content) >= 20:
            chunks.append(content)
    return chunks


def smart_chunk(text: str, source_name: str) -> list[str]:
    """
    Choose the best chunking strategy:
    - Markdown → split by sections
    - PDF / TXT → classic chunking
    """
    if source_name.endswith(".md") or "## " in text:
        return chunk_by_markdown_sections(text)
    return chunk_text(text)


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


# ============================================================
# LOAD DOCUMENTS (for full rebuild)
# ============================================================
def load_documents() -> list[dict]:
    """Load all supported files from the knowledge folder."""
    documents = []
    
    files = glob.glob(os.path.join(DOCS_FOLDER, "*.*"))
    supported = [".md", ".txt", ".pdf"]

    for filepath in files:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in supported:
            continue

        source_name = os.path.basename(filepath)

        try:
            if ext == ".pdf":
                text = extract_text_from_pdf(filepath)
            else:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
        except Exception as e:
            print(f"⚠️ Error reading {source_name}: {e}")
            continue

        chunks = smart_chunk(text, source_name)

        for idx, chunk in enumerate(chunks):
            documents.append({
                "id": f"{source_name}_{idx}",
                "content": chunk,
                "source": source_name,
                "chunk_index": idx,
            })

    return documents


# ============================================================
# FULL REBUILD
# ============================================================
def build_chroma_collection():
    """Delete and recreate the entire collection (full rebuild)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' deleted.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"description": "TechMarket support knowledge base"},
    )

    documents = load_documents()

    if not documents:
        print("No documents to index.")
        return

    collection.add(
        ids=[d["id"] for d in documents],
        documents=[d["content"] for d in documents],
        metadatas=[{"source": d["source"], "chunk_index": d["chunk_index"]} for d in documents],
    )

    print(f"✅ {len(documents)} chunks indexed in '{COLLECTION_NAME}'.")
    
    # Summary per source
    sources = {}
    for d in documents:
        sources[d["source"]] = sources.get(d["source"], 0) + 1
    for source, count in sources.items():
        print(f"   - {source}: {count} chunks")


# ============================================================
# INCREMENTAL ADD (one file)
# ============================================================
def add_document_to_chroma(filepath: str) -> int:
    """
    Add only one document (PDF / MD / TXT) to the existing collection.
    Does NOT delete previous documents.
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    source_name = os.path.basename(filepath)

    # Extract text
    if source_name.lower().endswith(".pdf"):
        text = extract_text_from_pdf(filepath)
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

    chunks = smart_chunk(text, source_name)

    if not chunks:
        print(f"No content found in {source_name}")
        return 0

    ids = [f"{source_name}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
    )

    print(f"✅ Added {len(chunks)} chunks from '{source_name}'")
    return len(chunks)


# ============================================================
# ADD SHORT TEXT (for future use)
# ============================================================
def add_single_document(content: str, source: str = "manual_entry"):
    """Add a short piece of text (useful later for validated answers)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
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
    print(f"Document added with id: {doc_id}")


# ============================================================
# DELETE ONE DOCUMENT
# ============================================================
def delete_document_from_chroma(source_name: str) -> int:
    """Delete all chunks belonging to one document."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
    except Exception:
        print(f"Collection '{COLLECTION_NAME}' does not exist.")
        return 0

    results = collection.get(where={"source": source_name})
    ids_to_delete = results["ids"]

    if not ids_to_delete:
        print(f"No chunks found for '{source_name}'")
        return 0

    collection.delete(ids=ids_to_delete)
    print(f"🗑️ Deleted {len(ids_to_delete)} chunks from '{source_name}'")
    return len(ids_to_delete)


# ============================================================
# MAIN (for testing)
# ============================================================
if __name__ == "__main__":
    build_chroma_collection()

    print("\n--- Test de recherche ---")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_collection(COLLECTION_NAME, embedding_function=embedding_fn)

    results = collection.query(
        query_texts=["Combien de temps ai-je pour retourner un produit ?"],
        n_results=2,
    )
    
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"\n[Source: {meta['source']}]")
        print(doc[:200], "...")