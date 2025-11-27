from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import json, base64
from datetime import datetime
from fastapi import FastAPI
import pyotp
import asyncio



# -------- Chargement des clés (fait une seule fois au chargement du module) --------

# fonctionEcritureLecture.py

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import json, base64
from datetime import datetime

# -------- Chargement des clés --------

with open("ma_clee_public.pem", "rb") as pub_file:
    public_key = RSA.import_key(pub_file.read())

with open("ma_cle_privee.pem", "rb") as priv_file:
    private_key = RSA.import_key(priv_file.read())

cipher = PKCS1_OAEP.new(public_key)
decipher = PKCS1_OAEP.new(private_key)


def chiffrer_rsa(data):
    if isinstance(data, str):
        data = data.encode("utf-8")

    result = cipher.encrypt(data)
    return result
def dechiffrer_rsa(data):
    result = decipher.decrypt(data)
    return result.decode("utf-8")


# --------------------------------------------------------
#   ÉCRITURE VIA API (sans input, version propre)
# --------------------------------------------------------
def ecrire_historique_api(historique_file, message):
    try:
        with open(historique_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    lettre_chiffre = cipher.encrypt(message.encode("utf-8"))

    data.append({
        "date": datetime.now().isoformat(),
        "ciphertext": base64.b64encode(lettre_chiffre).decode("utf-8")
    })

    with open(historique_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



# --------------------------------------------------------
#   LECTURE DÉCHIFFRÉE (retourne une liste de messages)
# --------------------------------------------------------
def lire_historique(private_key_file, historique_file):
    with open(private_key_file, "rb") as f:
        private_key = RSA.import_key(f.read())

    decipher = PKCS1_OAEP.new(private_key)

    with open(historique_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = []

    for entry in data:
        ciphertext = base64.b64decode(entry["ciphertext"])
        message = decipher.decrypt(ciphertext).decode("utf-8")
        
        messages.append({
            "date": entry["date"],
            "message": message
        })

    return messages

def validation_totp(code):
        #TOTP
    SECRET_TOTP = "GNITM2HC2S5JJMXZOXIRKUG2T24A5OWY"
    totp = pyotp.TOTP(SECRET_TOTP)

    
    if totp.verify(code):
        print("Accès autorisé 🟩")
        return True
    else:
        print("Accès refusé 🟥")
        return False
    

def style_messages_discord(messages):
    """
    Améliore le rendu Discord : reçoit une liste [{"date":..., "message":...}], donne une chaîne markdown stylée.
    """
    if not messages:  # check liste vide
        return "⚠️ Aucun message à afficher."
    styled = []
    for entry in messages:
        date = entry.get('date', '???')
        msg = entry.get('message', '')
        styled.append(f"✉️ **{date}** : {msg}")
    
    # Ajoute tout dans le bloc markdown
    return "``````"
