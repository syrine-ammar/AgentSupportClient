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
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.services.auth_utils import login, signup, load_users
from database_mock import get_orders_by_customer, get_product

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
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "customer_id" not in st.session_state:
    st.session_state.customer_id = "anonymous"
if "customer_name" not in st.session_state:
    st.session_state.customer_name = None
if "force_login_required" not in st.session_state:
    st.session_state.force_login_required = False
if "waiting_for_approval" not in st.session_state:
    st.session_state.waiting_for_approval = False
if "pending_email" not in st.session_state:
    st.session_state.pending_email = None
if "pending_password" not in st.session_state:
    st.session_state.pending_password = None
if "pending_request" not in st.session_state:
    st.session_state.pending_request = None
if "auth_message" not in st.session_state:
    st.session_state.auth_message = None

# --- Sidebar ---
with st.sidebar:
    st.header("Session client")

    if st.session_state.logged_in:
        st.success(
            f"Connecté en tant que **{st.session_state.customer_name}**\n\n"
            f"ID : `{st.session_state.customer_id}`"
        )

        if st.button("Se déconnecter", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.customer_id = "anonymous"
            st.session_state.customer_name = None
            st.session_state.force_login_required = False
            st.session_state.auth_message = None
            st.session_state.waiting_for_approval = False
            st.rerun()

        # --- Order history ---
        st.divider()
        st.subheader("📦 Mes commandes")
        try:
            orders = get_orders_by_customer(st.session_state.customer_id)
            if not orders:
                st.info("Aucune commande trouvée.")
            else:
                for order in orders:
                    # Resolve product names from product IDs
                    product_ids = order.get('products', []) or []
                    product_names = []
                    for pid in product_ids:
                        p = get_product(pid)
                        if p:
                            product_names.append(p.get('name'))
                        else:
                            product_names.append(pid)

                    products_display = ", ".join(product_names) if product_names else "-"

                    with st.container():
                        st.markdown(
                            f"""
                            **{order.get('order_id')}**  
                            Produit(s) : {products_display}  
                            Coût : **{order.get('total')} €**  
                            Date : {order.get('order_date')}
                            """
                        )
                        st.divider()
        except Exception:
            st.warning("Impossible de charger les commandes.")

    else:
        st.info("Vous chattez actuellement en mode **anonyme**.\n\n"
                "La connexion sera demandée uniquement si nécessaire.")

    st.divider()
    show_debug = st.checkbox("Afficher le panneau debug", value=False)

    if st.button("🔄 Réinitialiser la conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_debug_data = None
        st.session_state.temp_input = None
        st.session_state.force_login_required = False
        st.session_state.waiting_for_approval = False
        st.session_state.pending_request = None
        st.rerun()
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


def get_user_status(email: str):
    users = load_users()
    user = users.get(email)
    return user.get("status") if user else None


def continue_pending_request():
    if not st.session_state.pending_request or not st.session_state.logged_in:
        return

    history_for_backend = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
        if msg["role"] != "assistant" or msg["content"] != "Veuillez vous connecter ou créer un compte pour poursuivre."
    ]

    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "customer_id": st.session_state.customer_id,
                "message": st.session_state.pending_request,
                "conversation_history": history_for_backend
            },
        )
        response.raise_for_status()
        data = response.json()
        final_response = data.get("final_response", "Désolé, une erreur est survenue.")
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        st.session_state.last_debug_data = data
    except Exception as e:
        st.session_state.messages.append({"role": "assistant", "content": "Erreur lors de la reprise de la conversation après validation : " + str(e)})

    st.session_state.pending_request = None
    st.session_state.waiting_for_approval = False
    st.session_state.force_login_required = False
    st.session_state.pending_email = None
    st.session_state.pending_password = None


if st.session_state.waiting_for_approval and st.session_state.pending_email:
    current_status = get_user_status(st.session_state.pending_email)
    if current_status == "approved":
        login_result = login(st.session_state.pending_email, st.session_state.pending_password)
        if login_result.get("success"):
            st.session_state.logged_in = True
            st.session_state.customer_id = login_result["customer_id"]
            st.session_state.customer_name = login_result["name"]
            continue_pending_request()


