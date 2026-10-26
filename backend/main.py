"""
main.py
-------
Backend FastAPI pour NovaShop Support
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Import du workflow ET du classifieur (pour le pré-check)
from graph.workflow import support_graph, ACTION_INTENTS
from agents.classifier import classify_message 

app = FastAPI(title="NovaShop Support Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SCHEMAS
# ============================================================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    customer_id: str
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    final_response: str
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    status: Optional[str] = None
    needs_escalation: Optional[bool] = False
    escalation_reason: Optional[str] = None
    action_result: Optional[dict] = None
    rag_answer: Optional[str] = None
    action_type: Optional[str] = None
    login_required: Optional[bool] = False


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def health_check():
    return {"status": "ok", "service": "NovaShop Support Agent API"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        # --- STEP 1: Pre-check for action intents---
        # Run only the classifier to see if login is required upfront
        classifier_state = {"message": request.message, "conversation_history": []}
        classifier_result = classify_message(classifier_state)
        intent = classifier_result.get("intent")
        confidence = classifier_result.get("intent_confidence")

        if request.customer_id == "anonymous" and intent in ACTION_INTENTS:
            return ChatResponse(
                final_response="Pour accéder à vos commandes ou remboursements, veuillez vous connecter. 🔐",
                intent=intent,
                intent_confidence=confidence,
                login_required=True,
                needs_escalation=False,
                status="pending_login",
            )

        # --- STEP 2: Run the full graph ---
        initial_state = {
            "customer_id": request.customer_id,
            "message": request.message,
            "conversation_history": [m.dict() for m in (request.conversation_history or [])],
        }

        result = support_graph.invoke(initial_state)

        # --- STEP 3: Handle anonymous escalation ---
        if request.customer_id == "anonymous" and result.get("needs_escalation"):
            return ChatResponse(
                final_response="Pour que nous puissions vous aider plus précisément, veuillez vous connecter ou créer un compte.",
                intent=result.get("intent"),
                intent_confidence=result.get("intent_confidence"),
                login_required=True,
                needs_escalation=False,
                status="pending_login",
            )

        # --- STEP 4: Normal response ---
        final_response = result.get("final_response")
        if not final_response:
            if result.get("needs_escalation"):
                final_response = "Nous allons vous appeler bientôt. Un conseiller humain prendra contact avec vous sous peu."
            else:
                final_response = "Désolé, je n'ai pas pu traiter votre demande pour le moment."

        return ChatResponse(
            final_response=final_response,
            intent=result.get("intent"),
            intent_confidence=result.get("intent_confidence"),
            status=result.get("status"),
            needs_escalation=result.get("needs_escalation", False),
            escalation_reason=result.get("escalation_reason"),
            action_result=result.get("action_result"),
            rag_answer=result.get("rag_answer"),
            action_type=result.get("action_type"),
            login_required=False,
        )

    except Exception as e:
        print("❌ ERROR in LangGraph:", str(e))
        import traceback
        traceback.print_exc()

        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "resourceexhausted" in error_str:
            friendly_message = "Le serveur est momentanément très sollicité 🙏 Merci de réessayer dans une minute."
        else:
            friendly_message = "Une erreur est survenue lors du traitement. Merci de réessayer."

        return ChatResponse(
            final_response=friendly_message,
            needs_escalation=False,
            status="error",
            login_required=False,
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)