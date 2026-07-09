

"""
writer_agent.py
----------------
Agent Rédacteur : formule la réponse finale envoyée au client.
"""

from agents.LLM_client import call_LLM
from graph.state import SupportState


WRITER_SYSTEM_PROMPT = """Tu es l'agent de support client final de TechMarket, un site e-commerce
d'électronique. Ton rôle : transformer des informations brutes (résultat de recherche documentaire
et/ou résultat d'une action système) en UNE réponse finale, claire et chaleureuse pour le client jamais robotique.

Règles importantes :
- Réponds en français, sauf si le message du client est dans une autre langue.
- Ne mentionne JAMAIS les termes techniques internes (RAG, agent, base de données, ChromaDB, etc.)
- Ne dis jamais "selon nos documents" - parle comme si tu connaissais directement l'information.
- Sois direct : réponds à la question dès la première phrase.
- Si le client semble frustré, reconnais sa gêne brièvement.
- Termine par une phrase ouverte si pertinent.
"""

def writer_node(state: SupportState) -> SupportState:
    message = state.get("message", "")
    rag_answer = state.get("rag_answer")
    action_result = state.get("action_result")

    context = [f"Question du client : \"{message}\""]

    if rag_answer:
        context.append(f"Information trouvée :\n{rag_answer}")
    if action_result:
        context.append(f"Résultat action :\n{action_result}")

    final_response = call_LLM(
        system_prompt=WRITER_SYSTEM_PROMPT,
        user_message="\n\n".join(context),
        temperature=0.6,
    )

    return {
        **state,
        "final_response": final_response.strip(),
        "status": "resolved",
    }

