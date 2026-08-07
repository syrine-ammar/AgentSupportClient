"""
classifier.py
--------------
Agent Classifier : détermine l'intention du client, l'urgence, et le sentiment.
C'est le PREMIER agent appelé dans le graph - il décide vers quels agents router.
"""


from agents.LLM_client import call_LLM_json
from graph.state import SupportState

CLASSIFIER_PROMPT = """Tu es un classifieur d'intentions pour le support client.

Analyse le message et retourne UNIQUEMENT un JSON avec :
{
  "intent": "order_status" | "return_refund" | "product_question" | "technical_support" | "greeting_smalltalk" | "general_inquiry" | "other",
  "confidence": nombre flottant entre 0.0 et 1.0,
  "extracted_entities": {
      "order_id": null ou chaîne de caractères,
      "product_name": null ou chaîne de caractères
  }
}

Définitions des intentions :

- order_status : demande concernant l'état d'une commande, son avancement, la livraison ou le suivi d'un colis.

- return_refund : demande concernant un retour de produit, un remboursement, une annulation de commande ou les conditions de retour.

- product_question : question concernant les caractéristiques d'un produit, son prix, sa disponibilité ou ses informations générales.

- technical_support : problème lié à l'utilisation d'un produit déjà reçu (panne, configuration, installation ou problème technique).

- greeting_smalltalk : messages de politesse, salutations, remerciements.

- general_inquiry : questions générales sur l'entreprise, les politiques, etc. (couvertes par la FAQ).

- other : tout le reste (demande de parler à un humain, spam, questions hors sujet, blagues...).
Règle pour la confiance (confidence) :

La valeur de confidence représente votre niveau de certitude concernant la classification de l'intention du message.

Utilisez les valeurs suivantes :

- 0.9 à 1.0 : cas très clair, l'intention est évidente et sans ambiguïté.
- 0.6 à 0.8 : cas partiellement ambigu ou pouvant correspondre à plusieurs intentions.
- inférieur à 0.5 : message peu clair, trop court ou impossible à classer avec certitude.

Si le message est ambigu ou trop court, utilisez une confidence inférieure à 0.7.
"""

def classify_message(state: SupportState) -> SupportState:
    message = state.get("message", "")
    result = call_LLM_json(CLASSIFIER_PROMPT, f"Message : \"{message}\"")
    
    if "_parse_error" in result:
        # En cas d'erreur, on met une intention par défaut et on escalade
        return {
            **state,
            "intent": "other",
            "intent_confidence": 0.0,
            "needs_escalation": True,
            "escalation_reason": "classifier_parse_error",
        }
    
    intent = result.get("intent", "other")
    confidence = result.get("confidence", result.get("intent_confidence", 0.5))
    entities = result.get("extracted_entities",None)#, {})
    
    # Si confiance faible, on escalade directement, 
    if intent == "other" or confidence < 0.7:
        return {
            **state,
            "intent": intent,
            "intent_confidence": confidence,
            "needs_escalation": True,
            "escalation_reason": "intent_other" if intent == "other" else "low_confidence",
            "action_result": {"extracted_entities": entities},
        }
    
    return {
        **state,
        "intent": intent,
        "intent_confidence": confidence,
        "action_result": {"extracted_entities": entities},
        "needs_escalation": False,
    }
# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    tests = [
        "Bonjour, ma commande ORD5001 devait arriver il y a 3 jours",
        "Bonjour !",
        "Merci pour votre aide",
        "Quels sont les moyens de paiement acceptés ?",
        "Mon imprimante ne fonctionne plus",
        "Je veux parler à un humain",
        "Quelle est la couleur du ciel ?"
    ]
    
    for msg in tests:
        state = {"message": msg, "conversation_history": []}
        result = classify_message(state)
        print(f"Message: {msg}")
        print(f"→ Intent: {result['intent']} (conf: {result['intent_confidence']})")
        print("-" * 60)

