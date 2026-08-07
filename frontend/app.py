"""
app.py
------
Interface Streamlit premium type chat, qui appelle le backend FastAPI.
Inclut des styles CSS sur-mesure pour répliquer le design NovaShop Support.
"""

import re
import requests
import streamlit as st
import os

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000"
)

# Configuration de la page
st.set_page_config(page_title="NovaShop Support", page_icon="🛍️", layout="centered")

# --- Injection CSS pour le style Premium ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@400;600;700;800&display=swap');

/* Main app background with radial gradients and neon glow */
[data-testid="stAppViewContainer"] {
    background-color: #0a071f !important;
    background-image: 
        radial-gradient(at 20% 30%, rgba(139, 92, 246, 0.18) 0px, transparent 50%),
        radial-gradient(at 80% 70%, rgba(236, 72, 153, 0.12) 0px, transparent 55%),
        radial-gradient(at 50% 20%, rgba(59, 130, 246, 0.08) 0px, transparent 65%) !important;
    background-attachment: fixed !important;
    font-family: 'Inter', sans-serif !important;
    color: #e2e8f0 !important;
}

/* Hide standard Streamlit header and footer */
#MainMenu {
    visibility: hidden;
}
[data-testid="stHeader"] {
    background-color: transparent !important;
}
footer {
    visibility: hidden;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: rgba(10, 8, 28, 0.95) !important;
    border-right: 1px solid rgba(124, 58, 237, 0.15) !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #a78bfa !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Custom Header layout */
.header-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-bottom: 2rem;
    padding-top: 1rem;
}
.header-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.8rem;
    font-weight: 800;
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    line-height: 1.2;
}
.title-novashop {
    background: linear-gradient(90deg, #c026d3 0%, #7c3aed 50%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.title-support {
    background: linear-gradient(90deg, #f97316 0%, #fbbf24 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.status-container {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 0.5rem;
}
.status-dot {
    width: 12px;
    height: 12px;
    background-color: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10b981, 0 0 20px #10b981;
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.status-text {
    color: #9ca3af;
    font-size: 0.95rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
}

/* Chat History Layout */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 1rem 0;
    margin-bottom: 1.5rem;
    overflow-y: auto;
}
.chat-message-row {
    display: flex;
    width: 100%;
    align-items: flex-start;
    animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.row-user {
    justify-content: flex-end;
}
.row-assistant {
    justify-content: flex-start;
}

.message-bubble {
    max-width: 70%;
    padding: 0.9rem 1.25rem;
    color: #ffffff;
    font-size: 0.95rem;
    line-height: 1.5;
    font-family: 'Inter', sans-serif;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}
.bubble-user {
    background-color: rgba(22, 17, 51, 0.6);
    border: 1px solid rgba(124, 58, 237, 0.25);
    border-radius: 20px 20px 4px 20px;
    margin-right: 12px;
}
.bubble-assistant {
    background-color: rgba(13, 10, 33, 0.6);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 20px 20px 20px 4px;
    margin-left: 12px;
}

.avatar-container {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}
.avatar-user {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
}
.avatar-assistant {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}
.avatar-icon {
    width: 20px;
    height: 20px;
    fill: #ffffff;
}

/* Typing Indicator */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 4px;
}
.typing-indicator span {
    width: 6px;
    height: 6px;
    background-color: #3b82f6;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1.0); }
}

/* Action Chips Wrapper */
.chips-outer-container {
    margin-top: 10px;
    margin-bottom: 25px;
}

/* styling buttons inside st-key-chips container */
.st-key-chips button {
    background-color: rgba(13, 10, 33, 0.45) !important;
    color: #e2e8f0 !important;
    border-radius: 20px !important;
    padding: 0.5rem 1.25rem !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: all 0.25s ease !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    width: 100% !important;
}

.st-key-chips button:hover {
    color: #ffffff !important;
    transform: translateY(-2px) !important;
}

/* Custom individual chip glow colors */
.st-key-chip_track button {
    border: 1px solid rgba(168, 85, 247, 0.35) !important; /* purple */
}
.st-key-chip_track button:hover {
    border-color: rgba(168, 85, 247, 0.8) !important;
    box-shadow: 0 0 15px rgba(168, 85, 247, 0.25) !important;
    background-color: rgba(168, 85, 247, 0.08) !important;
}

.st-key-chip_rec button {
    border: 1px solid rgba(59, 130, 246, 0.35) !important; /* blue */
}
.st-key-chip_rec button:hover {
    border-color: rgba(59, 130, 246, 0.8) !important;
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.25) !important;
    background-color: rgba(59, 130, 246, 0.08) !important;
}

.st-key-chip_return button {
    border: 1px solid rgba(99, 102, 241, 0.35) !important; /* indigo */
}
.st-key-chip_return button:hover {
    border-color: rgba(99, 102, 241, 0.8) !important;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.25) !important;
    background-color: rgba(99, 102, 241, 0.08) !important;
}

