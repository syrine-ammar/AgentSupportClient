"""
escalation_agent.py
-------------------
Agent d'escalade humaine.
- Génère un résumé pour l'humain
- Sauvegarde la demande + l'historique complet dans escalations.json
- Le dashboard affichera ensuite ces demandes avec tout le contexte
"""

import json
from datetime import datetime
from pathlib import Path
from graph.state import SupportState
from agents.LLM_client import call_LLM

ESCALATIONS_FILE = Path("data/escalations.json")

ESCALATION_SUMMARY_PROMPT = """Tu es un assistant qui prépare des résumés pour un agent humain du support client.
Voici les informations :
- ID Client : {customer_id}
- Message original : "{message}"
- Intention détectée : {intent} (confiance : {intent_confidence}%)
- Raison de l'escalade : {escalation_reason}

Rédige un résumé TRÈS CONCIS (max 4-5 lignes) pour l'agent humain.
Il doit comprendre :
1. Qui est le client
2. Quel est le problème
3. Pourquoi l'IA n'a pas pu répondre
4. Le niveau d'urgence

Écris directement le résumé, sans formule de politesse.
"""

def escalation_node(state: SupportState) -> SupportState:
    customer_id = state.get("customer_id", "anonymous")
    # Si le client est anonyme, on ne peut pas traiter la demande (cas failed RAG)
    if customer_id == "anonymous":
        return {
            **state,
            "escalation_summary": None,
            "status": "pending_login",
            "final_response": "Veuillez vous identifier pour que nous puissions traiter votre demande.",
        }

    message = state.get("message", "")
    intent = state.get("intent", "other")
    confidence = state.get("intent_confidence", 0.0) * 100
    reason = state.get("escalation_reason", "unknown")
    conversation_history = state.get("conversation_history", []) 

    # 1. Générer le résumé
    prompt = ESCALATION_SUMMARY_PROMPT.format(
        customer_id=customer_id,
        message=message,
        intent=intent,
        intent_confidence=round(confidence, 1),
        escalation_reason=reason
    )

    summary = call_LLM(
        system_prompt="Tu es un assistant de support client.",
        user_message=prompt,
        temperature=0.3
    ).strip()

    # 2. Sauvegarder dans escalations.json (avec historique complet)
    if not ESCALATIONS_FILE.exists():
        ESCALATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ESCALATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(ESCALATIONS_FILE, "r", encoding="utf-8") as f:
        escalations = json.load(f)

    new_request = {
        "id": f"REQ-{len(escalations)+1:04d}",
        "customer_id": customer_id,
        "message": message,
        "reason": reason,
        "intent": intent,
        "summary": summary,
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "handled_at": None,
        "conversation_history": conversation_history  # Ajout de l'historique complet
    }

    escalations.append(new_request)

    with open(ESCALATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(escalations, f, indent=2, ensure_ascii=False)

    # 3. Affichage dans la console (debug)
    print("\n" + "="*60)
    print("🚨 ESCALADE HUMAINE REQUISE")
    print("="*60)
    print(f"Client     : {customer_id}")
    print(f"Raison     : {reason}")
    print(f"Résumé     :\n{summary}")
    print("Historique complet :")
    for turn in conversation_history:
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        print(f"  {role}: {content}")
    print("="*60 + "\n")

    return {
        **state,
        "escalation_summary": summary,
        "status": "escalated",
        "needs_escalation": True,
        "final_response": "Nous allons vous appeler bientôt. Un conseiller humain prendra contact avec vous sous peu."
    }