# --- Force Login / Signup Form ---
if st.session_state.force_login_required and not st.session_state.logged_in:

    st.markdown("""
    <div style="
        background: rgba(15, 12, 38, 0.7);
        border: 1px solid rgba(124, 58, 237, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        backdrop-filter: blur(12px);
    ">
        <h3 style="margin-top:0; color:#c4b5fd;">🔐 Connexion requise</h3>
        <p style="color:#9ca3af; margin-bottom: 20px;">
            Pour continuer, veuillez vous connecter ou créer un compte.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Mode selection (outside the form so it switches instantly)
    auth_mode = st.radio(
        "Choisissez une action :",
        ["Se connecter", "Créer un compte"],
        horizontal=True,
        key="auth_mode_radio"
    )

    st.write("")  # small spacer

    if auth_mode == "Se connecter":
        with st.form("login_form_inline", clear_on_submit=False):
            st.subheader("Se connecter")
            auth_identifier = st.text_input("Email ou téléphone", key="login_id")
            auth_password = st.text_input("Mot de passe", type="password", key="login_pwd")
            
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
            
            if submitted:
                result = login(auth_identifier.strip(), auth_password)
                if result.get("success"):
                    st.session_state.logged_in = True
                    st.session_state.customer_id = result["customer_id"]
                    st.session_state.customer_name = result["name"]
                    st.session_state.force_login_required = False
                    st.session_state.auth_message = "Connecté avec succès !"
                    if st.session_state.pending_request:
                        continue_pending_request()
                    st.rerun()
                else:
                    st.error(result.get("message", "Erreur de connexion"))
                    if "attente" in (result.get("message") or "").lower():
                        st.session_state.waiting_for_approval = True
                        st.session_state.pending_email = auth_identifier.strip()
                        st.session_state.pending_password = auth_password

    else:  # Créer un compte
        with st.form("signup_form_inline", clear_on_submit=False):
            st.subheader("Créer un compte")
            auth_name = st.text_input("Nom complet", key="signup_name")
            auth_email = st.text_input("Email", key="signup_email")
            auth_phone = st.text_input("Téléphone", key="signup_phone")
            auth_password = st.text_input("Mot de passe", type="password", key="signup_pwd")
            
            submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
            
            if submitted:
                # Validate inputs
                errors = []
                name_val = (auth_name or "").strip()
                email_val = (auth_email or "").strip()
                phone_val = (auth_phone or "").strip()
                pwd_val = auth_password or ""

                if not name_val:
                    errors.append("Le nom est requis.")

                # Gmail-only: must have text before @gmail.com
                if not email_val or not email_val.lower().endswith("@gmail.com") or email_val.count("@") != 1 or email_val.split("@")[0] == "":
                    errors.append("Email Gmail valide requis (ex: utilisateur@gmail.com).")

                # Phone: digits only and expected length 10
                if not phone_val.isdigit() or len(phone_val) != 8:
                    errors.append("Téléphone invalide : 8 chiffres requis, seulement des chiffres autorisés.")

                # Password length
                if len(pwd_val) < 8:
                    errors.append("Le mot de passe doit contenir au moins 8 caractères.")

                if errors:
                    st.error("\n".join(errors))
                else:
                    result = signup(
                        email_val,
                        pwd_val,
                        name_val,
                        phone_val
                    )
                    if result.get("success"):
                        st.session_state.auth_message = (
                            "✅ Compte créé avec succès !\n\n"
                            "Votre compte est en attente de validation par un administrateur. "
                            "Vous pourrez vous connecter une fois approuvé."
                        )
                        st.session_state.waiting_for_approval = True
                        st.session_state.pending_email = email_val
                        st.session_state.pending_password = pwd_val
                        st.success(st.session_state.auth_message)
                    else:
                        st.error(result.get("message", "Erreur lors de la création du compte"))

    # Waiting for approval message
    if st.session_state.waiting_for_approval:
        st.info("⏳ En attente de validation par l'administrateur...")
        if st.button("🔄 Vérifier si mon compte est approuvé"):
            st.rerun()

    # Disable the normal chat input while login is required
    user_input = None

else:
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
                "customer_id": st.session_state.customer_id,
                "message": input_to_process,
                "conversation_history": history_for_backend
            },
            #timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        
        final_response = data.get("final_response", "Désolé, une erreur est survenue.")
        needs_escalation = data.get("needs_escalation", False)
        action_triggered = bool(data.get("action_result")) or data.get("action") == "action_agent"

        login_required_by_backend = data.get("login_required", False)

        if login_required_by_backend and not st.session_state.logged_in:
            st.session_state.force_login_required = True
            st.session_state.pending_request = input_to_process
            display_message = (
                "Pour accéder à cette information, merci de vous connecter. "
                "Vos données sont sécurisées 🔐"
            )
        elif needs_escalation and st.session_state.logged_in:
            display_message = (
                "Nous sommes désolés, un conseiller humain va vous contacter "
                "très bientôt par téléphone ou email."
            )
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
st.markdown('<div class="chips-outer-container st-key-chips">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📦 Ma commande", key="chip_track"):
        # Action intent → demande de login si anonyme
        st.session_state.temp_input = "Où en est ma commande ?"
        st.rerun()

with col2:
    if st.button("📋 Politique de retour", key="chip_return"):
        # RAG intent → réponse directe depuis la FAQ
        st.session_state.temp_input = "Quelle est la politique de retour ?"
        st.rerun()

with col3:
    if st.button("💻 Garantie produit", key="chip_warranty"):
        # RAG intent → réponse directe
        st.session_state.temp_input = "Quelle est la durée de garantie ?"
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