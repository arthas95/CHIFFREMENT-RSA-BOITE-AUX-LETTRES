# ================================================================
#  Petite boîte aux lettres chiffrée pour Al-Misri
#  (version RSA + AES avec msg_aes.json)
# ================================================================

from pydantic import BaseModel                     # Schémas de données pour les requêtes
from fastapi.responses import HTMLResponse        # Pour renvoyer une page HTML
from fastapi import FastAPI, HTTPException        # FastAPI et gestion des erreurs HTTP

# Anciennes fonctions (RSA seul) – on garde juste TOTP
from fonctionEcritureLecture import (
    validation_totp                                # vérifie un code TOTP (True/False)
)

# Nouvelle logique hybride AES + RSA
from testAES import (
    chiffre_en_AES,                                # chiffre un message et retourne une entrée à stocker
    stocker_AES,                                   # ajoute des entrées dans msg_aes.json
    lire_messages                                  # lit msg_aes.json et renvoie les messages déchiffrés
)


# -----------------------------------------------------
#  Pydantic model pour TOTP
# -----------------------------------------------------
class TotpCode(BaseModel):
    code: str   # le code TOTP à 6 chiffres envoyé par le client


# -----------------------------------------------------
#  Pydantic model pour /message
# -----------------------------------------------------
class Message(BaseModel):
    message: str  # contenu texte du message à chiffrer et stocker


# -----------------------------------------------------
#  Instanciation de l'application FastAPI
# -----------------------------------------------------
app = FastAPI()

# (les constantes HISTORIQUE_FILE / PRIVATE_KEY_FILE ne sont plus utilisées ici,
#  tout passe par msg_aes.json dans testAES.py)


# =====================================================
#            ENDPOINT : POST /message
#  Ajoute un message dans la "boîte aux lettres"
#  - Reçoit : { "message": "..." }
#  - Action : chiffre (AES + RSA) + stocke dans msg_aes.json
#  - Retour : JSON de confirmation
# =====================================================
@app.post("/message")
async def ajouter_message(payload: Message):
    """
    Endpoint pour déposer un message dans la boîte aux lettres.
    Le message est chiffré (AES + RSA) et ajouté dans msg_aes.json.
    """
    # Chiffre le message puis l'ajoute dans le fichier JSON via testAES
    entrees = chiffre_en_AES(payload.message)  # -> liste avec 1 dict
    stocker_AES(entrees)

    return {"status": "ok", "message": "Ajouté !"}


# =====================================================
#            ENDPOINT : GET /messages
#  Retourne tous les messages déchiffrés en JSON
#  - Protégé par TOTP (?otp=XXXXXX)
# =====================================================
@app.get("/messages")
async def lire_messages_api(otp: str):
    """
    Retourne tous les messages déchiffrés sous forme JSON.
    Exemple de réponse :
    [
      { "message": "Salam ..." },
      ...
    ]
    """
    # Vérification du code TOTP
    if not validation_totp(otp):
        return "CODE INVALIDE"

    # lire_messages() (testAES) renvoie une liste de strings (messages en clair)
    messages_clairs = lire_messages()

    # On renvoie une liste de dicts pour rester cohérent avec l'ancien format
    return [{"message": m} for m in messages_clairs]


# =====================================================
#            ENDPOINT : POST /totp
#  Vérifie un code TOTP envoyé par le client.
# =====================================================
@app.post("/totp")
def envoie_code(payload: TotpCode):
    """
    Vérifie un code TOTP. Sert de test / endpoint pour vérifier que
    ton appli TOTP (Google Authenticator, etc.) est bien synchronisée.
    """
    if validation_totp(payload.code):
        return {"valid": True, "message": "Accès autorisé 🟩"}
    else:
        raise HTTPException(status_code=401, detail="Code TOTP invalide")


# =====================================================
#         ENDPOINT : GET /consultation
#  Page HTML pour consulter la boîte aux lettres.
#  - Protégée par un code TOTP (paramètre ?otp=123456)
#  - Si le code TOTP est mauvais → 401 Accès refusé
#  - Sinon → page HTML avec tous les messages déchiffrés
# =====================================================
@app.get("/consultation", response_class=HTMLResponse)
async def consultation(otp: str):
    """
    Page HTML protégée par TOTP.
    - L'utilisateur doit fournir un paramètre ?otp=CODE
    - Si le code est valide -> on affiche tous les messages déchiffrés
    - Sinon -> accès refusé
    Exemple d'URL :
      http://localhost:8000/consultation?otp=123456
    """

    # Vérification TOTP
    if not validation_totp(otp):
        return HTMLResponse("<h1>Accès refusé 🟥</h1>", status_code=401)

    # Récupération des messages déchiffrés via AES + RSA
    messages_clairs = lire_messages()

    # Construction du HTML
    html = """
    <html>
    <head>
        <title>Messages d'Al Misri</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f7f7f7;
                padding: 20px;
            }
            h1 {
                text-align: center;
                color: #333;
            }
            .message {
                background: white;
                padding: 15px;
                margin: 15px auto;
                border-radius: 8px;
                width: 60%;
                box-shadow: 0px 3px 6px rgba(0,0,0,0.1);
            }
            .content {
                font-size: 16px;
                color: #222;
            }
        </style>
    </head>
    <body>
        <h1>📜 Historique des Messages</h1>
    """

    for m in messages_clairs:
        html += f"""
        <div class="message">
            <div class="content">{m}</div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return HTMLResponse(content=html)