/* Chat Input custom styles */
[data-testid="stChatInput"] {
    background-color: rgba(15, 12, 38, 0.65) !important;
    border: 1px solid rgba(124, 58, 237, 0.25) !important;
    border-radius: 24px !important;
    backdrop-filter: blur(16px) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
    padding: 6px 12px !important;
    margin-bottom: 5px !important;
}

[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    background-color: transparent !important;
    border: none !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    caret-color: #7c3aed !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(156, 163, 175, 0.55) !important;
}

[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
    border-radius: 50% !important;
    border: none !important;
    width: 40px !important;
    height: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 10px rgba(124, 58, 237, 0.3) !important;
}

[data-testid="stChatInput"] button:hover {
    transform: scale(1.08) rotate(-10deg) !important;
    box-shadow: 0 6px 15px rgba(124, 58, 237, 0.5) !important;
}

[data-testid="stChatInput"] button svg {
    fill: #ffffff !important;
    stroke: #ffffff !important;
}

/* Glassmorphic debug expander */
.stExpander {
    background-color: rgba(15, 12, 38, 0.4) !important;
    border: 1px solid rgba(124, 58, 237, 0.15) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(10px) !important;
    margin-top: 1.5rem !important;
}
.stExpander summary {
    font-family: 'Outfit', sans-serif !important;
    color: #a78bfa !important;
    font-weight: 600 !important;
}
.stExpander div[data-animated="true"] {
    background-color: transparent !important;
}

