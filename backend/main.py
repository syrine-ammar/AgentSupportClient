"""
main.py
-------
Backend FastAPI pour NovaShop Support
"""
from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Import du workflow ET du classifieur (pour le pré-check)
from graph.workflow import support_graph, ACTION_INTENTS
from agents.classifier import classify_message 

from backend.services.security import decode_token

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
# DÉPENDANCE DE SÉCURITÉ (JWT)
# ============================================================

def get_current_user_optional(authorization: Optional[str] = Header(None)):
    """
    Extrait et valide le token JWT de manière optionnelle.
    Retourne le payload (ex: {"sub": "email", "customer_id": "CUST123"}) 
    ou None si pas de token ou token invalide (mode anonyme).
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        return None # Token invalide ou expiré -> traité comme anonyme
    
    return payload


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def health_check():
    return {"status": "ok", "service": "NovaShop Support Agent API"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: dict = Depends(get_current_user_optional)):
    try:
        # ---JWT : Déterminer l'identité réelle ---
        effective_customer_id = current_user["customer_id"] if current_user else request.customer_id

        # --- STEP 1: Pre-check for action intents ---
        classifier_state = {"message": request.message, "conversation_history": []}
        classifier_result = classify_message(classifier_state)
        intent = classifier_result.get("intent")
        confidence = classifier_result.get("intent_confidence")

        # Utiliser effective_customer_id au lieu de request.customer_id
        if effective_customer_id == "anonymous" and intent in ACTION_INTENTS:
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
            "customer_id": effective_customer_id, # --- MODIFICATION JWT ---
            "message": request.message,
            "conversation_history": [m.dict() for m in (request.conversation_history or [])],
        }

        result = support_graph.invoke(initial_state)

        # --- STEP 3: Handle anonymous escalation ---

        if effective_customer_id == "anonymous" and result.get("needs_escalation"):
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


    ##################### testing sign up and login endpoints
from backend.services.security import hash_password, create_access_token, decode_token
from backend.services.auth_utils import signup as auth_signup, login as auth_login, load_users

# ============================================================
# SCHEMAS POUR L'AUTHENTIFICATION
# ============================================================

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    identifier: str # Email ou téléphone
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    customer_id: Optional[str] = None
    name: Optional[str] = None

# ============================================================
# ROUTES D'AUTHENTIFICATION
# ============================================================

@app.post("/signup", response_model=AuthResponse)
def api_signup(request: SignupRequest):
    """Inscription d'un nouvel utilisateur."""
    result = auth_signup(request.email, request.password, request.name, request.phone)
    return AuthResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
    )

@app.post("/login", response_model=AuthResponse)
def api_login(request: LoginRequest):
    """Connexion et génération du token JWT."""
    result = auth_login(request.identifier, request.password)
    
    if not result.get("success"):
        return AuthResponse(success=False, message=result.get("message", "Échec de connexion"))

    # Génération du JWT si le login est réussi
    token = create_access_token(data={
        "sub": request.identifier, 
        "customer_id": result["customer_id"]
    })

    return AuthResponse(
        success=True,
        message="Connexion réussie",
        access_token=token,
        customer_id=result["customer_id"],
        name=result["name"]
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)