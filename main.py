# ================================================================
#  Petite boîte aux lettres chiffrée pour Al-Misri
#  ------------------------------------------------
#  Idée :
#   - /message      : point d'entrée pour déposer un message chiffré
#   - /messages     : API JSON pour lire tous les messages déchiffrés
#   - /consultation : page HTML qui affiche les messages (protégée par TOTP)
#   - /totp         : endpoint pour tester/valider un code TOTP
#
#  Les messages ne sont jamais stockés en clair sur le disque :
#   - côté écriture : ecrire_historique_api() chiffre avec RSA et stocke en JSON
#   - côté lecture  : lire_historique() déchiffre avec la clé privée
#
#  Ce système peut être utilisé :
#   - par un bot Discord / Telegram / autre → il appelle /message
#   - par toi (Al-Misri) pour consulter → tu utilises /consultation avec un TOTP
#
#  Résultat : tu n'as plus besoin de laisser traîner des messages sensibles
#  en clair sur Discord, WhatsApp, etc. Tout passe par une API chiffrée,
#  contrôlée par toi.
# ================================================================

from pydantic import BaseModel                      # Sert à définir des schémas de données (Pydantic) pour les requêtes
from fastapi.responses import HTMLResponse          # Pour renvoyer une vraie page HTML depuis FastAPI
from fastapi import FastAPI, HTTPException          # FastAPI = framework API, HTTPException = renvoyer des erreurs HTTP
from fonctionEcritureLecture import (               # Fonctions maison pour la crypto et l'historique
    ecrire_historique_api,                          #   - chiffre et ajoute un message dans le fichier JSON
    lire_historique,                                #   - lit et déchiffre tous les messages du fichier JSON
    validation_totp                                 #   - vérifie un code TOTP (True/False)
)

# -----------------------------------------------------
#  Pydantic model pour TOTP
#  Ce modèle représente le JSON attendu par /totp
#  Exemple de corps de requête :
#    { "code": "123456" }
# -----------------------------------------------------
class TotpCode(BaseModel):
    code: str   # le code TOTP à 6 chiffres envoyé par le client

# -----------------------------------------------------
#  Pydantic model pour /message
#  Ce modèle représente le JSON attendu par /message
#  Exemple de corps de requête :
#    { "message": "Salam aleykoum" }
# -----------------------------------------------------
class Message(BaseModel):
    message: str  # contenu texte du message à chiffrer et stocker

# -----------------------------------------------------
#  Instanciation de l'application FastAPI
# -----------------------------------------------------
app = FastAPI()

# Fichier où l'on stocke l'historique chiffré (JSON)
HISTORIQUE_FILE = "historique_msg.json"

# Fichier contenant la clé privée RSA (pour déchiffrer)
PRIVATE_KEY_FILE = "ma_cle_privee.pem"

# =====================================================
#            ENDPOINT : POST /message
#  Ajoute un message dans la "boîte aux lettres"
#  - Reçoit : { "message": "..." }
#  - Action : chiffre + stocke dans historique_msg.json
#  - Retour : JSON de confirmation
# =====================================================
@app.post("/message")
async def ajouter_message(payload: Message):
    """
    Endpoint pour déposer un message dans la boîte aux lettres.
    Le message est chiffré et ajouté dans le fichier JSON.
    """
    # On appelle la fonction de crypto / stockage (dans fonctionEcritureLecture)
    ecrire_historique_api(HISTORIQUE_FILE, payload.message)

    # On renvoie un petit JSON de confirmation
    return {"status": "ok", "message": "Ajouté !"}

    # ⚠️ Ces lignes étaient dans ton code initial mais sont inutiles
    #    (et 'message' n'est pas défini ici). On les laisse commentées
    #    pour montrer qu'elles sont obsolètes.
    #
    # ecrire_historique_api(HISTORIQUE_FILE, message)
    # return {"status": "message ajouté"}


# =====================================================
#            ENDPOINT : GET /messages
#  Retourne tous les messages déchiffrés en JSON
#  - Utile pour debug / intégrations backend
#  - ATTENTION : pas protégé par TOTP ici
# =====================================================
@app.get("/messages")
async def lire_messages():
    """
    Retourne tous les messages déchiffrés sous forme JSON.
    Exemple de réponse :
    [
      { "date": "...", "message": "Salam ..." },
      ...
    ]
    """
    messages = lire_historique(PRIVATE_KEY_FILE, HISTORIQUE_FILE)
    return messages


# =====================================================
#            ENDPOINT : POST /totp
#  Vérifie un code TOTP envoyé par le client.
#  - Reçoit : { "code": "123456" }
#  - Retourne : { valid: true/false, message: ... } ou 401
# =====================================================
@app.post("/totp")
def envoie_code(payload: TotpCode):
    """
    Vérifie un code TOTP. Sert de test / endpoint pour vérifier que
    ton appli TOTP (Google Authenticator, etc.) est bien synchronisée.
    """
    # On appelle validation_totp(code) qui renvoie True ou False
    if validation_totp(payload.code):
        return {"valid": True, "message": "Accès autorisé 🟩"}
    else:
        # On renvoie une erreur HTTP 401 si le code est incorrect
        raise HTTPException(status_code=401, detail="Code TOTP invalide")


# =====================================================
#        ENDPOINT : GET /consultation
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
    - Si le code est valide -> on affiche tous les messages
    - Sinon -> accès refusé
    Exemple d'URL :
      http://localhost:8000/consultation?otp=123456
    """

    # On vérifie d'abord le code TOTP fourni en paramètre
    if not validation_totp(otp):
        # Si le code est invalide → on renvoie une page 401 HTML
        return HTMLResponse("<h1>Accès refusé 🟥</h1>", status_code=401)

    # Si le TOTP est valide, on récupère les messages déchiffrés
    messages = lire_historique(PRIVATE_KEY_FILE, HISTORIQUE_FILE)

    # -----------------------------
    # Construction du HTML à la main
    # (on pourrait utiliser des templates Jinja, mais ici on reste simple)
    # -----------------------------
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
            .date {
                font-size: 12px;
                color: #888;
                margin-bottom: 5px;
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

    # Pour chaque message, on ajoute un bloc HTML
    for msg in messages:
        html += f"""
        <div class="message">
            <div class="date">{msg['date']}</div>
            <div class="content">{msg['message']}</div>
        </div>
        """

    # On termine le HTML
    html += """
    </body>
    </html>
    """

    # On renvoie la réponse HTML finale
    return HTMLResponse(content=html)
