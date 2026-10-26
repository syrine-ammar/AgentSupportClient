# backend/services/email_service.py
import resend
import os
from dotenv import load_dotenv

load_dotenv()


resend.api_key = os.getenv("RESEND_API_KEY")

def send_approval_email(to_email: str, user_name: str):
    """Envoie un email de bienvenue quand le compte est approuvé."""
    try:
        params = {
            "from": "NovaShop Support <onboarding@resend.dev>", # Adresse par défaut Resend en mode free
            "to": [to_email],
            "subject": " Votre compte NovaShop a été approuvé !",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                <h2 style="color: #2c3e50;">Bonjour {user_name},</h2>
                <p>Votre compte a été validé avec succès par notre équipe.</p>
                <p>Vous pouvez désormais vous connecter pour :</p>
                <ul>
                    <li>Suivre vos commandes en temps réel</li>
                    <li>Demander des remboursements</li>
                    <li>Bénéficier de votre programme de fidélité</li>
                </ul>
                <p style="margin-top: 20px;">Cordialement,<br><strong>L'équipe Support NovaShop</strong></p>
            </div>
            """
        }
        email = resend.Emails.send(params)
        print(f"✅ Email envoyé à {to_email}")
        return {"success": True, "message": "Email envoyé avec succès."}
        
    except Exception as e:
        # C'est ici qu'on capture l'erreur (ex: format invalide)
        error_msg = str(e)
        print(f"❌ Erreur envoi email à {to_email}: {error_msg}")
        return {"success": False, "message": f"Échec de l'envoi : {error_msg}"}       