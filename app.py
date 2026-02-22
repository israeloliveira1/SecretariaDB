import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Pegamos os dados das Variáveis de Ambiente do Render por segurança
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Inicializa o Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def enviar_whatsapp(numero, texto):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    return requests.post(url, json=payload, headers=headers).json()

@app.route("/webhook", methods=["GET"])
def verificar():
    # Esta parte resolve o erro de validação da Meta
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token Inválido", 403

@app.route("/webhook", methods=["POST"])
def receber():
    dados = request.get_json()
    try:
        if dados.get("entry") and "messages" in dados["entry"][0]["changes"][0]["value"]:
            msg = dados["entry"][0]["changes"][0]["value"]["messages"][0]
            numero_fiel = msg["from"]
            texto_fiel = msg["text"]["body"]

            # Lógica da IA acolhedora
            prompt = f"Você é o assistente virtual da Secretaria Dom Bosco. Responda com carinho: {texto_fiel}"
            resposta_ia = model.generate_content(prompt)
            
            enviar_whatsapp(numero_fiel, resposta_ia.text)
    except:
        pass
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
