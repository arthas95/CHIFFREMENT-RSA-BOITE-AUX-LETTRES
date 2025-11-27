from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
import base64
import json
from fonctionEcritureLecture import *  # contient chiffrer_rsa / dechiffrer_rsa
import os

def chiffre_en_AES(message):
    # Génère une clé AES aléatoire de 256 bits (32 octets)
    key = get_random_bytes(32)
    message = str(message).encode("utf-8")
    # Crée un objet de chiffrement AES en mode EAX (chiffrement + authentification)
    cipher = AES.new(key, AES.MODE_EAX)

    # Chiffre le message (bytes) et calcule un tag d'authentification
    # - ciphertext : données chiffrées
    # - tag        : permet de vérifier que les données n'ont pas été modifiées
    ciphertext, tag = cipher.encrypt_and_digest(message)

    # Nonce (number used once) généré automatiquement par EAX
    # Il est nécessaire pour pouvoir déchiffrer plus tard avec la même clé
    nonce = cipher.nonce

    # ----------------------------
    # Encodage en Base64 (1ère couche)
    # ----------------------------
    # On transforme les bytes (key, ciphertext, nonce, tag)
    # en chaînes de caractères ASCII (str) pour pouvoir les manipuler facilement
    # et les chiffrer avec RSA.
    b64_key = base64.b64encode(key).decode("utf-8")
    b64_ciphertext = base64.b64encode(ciphertext).decode("utf-8")
    b64_nonce = base64.b64encode(nonce).decode("utf-8")
    b64_tag = base64.b64encode(tag).decode("utf-8")

    # ----------------------------
    # Chiffrement RSA + Base64 (2ᵉ couche)
    # ----------------------------
    # On va maintenant PROTÉGER ces chaînes Base64 en les chiffrant avec RSA,
    # puis en re-encodant le résultat RSA (bytes) en Base64 pour pouvoir
    # les stocker dans un JSON (qui n’accepte que du texte).
    messages = []
    messages.append({
        # b64_ciphertext est une str → chiffrer_rsa la convertit en bytes RSA chiffrés
        # base64.b64encode(...) retransforme ces bytes RSA en str Base64 pour JSON
        # On laisse le ciphertext juste en AES + Base64 (pas de RSA dessus)
        "b64_ciphertext": b64_ciphertext,
        "b64_nonce":      base64.b64encode(chiffrer_rsa(b64_nonce)).decode("utf-8"),
        "b64_tag":        base64.b64encode(chiffrer_rsa(b64_tag)).decode("utf-8"),
        "b64_key":        base64.b64encode(chiffrer_rsa(b64_key)).decode("utf-8"),
    })

    # On renvoie une liste contenant une entrée (prêt pour stockage JSON)
    return messages


def stocker_AES(nouvelles_entrees):
    """
    nouvelles_entrees : liste de dict (ce que retourne chiffre_en_AES)
    On ajoute ces entrées à msg_aes.json en gardant l'historique.
    """
    chemin = "msg_aes.json"

    # 1) Charger l'existant s'il existe, sinon partir d'une liste vide
    if os.path.exists(chemin):
        with open(chemin, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)  # liste déjà présente
            except json.JSONDecodeError:
                data = []           # fichier corrompu / vide
    else:
        data = []

    # 2) Ajouter les nouveaux messages (liste) à la liste existante
    data.extend(nouvelles_entrees)

    # 3) Réécrire tout le fichier proprement
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return data
def lire_messages():
    with open("msg_aes.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        messages_clairs = []
        for entry in data:
            b64_ciphertext = entry["b64_ciphertext"]
            rsa_b64_nonce  = entry["b64_nonce"]
            rsa_b64_tag    = entry["b64_tag"]
            rsa_b64_key    = entry["b64_key"]

            # b) Base64 -> bytes RSA chiffrés
            enc_nonce = base64.b64decode(rsa_b64_nonce)
            enc_tag   = base64.b64decode(rsa_b64_tag)
            enc_key   = base64.b64decode(rsa_b64_key)

            # c) RSA -> texte Base64 original
            b64_nonce = dechiffrer_rsa(enc_nonce)
            b64_tag   = dechiffrer_rsa(enc_tag)
            b64_key   = dechiffrer_rsa(enc_key)

            # d) Base64 -> bytes pour AES
            ciphertext = base64.b64decode(b64_ciphertext)
            nonce      = base64.b64decode(b64_nonce)
            tag        = base64.b64decode(b64_tag)
            key        = base64.b64decode(b64_key)

            # e) Déchiffrer AES
            cipher = AES.new(key, AES.MODE_EAX, nonce)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            messages_clairs.append(decrypted.decode("utf-8"))

    return messages_clairs


# ----------------------------
# Exemple d'utilisation
# ----------------------------
# On chiffre le message b"Salam" avec AES+RSA puis on stocke le résultat dans msg_aes.json
stocker_AES(chiffre_en_AES("kos omak"))

resultat = lire_messages()
print(resultat)
#pour dechiffrer
# DECHIFFRER
#decipher = AES.new(key, AES.MODE_EAX, nonce)
#plaintext = decipher.decrypt_and_verify(ciphertext, tag)
#print(plaintext.decode("utf-8"))