#  Assistant de Support Client Intelligent

Système multi-agents orchestré avec LangGraph pour automatiser le support client
d'un site e-commerce d'électronique fictif .

## Architecture

```
Client Message
      ↓
[Agent Classifier] → intent, urgence, sentiment
      ↓
   routing selon intent
      ↓                              ↓
[Agent RAG]                  [Agent Action]
(politiques, FAQ)            (commandes, remboursements, tickets)
      ↓                              ↓
   needs_escalation ?
      ↓                              ↓
[Agent Rédacteur]            [Agent Escalation]
(réponse finale)             (résumé humain + ticket)
```

## Setup

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configurer la clé API

```bash
cp .env.example .env
# Édite .env et mets ta vraie clé ANTHROPIC_API_KEY
```

### 3. Indexer les documents dans ChromaDB

```bash
python ingest_docs_chromaDB.py
```

⚠️ Au premier lancement, ChromaDB télécharge automatiquement le modèle d'embedding
(`all-MiniLM-L6-v2`, ~80MB depuis HuggingFace). Si tu es derrière un réseau
restrictif (proxy d'entreprise) et que ça échoue, voir la note en bas de
`ingest_docs_chromaDB.py` pour utiliser Voyage AI ou OpenAI embeddings à la place.

### 4. Lancer le backend FastAPI

```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Lancer le frontend Streamlit (dans un autre terminal)

```bash
streamlit run frontend/app.py
```

## Tester chaque agent isolément

Chaque agent a un bloc `if __name__ == "__main__":` avec un test rapide :

```bash
python -m agents.classifier
python -m agents.rag_agent
python -m agents.action_agent
python -m agents.escalation_agent
python -m agents.writer_agent
python -m graph.workflow      # teste le graph complet de bout en bout
```

## Données de test (database_mock.py)

| Customer ID | Nom | Tier |
|---|---|---|
| CUST001 | Sarah Ben Ali | Gold |
| CUST002 | Karim Trabelsi | Silver |
| CUST003 | Lina Mansour | Bronze |

| Order ID | Client | Statut |
|---|---|---|
| ORD5001 | CUST001 | shipped |
| ORD5002 | CUST002 | delivered |
| ORD5003 | CUST003 | processing |

## Exemples de messages à tester

- "Où en est ma commande ORD5001 ?" → Action Agent (order_status)
- "Combien de temps ai-je pour retourner un produit ?" → RAG Agent
- "Mon casque est tombé en panne, je veux un remboursement immédiat sinon je porte plainte !" → Escalation
- "Le routeur X3 est-il compatible avec la fibre ?" → RAG Agent (product_question)

## Prochaines étapes (roadmap stage)

- [ ] Double-routing : certains intents (ex: return_refund) devraient passer par RAG **et** Action
- [ ] Mémoire conversationnelle multi-tours (utiliser `conversation_history`)
- [ ] Dataset d'évaluation (20-30 questions test) + script de scoring
- [ ] Enrichissement automatique de ChromaDB via `add_single_document()` quand une nouvelle question validée arrive
- [ ] Logging structuré (SQLite ou fichier JSON) de toutes les interactions
- [ ] Reranking des résultats RAG avec un cross-encoder