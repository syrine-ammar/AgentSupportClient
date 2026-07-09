"""
workflow.py
-----------
Définit le graph LangGraph complet : assemble tous les agents et le routing
entre eux
"""

from langgraph.graph import StateGraph, END
from graph.state import SupportState
from agents.classifier import classify_message
from agents.action_agent import action_node
from agents.rag_agent import rag_node
from agents.escalation_agent import escalation_node
from agents.writer_agent import writer_node

# Définir les listes d'intentions

ACTION_INTENTS = {"order_status", "return_refund"}
RAG_INTENTS = {"product_question", "general_inquiry"}
LLM_INTENTS = {"greeting_smalltalk", "technical_support"}
ESCALATE_INTENTS = {"other"}

def route_after_classifier(state: SupportState) -> str:
    # Si escalade décidée par le classifieur (confiance faible)
    if state.get("needs_escalation"):
        return "escalation_agent"
    
    intent = state.get("intent", "other")
    if intent in ACTION_INTENTS:
        return "action_agent"
    elif intent in RAG_INTENTS:
        return "rag_agent"
    elif intent in LLM_INTENTS:
        return "writer_agent"
    else:
        # fallback
        return "escalation_agent"

def route_after_action_or_rag(state: SupportState) -> str:
    if state.get("needs_escalation"):
        return "escalation_agent"
    return "writer_agent"

def build_graph():
    graph = StateGraph(SupportState)
    
    graph.add_node("classifier", classify_message)
    graph.add_node("action_agent", action_node)
    graph.add_node("rag_agent", rag_node)
    graph.add_node("escalation_agent", escalation_node)
    graph.add_node("writer_agent", writer_node)
    
    graph.set_entry_point("classifier")
    
    graph.add_conditional_edges(
        "classifier",
        route_after_classifier,
        {
            "action_agent": "action_agent",
            "rag_agent": "rag_agent",
            "writer_agent": "writer_agent",
            "escalation_agent": "escalation_agent",
            #LangGraph uses this dictionary as a lookup table ,decide where to route based on the output of the conditional function.
        }
    )
    
    graph.add_conditional_edges(
        "action_agent",
        route_after_action_or_rag,
        {
            "escalation_agent": "escalation_agent",
            "writer_agent": "writer_agent",
        }
    )
    
    graph.add_conditional_edges(
        "rag_agent",
        route_after_action_or_rag,
        {
            "escalation_agent": "escalation_agent",
            "writer_agent": "writer_agent",
        }
    )
    
    graph.add_edge("escalation_agent", END)
    graph.add_edge("writer_agent", END)
    
    return graph.compile()

app = build_graph()

if __name__ == "__main__":
    test_inputs = [
        #{"customer_id": "CUST001", "message": "Où en est ma commande ORD5001 ?"},
        #{"customer_id": "CUST002", "message": "Je veux retourner mon produit ORD5002"},
        #{"customer_id": "CUST003", "message": "Quelle est la garantie pour un ordinateur ?"},
        {"customer_id": "CUST004", "message": "Mon imprimante ne fonctionne plus"},
        {"customer_id": "CUST005", "message": "Bonjour"},
    ]
    
    for inp in test_inputs:
        print("="*60)
        print("INPUT:", inp["message"])
        result = app.invoke(inp)
        print("INTENT:", result.get("intent"), "(conf:", result.get("intent_confidence"), ")")
        print("STATUS:", result.get("status"))
        print("FINAL:", result.get("final_response"))
        if result.get("needs_escalation"):
            print("ESCALATION REASON:", result.get("escalation_reason"))
        print()