.disclaimer-text {
    text-align: center;
    color: rgba(156, 163, 175, 0.45);
    font-size: 0.75rem;
    margin-top: 10px;
    margin-bottom: 20px;
    font-family: 'Inter', sans-serif;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# --- Initialisation de l'historique et de l'état ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "temp_input" not in st.session_state:
    st.session_state.temp_input = None
if "last_debug_data" not in st.session_state:
    st.session_state.last_debug_data = None

# --- Sélection du client (simule une connexion dans le Sidebar) ---
with st.sidebar:
    st.header("Session client")
    customer_id = st.selectbox(
        "Client connecté",
        options=["CUST001", "CUST002", "CUST003"],
        format_func=lambda cid: {
            "CUST001": "CUST001 — Sarah Ben Ali (Gold)",
            "CUST002": "CUST002 — Karim Trabelsi (Silver)",
            "CUST003": "CUST003 — Lina Mansour (Bronze)",
        }[cid],
    )

    st.divider()
    show_debug = st.checkbox("Afficher le panneau debug", value=True)

    if st.button("🔄 Réinitialiser la conversation"):
        st.session_state.messages = []
        st.session_state.last_debug_data = None
        st.session_state.temp_input = None
        st.rerun()#rerun the script 

# --- En-tête de l'application ---
st.markdown("""
<div class="header-container">
    <h1 class="header-title">
        🛍️ <span class="title-novashop">NovaShop</span> <span class="title-support">Support</span>
    </h1>
    <div class="status-container">
        <div class="status-dot"></div>
        <div class="status-text">Aria is online • average reply time < 1s</div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- Fonction de rendu des messages HTML ---
def render_chat(messages, show_typing=False):
    chat_html = '<div class="chat-wrapper">'

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        formatted = content.replace('\n', '<br>')
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
        formatted = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted)

        if role == "user":
            chat_html += (
                '<div class="chat-message-row row-user">'
                f'<div class="message-bubble bubble-user">{formatted}</div>'
                '<div class="avatar-container avatar-user">'
                '<svg class="avatar-icon" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
                '</div>'
                '</div>'
            )
        else:
            chat_html += (
                '<div class="chat-message-row row-assistant">'
                '<div class="avatar-container avatar-assistant">'
                '<svg class="avatar-icon" viewBox="0 0 24 24"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.38-1 1.72V7h3a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3V5.72c-.6-.34-1-0.98-1-1.72a2 2 0 0 1 2-2M7.5 13A1.5 1.5 0 0 0 6 14.5A1.5 1.5 0 0 0 7.5 16A1.5 1.5 0 0 0 9 14.5A1.5 1.5 0 0 0 7.5 13m9 0a1.5 1.5 0 0 0-1.5 1.5a1.5 1.5 0 0 0 1.5 1.5a1.5 1.5 0 0 0 1.5-1.5a1.5 1.5 0 0 0-1.5-1.5M10 9v2h4V9h-4z"/></svg>'
                '</div>'
                f'<div class="message-bubble bubble-assistant">{formatted}</div>'
                '</div>'
            )

    if show_typing:
        chat_html += (
            '<div class="chat-message-row row-assistant">'
            '<div class="avatar-container avatar-assistant">'
            '<svg class="avatar-icon" viewBox="0 0 24 24"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.38-1 1.72V7h3a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3V5.72c-.6-.34-1-0.98-1-1.72a2 2 0 0 1 2-2M7.5 13A1.5 1.5 0 0 0 6 14.5A1.5 1.5 0 0 0 7.5 16A1.5 1.5 0 0 0 9 14.5A1.5 1.5 0 0 0 7.5 13m9 0a1.5 1.5 0 0 0-1.5 1.5a1.5 1.5 0 0 0 1.5 1.5a1.5 1.5 0 0 0 1.5-1.5a1.5 1.5 0 0 0-1.5-1.5M10 9v2h4V9h-4z"/></svg>'
            '</div>'
            '<div class="message-bubble bubble-assistant">'
            '<div class="typing-indicator"><span></span><span></span><span></span></div>'
            '</div>'
            '</div>'
        )

    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
# --- Affichage de l'historique ---
chat_container = st.empty()
with chat_container:
    render_chat(st.session_state.messages, show_typing=False)

# --- Saisie utilisateur classique ---
user_input = st.chat_input("Ask Aria anything...")

# --- Gestion des entrées ---
input_to_process = None

if user_input:
    input_to_process = user_input
elif st.session_state.temp_input:
    input_to_process = st.session_state.temp_input
    st.session_state.temp_input = None  # Reset


# Action si un message est soumis
if input_to_process:
    # 1. Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": input_to_process})
    
    # 2. Afficher avec indicateur de typing
    with chat_container:
        render_chat(st.session_state.messages, show_typing=True)
    
    # 3. Appel backend
    try:
        # Préparer l'historique
        history_for_backend = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.messages[:-1]
        ]

        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "customer_id": customer_id,
                "message": input_to_process,
                "conversation_history": history_for_backend
            },
            #timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        
        final_response = data.get("final_response", "Désolé, une erreur est survenue.")
        needs_escalation = data.get("needs_escalation", False)
        
        # === LOGIQUE DEMANDÉE ===
        if needs_escalation:
            display_message = "Nous sommes désolés de ne pas pouvoir résoudre votre demande immédiatement.Un conseiller humain va vous contacter très bientôt par téléphone ou email."
        else:
            display_message = final_response
        
        # Ajouter la réponse de l'assistant
        st.session_state.messages.append({"role": "assistant", "content": display_message})
        st.session_state.last_debug_data = data
        
        st.rerun()
    except requests.exceptions.Timeout:
        st.error("⚠️ Le backend a mis trop de temps à répondre. Veuillez réessayer.")
        
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Impossible de contacter le backend. Vérifie qu'il tourne sur le port 8000.")
    except Exception as e:
        st.error(f"Erreur lors du traitement: {str(e)}")

# --- Suggestions d'actions (Chips) ---
order_ids = {
    "CUST001": "ORD5001",
    "CUST002": "ORD5002",
    "CUST003": "ORD5003"
}
order_id = order_ids.get(customer_id, "ORD5001")

st.markdown('<div class="chips-outer-container st-key-chips">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1.3, 1])

with col1:
    if st.button("📦 Track order", key="chip_track"):
        st.session_state.temp_input = f"Où en est ma commande {order_id} ?"
        st.rerun()
with col2:
    if st.button("🎧 Recommend headphones", key="chip_rec"):
        st.session_state.temp_input = "Le routeur X3 est-il compatible avec la fibre ?"
        st.rerun()
with col3:
    if st.button("↩ Return policy", key="chip_return"):
        st.session_state.temp_input = "Combien de temps ai-je pour retourner un produit ?"
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Texte informatif de bas de page
st.markdown('<div class="disclaimer-text">Aria can make mistakes. Please check important info.</div>', unsafe_allow_html=True)

# --- Panneau debug (for only developpers not production users  ) ---
if show_debug and st.session_state.last_debug_data:
    data = st.session_state.last_debug_data
    with st.expander("🔍 Détails (debug)"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Intent:**", data.get("intent"))
            st.write("**Confidence:**", data.get("intent_confidence"))
        with col2:
            st.write("**Status:**", data.get("status"))
            st.write("**Escaladé:**", data.get("needs_escalation"))
        
        if data.get("escalation_reason"):
            st.write("**Raison d'escalade:**", data.get("escalation_reason"))
        
        if data.get("action_result"):
            st.write("**Action Result:**")
            st.json(data.get("action_result"))
        
        if data.get("rag_answer"):
            st.write("**RAG Answer:**")
            st.write(data.get("rag_answer"))