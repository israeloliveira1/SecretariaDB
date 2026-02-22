import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURAÇÕES DE ENGENHARIA ---
# O sistema lê os tokens que você já salvou no Render
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- MOTOR DE INTELIGÊNCIA (Gemini 2.0 Flash) ---
# Alterado para 2.0 para evitar o erro 429 de quota
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def enviar_resposta_whatsapp(destinatario, texto):
    """Envia a mensagem final para o WhatsApp via API da Meta"""
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
    
    response = requests.post(url, json=payload, headers=headers)
    
    # Logs de debug para monitorarmos a saída no painel do Render
    print(f"\n--- DEBUG DE SAÍDA ---")
    print(f"Status Code da Meta: {response.status_code}")
    print(f"Resposta da Meta: {response.json()}")
    print(f"----------------------\n")
    
    return response.json()

@app.route("/webhook", methods=["GET"])
def validar_webhook():
    """Realiza o aperto de mão com a Meta usando o token 'dombosco123'"""
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Falha na verificação", 403

@app.route("/webhook", methods=["POST"])
def receber_comando():
    """Recebe a mensagem, processa no Gemini 2.0 e responde"""
    dados = request.get_json()

    try:
        # Detecta se há uma nova mensagem de texto
        if dados.get("entry") and "messages" in dados["entry"][0]["changes"][0]["value"]:
            msg_data = dados["entry"][0]["changes"][0]["value"]["messages"][0]
            id_fiel = msg_data["from"]
            texto_fiel = msg_data["text"]["body"]

            print(f"Mensagem recebida de {id_fiel}: {texto_fiel}")

            # Persona da Secretaria Dom Bosco com marcações católicas
            prompt_sistema = (
                "Você é o assistente virtual da Secretaria Dom Bosco. "
                "Seja acolhedor e ajude com informações paroquiais. "
                "Ao citar a Bíblia, use o formato de marcações católicas (ex: Jo 3, 16). "
                f"Mensagem do fiel: {texto_fiel}"
            )

            # Processamento no novo motor 2.0
            resposta_ia = model.generate_content(prompt_sistema)
            texto_final = resposta_ia.text

            # Envio da resposta
            enviar_resposta_whatsapp(id_fiel, texto_final)

    except Exception as e:
        print(f"ERRO TÉCNICO: {e}")

    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    # O Render gerencia a porta automaticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
