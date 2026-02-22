import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURAÇÕES DE ENGENHARIA (Lidas do Render) ---
# Usamos os IDs e Tokens que você salvou no painel Environment
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- MOTOR DE INTELIGÊNCIA (Gemini 2.5 Flash) ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def enviar_resposta_whatsapp(destinatario, texto):
    """
    Função com debug ativado para monitorar a resposta da Meta.
    O ID utilizado é o 1038979222625523.
    """
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
    
    # --- LOGS DE SAÍDA (Aparecerão no painel do Render) ---
    print(f"\n--- DEBUG DE SAÍDA ---")
    print(f"Enviando para: {destinatario}")
    print(f"Status Code da Meta: {response.status_code}")
    print(f"Resposta Completa da Meta: {response.json()}")
    print(f"----------------------\n")
    
    return response.json()

@app.route("/webhook", methods=["GET"])
def validar_webhook():
    """Valida a conexão com o token 'dombosco123'"""
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Falha na verificação", 403

@app.route("/webhook", methods=["POST"])
def receber_comando():
    """Processa a entrada e gera a resposta da Secretaria Dom Bosco"""
    dados = request.get_json()

    try:
        if dados.get("entry") and "messages" in dados["entry"][0]["changes"][0]["value"]:
            msg_data = dados["entry"][0]["changes"][0]["value"]["messages"][0]
            id_do_fiel = msg_data["from"]
            texto_do_fiel = msg_data["text"]["body"]

            print(f"Mensagem recebida de {id_do_fiel}: {texto_do_fiel}")

            # Persona e Regras de Formatação (Citações Católicas)
            prompt_sistema = (
                "Você é o assistente virtual da Secretaria Dom Bosco. "
                "Seja extremamente acolhedor. "
                "Ao citar passagens bíblicas, use marcações católicas (ex: Jo 3, 16). "
                f"Pergunta do fiel: {texto_do_fiel}"
            )

            # Execução no Gemini 2.5
            resposta_ia = model.generate_content(prompt_sistema)
            texto_final = resposta_ia.text

            # Tentativa de envio de volta para o WhatsApp
            enviar_resposta_whatsapp(id_do_fiel, texto_final)

    except Exception as e:
        print(f"ERRO TÉCNICO: {e}")

    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    # O Render define a porta automaticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
