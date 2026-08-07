"""
escalation_agent.py
-------------------
Agent d'escalade humaine : résume la conversation et notifie l'humain.
"""

from graph.state import SupportState
from agents.LLM_client import call_LLM 


# 1. LE PROMPT POUR LE RÉSUMÉ
ESCALATION_SUMMARY_PROMPT = """Tu es un assistant qui prépare des résumés pour un agent humain du support client.

Voici les informations sur le client et le problème :
- ID Client : {customer_id}
- Message original : "{message}"
- Intention détectée par l'IA : {intent} (confiance : {intent_confidence}%)
- Raison de l'escalade : {escalation_reason}

Rédige un résumé TRÈS CONCIS (max 5 lignes) pour l'agent humain. 
Il doit comprendre :
1. Qui est le client.
2. Quel est le problème (en une phrase).
3. Pourquoi l'IA n'a pas pu répondre (info manquante, intention non reconnue, etc.).
4. L'urgence ressentie (d'après le message).

Écris directement le résumé, sans formule de politesse au début.
"""


def escalation_node(state: SupportState) -> SupportState:
    """
    Mission 1 : Résumer la conversation pour faire gagner du temps à l'humain.
    Mission 2 : A faire !! Notifier l'humain (ici : affichage dans la console + écriture dans un fichier log).
    """
    
    # --- Récupérer les infos du state ---
    customer_id = state.get("customer_id", "Inconnu")
    message = state.get("message", "")
    intent = state.get("intent", "non_déterminé")
    confidence = state.get("intent_confidence", 0.0) * 100  # Convertir en pourcentage
    escalation_reason = state.get("escalation_reason", "Raison non spécifiée")

    # --- MISSION 1 : Générer le résumé avec Gemini ---
    summary_prompt = ESCALATION_SUMMARY_PROMPT.format(#to replace the placeholder in promt
        customer_id=customer_id,
        message=message,
        intent=intent,
        intent_confidence=round(confidence, 1),
        escalation_reason=escalation_reason
    )
    
    # J'appelle call_LLM (pas call_LLM_json) car je veux du texte brut, pas du JSON
    summary = call_LLM(
        system_prompt="Tu es un assistant de support client.",
        user_message=summary_prompt,
        temperature=0.3  # Un peu de créativité mais pas trop
    )
    
    # Nettoyage basique (au cas où Gemini mettrait des guillemets ou astérisques)
    summary = summary.strip()

    # --- MISSION 2 : Notifier l'humain (SIMULATION) ---
    # 2a. On affiche un gros bloc coloré dans la console pour que tu voies le résumé
    print("\n" + "="*60)
    print("🚨 ESCALADE HUMAINE REQUISE 🚨")
    print("="*60)
    print(f"📋 RESUME POUR L'AGENT :\n{summary}")
    print(f"\n📌 Raison : {escalation_reason}")
    print("="*60 + "\n")

    # 2b. On écrit dans un fichier "notifications.log" (comme une boîte mail locale)
    with open("notifications.log", "a", encoding="utf-8") as f:
        f.write(f"[{customer_id}] - {escalation_reason}\n")
        f.write(f"RESUME: {summary}\n")
        f.write("-"*40 + "\n")

    # --- On retourne l'état mis à jour ---
    return {
        **state,
        "escalation_summary": summary,
        "status": "escalated",
        "needs_escalation": True,
        "final_response": None  # On ne répond pas au client car on passe la main à l'humain
    }