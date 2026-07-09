"""
rag_agent.py
------------
Agent RAG : interroge ChromaDB avec un seuil de distance.
Si le meilleur document est trop éloigné -> escalade.
"""

import chromadb
from chromadb.utils import embedding_functions
from graph.state import SupportState

# === CONSTANTES ===
CHROMA_PATH = "./chroma_data"
COLLECTION_NAME = "techmarket_docs"

# Seuil de distanc : en dessous = pertinent, au-dessus = escalade
DISTANCE_THRESHOLD = 0.5  # on peut ajuster (0.5 = strict, 0.8 = permissif)

# === Connexion à Chroma ===
client = chromadb.PersistentClient(path=CHROMA_PATH)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

try:
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )
except Exception as e:
    raise RuntimeError(
        f"Collection '{COLLECTION_NAME}' introuvable dans {CHROMA_PATH}.\n"
        "Lance d'abord : python ingest_docs_chromaDB.py"
    ) from e


def rag_node(state: SupportState) -> SupportState:
    query = state.get("message", "")

    if not query:
        return {
            **state,
            "rag_success": False,
            "rag_answer": None,
            "needs_escalation": True,
            "escalation_reason": "empty_query",
        }

    # Interroger Chroma (on prend le 1er résultat)
    results = collection.query(
        query_texts=[query],
        n_results=1
    )

    # Vérifier si un document a été trouvé
    if not results['documents'] or not results['documents'][0]:
        return {
            **state,
            "rag_success": False,
            "rag_answer": None,
            "needs_escalation": True,
            "escalation_reason": "no_docs_found",
        }

    # --- RÉCUPÉRER LE DOCUMENT ET SA DISTANCE ---
    best_doc = results['documents'][0][0]
    best_distance = results['distances'][0][0]  # LA DISTANCE 

    # Vérifier si la distance est acceptable
    if best_distance > DISTANCE_THRESHOLD:
        # Le document trouvé est trop éloigné de la question
        return {
            **state,
            "rag_success": False,
            "rag_answer": best_doc,  # On garde quand même pour info
            "needs_escalation": True,
            "escalation_reason": f"low_relevance_distance_{best_distance:.2f}",
        }

    # Succès : la distance est bonne
    return {
        **state,
        "rag_success": True,
        "rag_answer": best_doc,
        "needs_escalation": False,
        "status": "processing",
        # On peut stocker la distance pour le debug
        "rag_distance": best_distance,
    }


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    test_questions = [
        #"Combien de temps ai-je pour retourner un produit ?",
        #"Comment suivre ma commande ?",
        #"Quelle est la couleur du ciel ?", # Question hors sujet -> escalade
        "Je veux parler à un humain",
        "Est-ce que l'iPhone 15 est compatible avec la 5G en France",
        "Je veux parler à un conseiller"

    ]

    for q in test_questions:
        print("=" * 50)
        print(f"❓ {q}")
        state = {
            "customer_id": "TEST",
            "message": q,
            "conversation_history": [],
        }
        result = rag_node(state)
        print(f"📄 Réponse trouvée : {result.get('rag_answer', 'AUCUNE')}")
        print(f"📏 Distance : {result.get('rag_distance', 'N/A'):.3f}" if result.get('rag_distance') else "📏 Distance: N/A")
        print(f"🚨 Escalade ? {result.get('needs_escalation')}")
        print(f"📌 Raison : {result.get('escalation_reason', 'OK')}")