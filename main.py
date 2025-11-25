# main.py
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi import FastAPI
from fonctionEcritureLecture import ecrire_historique_api, lire_historique

class Message(BaseModel):
    message: str

app = FastAPI()

HISTORIQUE_FILE = "historique_msg.json"
PRIVATE_KEY_FILE = "ma_cle_privee.pem"

# -------------------------
#    AJOUTER UN MESSAGE
# -------------------------
@app.post("/message")
async def ajouter_message(payload: Message):
    ecrire_historique_api(HISTORIQUE_FILE, payload.message)
    return {"status": "ok", "message": "Ajouté !"}

    
    ecrire_historique_api(HISTORIQUE_FILE, message)
    return {"status": "message ajouté"}


# -------------------------
#   LIRE LES MESSAGES (JSON)
# -------------------------
@app.get("/messages")
async def lire_messages():
    messages = lire_historique(PRIVATE_KEY_FILE, HISTORIQUE_FILE)
    return messages


@app.get("/consultation", response_class=HTMLResponse)
async def consultation():
    messages = lire_historique(PRIVATE_KEY_FILE, HISTORIQUE_FILE)

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

    for msg in messages:
        html += f"""
        <div class="message">
            <div class="date">{msg['date']}</div>
            <div class="content">{msg['message']}</div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return HTMLResponse(content=html)