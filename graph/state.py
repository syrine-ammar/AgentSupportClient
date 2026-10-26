"""
state.py
--------
le State partagé entre tous les agents du graph LangGraph
"""

from typing import TypedDict, Optional, List, Literal


class SupportState(TypedDict, total=False):
    """
    total=False -> tous les champs sont optionnels au départ.
    Chaque agent remplit progressivement les champs qui le concernent.
    """
     # Input
    customer_id: str
    message: str
    conversation_history: List[dict]
    
    # Classifier output
    intent: Optional[str]          # une des 7 intentions
    intent_confidence: Optional[float]    # 0-1
    
    # Action output
    action_result: Optional[dict]  # résultat de l'appel DB mock
    action_success: Optional[bool] # True si données trouvées
    
    # RAG output
    rag_answer: Optional[str]      # réponse trouvée dans Chroma
    rag_success: Optional[bool]    # True si réponse trouvée
    
    # Escalation
    needs_escalation: Optional[bool]
    escalation_reason: Optional[str]
    
    # Final response
    final_response: Optional[str]
    status: Optional[Literal["processing", "resolved", "escalated", "pending_login"]]