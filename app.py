import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- CARREGAMENTO DE VARIÁVEIS (Configuradas no Render) ---
# Essas chaves garantem a segurança do seu sistema
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- CONFIGURAÇÃO DO MOTOR (Gemini 2.5) ---
# Atualizado conforme solicitado para a versão 2.5 observada nos logs
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def enviar_resposta_whatsapp(destinatario, texto):
    """Envia a mensagem final para o fiel através da API da Meta"""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": {"body": texto}
    }
    # O ID do número utilizado será o 1038979222625523
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

@app.route("/webhook", methods=["GET"])
def validar_webhook():
    """Realiza o aperto de mão com a Meta usando o token dombosco123"""
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Falha na verificação do token", 403

@app.route("/webhook", methods=["POST"])
def receber_comando():
    """Recebe o sinal do WhatsApp, processa na IA e devolve a resposta"""
    dados = request.get_json()

    try:
        # Verifica se recebemos uma mensagem válida
        if dados.get("entry") and "messages" in dados["entry"][0]["changes"][0]["value"]:
            mensagem_raw = dados["entry"][0]["changes"][0]["value"]["messages"][0]
            
            # Respondemos para o ID que nos enviou a mensagem para evitar o limbo do 9º dígito
            id_fiel = mensagem_raw["from"]
            texto_enviado = mensagem_raw["text"]["body"]

            # --- LÓGICA DA IA (Secretaria Dom Bosco) ---
            prompt_sistema = (
                "Você é o assistente virtual da Secretaria Dom Bosco. "
                "Seja extremamente acolhedor e prestativo. "
                "Ao citar passagens bíblicas, use OBRIGATORIAMENTE o formato de marcações católicas (ex: Jo 3, 16 ou Mt 7, 7). "
                f"Mensagem recebida: {texto_enviado}"
            )

            # Geração de conteúdo usando o motor gemini-2.5-flash
            resposta_ia = model.generate_content(prompt_sistema)
            texto_final = resposta_ia.text

            # Envia a resposta de volta ao WhatsApp
            enviar_resposta_whatsapp(id_fiel, texto_final)

    except Exception as e:
        print(f"Erro no processamento técnico: {e}")

    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    # O Render gerencia a porta dinamicamente através da variável PORT
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
