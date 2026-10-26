import json
from datetime import datetime
from pathlib import Path
from database_mock import create_fake_orders_for_customer
from backend.services.email_service import send_approval_email 


USERS_FILE = Path("data/users.json")

def load_users():
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def signup(email: str, password: str, name: str, phone: str = None) -> dict:
    users = load_users()

    if email in users:
        return {"success": False, "message": "Cet email existe déjà"}
    if phone and any(u.get("phone") == phone for u in users.values()):
        return {"success": False, "message": "Ce numéro de téléphone est déjà utilisé"}

    customer_id = f"CUST{str(len(users) + 100).zfill(3)}"
    phone_value = phone.strip() if phone and phone.strip() else "Not provided"

    users[email] = {
        "customer_id": customer_id,
        "name": name,
        "email": email,
        "phone": phone_value,
        "password": password,
        "status": "pending",
        "loyalty_tier": "bronze",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    save_users(users)
    return {
        "success": True,
        "message": "Compte créé ! En attente de validation par l'administrateur."
    }

def login(identifier: str, password: str) -> dict:
    users = load_users()
    user = users.get(identifier)
    if not user:
        user = next((u for u in users.values() if u.get("phone") == identifier), None)

    if not user or user["password"] != password:
        return {"success": False, "message": "Email, téléphone ou mot de passe incorrect"}

    if user.get("status") != "approved":
        return {"success": False, "message": "Votre compte est en attente de validation."}

    return {
        "success": True,
        "customer_id": user["customer_id"],
        "name": user["name"]
    }

def approve_user(email: str, phone: str = None) -> dict:
    users = load_users()
    if email not in users:
        return {"success": False, "message": "Utilisateur introuvable."}

    user_data = users[email]
    user_data["status"] = "approved"
    
    if phone and phone.strip():
        user_data["phone"] = phone.strip()

    create_fake_orders_for_customer(user_data["customer_id"])
    save_users(users)
    
    # Envoi de l'email
    email_result = send_approval_email(user_data["email"], user_data["name"])
    
    # Si l'email a échoué, on prévient l'admin mais on valide quand même le compte (ou on annule, selon ton choix)
    if not email_result["success"]:
        return {
            "success": True, # Le compte est approuvé dans la DB
            "email_sent": False,
            "message": f"Compte approuvé, mais l'email n'a pas pu être envoyé ({email_result['message']}). Vérifiez l'adresse email."
        }

    return {"success": True, "email_sent": True, "message": "Compte approuvé et email envoyé !"}

def reject_user(email: str):
    users = load_users()
    if email in users:
        del users[email]
        save_users(users)
        return True
    return False