"""
admin/dashboard.py
------------------
Admin Dashboard - Escalated Requests + Knowledge Base + User Management
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from database_mock import get_customer
from backend.services.auth_utils import load_users, approve_user, reject_user

# ============================================================
# PATHS
# ============================================================
ESCALATIONS_FILE = Path("data/escalations.json")
DOCS_PATH = Path("data/knowledge_docs")
DOCS_PATH.mkdir(parents=True, exist_ok=True)

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="NovaShop Admin", page_icon="🛡️", layout="wide")

# ============================================================
# ADMIN LOGIN
# ============================================================
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

# Au début du fichier, après les imports, ajouter un état pour l'historique
if "show_history" not in st.session_state:
    st.session_state.show_history = {}  # dict {request_id: bool}


if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# GESTION DE LA CONFIRMATION D'APPROBATION (SESSION STATE)
if 'confirm_approval_email' not in st.session_state:
    st.session_state.confirm_approval_email = None
if 'confirm_approval_msg' not in st.session_state:
    st.session_state.confirm_approval_msg = ""

if not st.session_state.admin_logged_in:
    st.title("🛡️ NovaShop - Admin Login")
    with st.form("admin_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect credentials")
    st.stop()


# ============================================================
# HELPERS
# ============================================================
def load_escalations():
    if not ESCALATIONS_FILE.exists():
        return []
    with open(ESCALATIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def mark_as_handled(request_id: str):
    escalations = load_escalations()
    for req in escalations:
        if req["id"] == request_id:
            req["status"] = "handled"
            req["handled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    with open(ESCALATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(escalations, f, indent=2, ensure_ascii=False)

def delete_request(request_id: str):
    """Supprime une demande du fichier escalations.json."""
    escalations = load_escalations()
    escalations = [req for req in escalations if req["id"] != request_id]
    with open(ESCALATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(escalations, f, indent=2, ensure_ascii=False)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
st.sidebar.title("🛡️ Admin Panel")
page = st.sidebar.radio("Navigation", [
    "Escalated Requests",
    "User Management",
    "Knowledge Base"
])

if st.sidebar.button("Logout"):
    st.session_state.admin_logged_in = False
    st.rerun()

# ============================================================
# PAGE 1 : ESCALATED REQUESTS
# ============================================================
if page == "Escalated Requests":
    st.title("📨 Escalated Requests")
    
    escalations = load_escalations()
    
    col1, col2, col3 = st.columns(3)
    pending = [e for e in escalations if e.get("status") == "pending"]
    handled = [e for e in escalations if e.get("status") == "handled"]
    
    col1.metric("Total", len(escalations))
    col2.metric("Pending", len(pending))
    col3.metric("Handled", len(handled))
    
    status_filter = st.selectbox("Filter", ["All", "pending", "handled"])
    
    filtered = escalations if status_filter == "All" else [e for e in escalations if e.get("status") == status_filter]
    
    if not filtered:
        st.info("No escalated requests.")
    else:
        for idx, req in enumerate(reversed(filtered)):
            with st.expander(f"**{req['id']}** — {req.get('created_at')} — {req.get('status', '').upper()}"):
                col_a, col_b = st.columns([2, 1])

                with col_a:
                    st.write("**Message:**")
                    st.info(req.get("message", "—"))
                    if req.get("summary"):
                        st.write("**Summary:**")
                        st.success(req["summary"])
                    st.write("**Reason:**", req.get("reason", "—"))

                with col_b:
                    st.write("**Customer ID:**", req.get("customer_id"))
                    client = get_customer(req.get("customer_id"))
                    if client:
                        st.write("**Name:**", client.get("name"))
                        st.write("**Email:**", client.get("email"))
                        st.write("**Phone:**", client.get("phone", "Not provided"))
                    st.write("**Created:**", req.get("created_at"))

                # Historique complet
                history = req.get("conversation_history", [])
                if history:
                    with st.expander("💬 Voir l'historique complet de la conversation"):
                        for turn in history:
                            role = turn.get("role", "unknown")
                            content = turn.get("content", "")
                            emoji = "👤" if role == "user" else "🤖"
                            st.write(f"{emoji} **{role}:** {content}")
                else:
                    st.caption("Aucun historique disponible pour cette demande.")

                # Actions avec clés uniques (idx ajouté)
                col_actions = st.columns([1, 1])
                with col_actions[0]:
                    if req.get("status") == "pending":
                        if st.button("✅ Mark as handled", key=f"handle_{req['id']}_{idx}"):
                            mark_as_handled(req["id"])
                            st.rerun()
                with col_actions[1]:
                    if st.button("🗑️ Delete request", key=f"delete_{req['id']}_{idx}"):
                        delete_request(req["id"])
                        st.success(f"Demande {req['id']} supprimée.")
                        st.rerun()
# ============================================================
# PAGE 2 : USER MANAGEMENT
# ============================================================

 
elif page == "User Management":
    st.title("👥 User Management")
    # Si une approbation nécessite une confirmation, on l'affiche en haut
    if st.session_state.confirm_approval_email:
        st.warning(f"🚨 **Attention pour l'utilisateur {st.session_state.confirm_approval_email} :** {st.session_state.confirm_approval_msg}")
        st.info("️ Le compte a été marqué comme approuvé en base, mais l'email a échoué. Que souhaitez-vous faire ?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmer l'approbation", key="btn_confirm_yes"):
                # L'admin accepte le risque, on garde le compte approuvé
                st.session_state.confirm_approval_email = None
                st.session_state.confirm_approval_msg = ""
                st.toast("Approbation confirmée par l'admin.", icon="✅")
                st.rerun()
                
        with col2:
            if st.button("❌ Annuler (Rejeter le compte)", key="btn_confirm_no"):
                # L'admin annule : on remet le compte en "pending" ou on le supprime
                #from auth.auth_utils import reject_user # Assure-toi que c'est bien importé
                reject_user(st.session_state.confirm_approval_email)
                
                st.session_state.confirm_approval_email = None
                st.session_state.confirm_approval_msg = ""
                st.toast("Compte annulé et rejeté.", icon="❌")
                st.rerun()
                
        st.divider() # Une ligne de séparation visuelle
   
    users = load_users()
    
    pending_users = {email: u for email, u in users.items() if u.get("status") == "pending"}
    approved_users = {email: u for email, u in users.items() if u.get("status") == "approved"}
    
    st.subheader(f"⏳ Pending Accounts ({len(pending_users)})")
    
    if not pending_users:
        st.info("No pending users.")
    else:
        for email, user in pending_users.items():
            with st.expander(f"{user['name']} — {email}"):
                st.write("**Customer ID:**", user["customer_id"])
                st.write("**Created at:**", user.get("created_at"))
                
                col1, col2 = st.columns(2)
                with col1:
                    # Dans ta boucle qui affiche les utilisateurs en attente (dashboard.py)

                    if st.button("✅ Approve", key=f"app_{email}"):
                        # Appel à ton endpoint backend ou fonction directe
                        result = approve_user(email) 
                        
                        if result["success"]:
                            if result.get("email_sent"):
                                # Cas normal : tout va bien
                                st.toast("✅ Compte approuvé et email envoyé !", icon="✅")
                                st.rerun()
                            else:
                                # CAS D'ERREUR EMAIL : On sauvegarde l'état pour l'afficher en haut
                                st.session_state.confirm_approval_email = email
                                st.session_state.confirm_approval_msg = result['message']
                                
                                # On force le rechargement pour que le bloc en haut (étape 1) s'affiche
                                st.rerun() 
                        else:
                            st.error(f"❌ Erreur critique : {result['message']}")
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"rej_{email}"):
                        reject_user(email)
                        st.warning(f"{user['name']} rejected.")
                        st.rerun()
    
    st.divider()
    st.subheader(f"✅ Approved Accounts ({len(approved_users)})")
    
    for email, user in approved_users.items():
        st.write(f"**{user['name']}** — `{email}` — `{user['customer_id']}`")

# ============================================================
# PAGE 3 : KNOWLEDGE BASE
# ============================================================
elif page == "Knowledge Base":
    st.title("📚 Knowledge Base")
    
    uploaded_file = st.file_uploader("Upload PDF / Markdown / TXT", type=["pdf", "md", "txt"])
    
    if uploaded_file is not None:
        file_path = DOCS_PATH / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File **{uploaded_file.name}** saved.")
        
        if st.button("➕ Add to Knowledge Base", type="primary"):
            with st.spinner("Indexing..."):
                try:
                    from ingest_docs_chromaDB import add_document_to_chroma
                    nb = add_document_to_chroma(str(file_path))
                    st.success(f"✅ Added {nb} chunks")
                except Exception as e:
                    st.error(str(e))
    
    st.subheader("Current Documents")
    docs = list(DOCS_PATH.glob("*"))
    
    if not docs:
        st.info("No documents yet.")
    else:
        for doc in docs:
            col1, col2 = st.columns([5, 1])
            with col1:
                #  Lecture du contenu pour le téléchargement
                with open(doc, "rb") as f:
                    file_bytes = f.read()
                # Bouton de téléchargement 
                st.download_button(
                    label=f"📄 {doc.name}",
                    data=file_bytes,
                    file_name=doc.name,
                    key=f"download_{doc.name}"
                )
            with col2:
                if st.button("🗑️", key=f"del_{doc.name}"):
                    try:
                        from ingest_docs_chromaDB import delete_document_from_chroma
                        delete_document_from_chroma(doc.name)
                        doc.unlink()
                        st.success("Deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))