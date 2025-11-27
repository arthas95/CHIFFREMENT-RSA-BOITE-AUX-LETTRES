from pydantic import BaseModel                      # Sert à définir des schémas de données (Pydantic) pour les requêtes
from fastapi.responses import HTMLResponse          # Pour renvoyer une vraie page HTML depuis FastAPI
from fastapi import FastAPI, HTTPException          # FastAPI = framework API, HTTPException = renvoyer des erreurs HTTP
from fonctionEcritureLecture import (               # Fonctions maison pour la crypto et l'historique
    ecrire_historique_api,                          #   - chiffre et ajoute un message dans le fichier JSON
    lire_historique,                                #   - lit et déchiffre tous les messages du fichier JSON
    validation_totp,
    style_messages_discord                                #   - vérifie un code TOTP (True/False)
)
from main import *
import json
from testAES import *


# ============================================================
#                   BOT DISCORD CHIFFRÉ
#    Envoie les messages au serveur FastAPI (RSA + TOTP)
#    Utilisation : /courrier ton message
# ============================================================

import discord
import requests

# ------------------------------------------------------------
# CONFIGURATION API
# ------------------------------------------------------------
API_URL = "http://127.0.0.1:8000"   # Ton API FastAPI locale
ROUTE_MESSAGE = "/message"          # POST
ROUTE_TOTP = "/totp"                # POST
ROUTE_CONSULTATION = "/messages"    #GET

# ------------------------------------------------------------
# INTENTS DISCORD
# ------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# ------------------------------------------------------------
# BOT ONLINE
# ------------------------------------------------------------
@client.event
async def on_ready():
    print("====================================================")
    print(f"🤖 Bot connecté : {client.user}")
    print("====================================================")

# ------------------------------------------------------------
# SURVEILLER LES MESSAGES
# ------------------------------------------------------------
@client.event
async def on_message(message):
    # Ignore ses propres messages
    if message.author == client.user:
        return

    # --------------------------------------------------------
    # COMMANDE : /courrier <message>
    # --------------------------------------------------------
    if message.content.startswith("#courrier"):
        contenu = message.content.replace("#courrier", "").strip()

        if contenu == "":
            await message.channel.send("⚠️ Mets un texte : `/courrier ton message`")
            return

        # Requête API → Ajout message chiffré
        payload = {"message": contenu}
        r = requests.post(API_URL + ROUTE_MESSAGE, json=payload)

        if r.status_code == 200:
            await message.channel.send("📨 Message chiffré et envoyé à la boîte d'Al-Misri.")
        else:
            await message.channel.send("❌ Erreur lors de l’envoi.")

    # --------------------------------------------------------
    # COMMANDE : /totp 123456
    # (permet de tester un code TOTP depuis Discord)
    # --------------------------------------------------------
    if message.content.startswith("#totp"):
        code = message.content.replace("#totp", "").strip()

        if len(code) < 4:
            await message.channel.send("⚠️ Code trop court.")
            return

        payload = {"code": code}
        r = requests.post(API_URL + ROUTE_TOTP, json=payload)
        msg = requests.get(API_URL + ROUTE_CONSULTATION+"?otp="+code)
        if r.status_code == 200:
            await message.channel.send("🟩 Code valide — accès autorisé.")
            messages_list = json.loads(msg.text)
            await message.channel.send(msg.content)
        else:
            await message.channel.send("🟥 Code invalide.")
    if message.content.startswith("#ping"):
        await message.channel.send("PONG")

# ------------------------------------------------------------
# TOKEN DU BOT DISCORD (A REMPLACER PAR TOI)
# ------------------------------------------------------------
DISCORD_TOKEN = ""

client.run(DISCORD_TOKEN)
