import json
import datetime
import time
import os
from twilio.rest import Client
from dotenv import load_dotenv

# ========== CONFIGURAÇÃO DO AMBIENTE ==========
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMERO = os.getenv("TWILIO_NUMERO")
SEU_NUMERO = os.getenv("SEU_NUMERO")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMERO, SEU_NUMERO]):
    raise EnvironmentError("⚠️ Variáveis do Twilio não estão configuradas corretamente no .env")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ========== CONSTANTES ==========
HISTORICO_ARQUIVO = "historico.json"
LIMITE_TENTATIVAS = 3
INTERVALO_REENVIO = 600  # 10 minutos

# ========== FUNÇÕES UTILITÁRIAS ==========
def log(msg):
    agora = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{agora} {msg}")

def carregar_historico():
    if not os.path.exists(HISTORICO_ARQUIVO):
        return {"confirmacoes": [], "pendencias": []}
    try:
        with open(HISTORICO_ARQUIVO, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "confirmacoes": data.get("confirmacoes", []),
                "pendencias": data.get("pendencias", [])
            }
    except Exception as e:
        log(f"[❌ ERRO] Falha ao carregar histórico: {e}")
        return {"confirmacoes": [], "pendencias": []}

def salvar_historico(historico):
    try:
        with open(HISTORICO_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"[❌ ERRO] Falha ao salvar histórico: {e}")

def enviar_mensagem(texto):
    try:
        client.messages.create(from_=TWILIO_NUMERO, to=SEU_NUMERO, body=texto)
        log(f"[📤 REENVIO] {texto}")
    except Exception as e:
        log(f"[❌ ERRO WHATSAPP] {e}")

# ========== MONITORAMENTO DE PENDÊNCIAS ==========
def verificar_pendencias():
    historico = carregar_historico()
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    agora = datetime.datetime.now()
    novas_pendencias = []

    for pendencia in historico.get("pendencias", []):
        if pendencia.get("data") != hoje:
            continue

        nome = pendencia.get("remedio")
        horario = pendencia.get("horario")
        tentativas = pendencia.get("tentativas", 0)

        # Verifica se o horário já passou
        hora_completa = datetime.datetime.strptime(f"{hoje} {horario}", "%Y-%m-%d %H:%M")
        if hora_completa > agora:
            continue  # ainda não é hora de lembrar

        # Verifica se já foi confirmado
        confirmado = any(
            c.get("remedio") == nome and c.get("data") == hoje and c.get("hora") == horario
            for c in historico.get("confirmacoes", [])
        )
        if confirmado:
            log(f"[✅ CONFIRMADO] {nome} às {horario}")
            continue

        if tentativas < LIMITE_TENTATIVAS:
            pendencia["tentativas"] = tentativas + 1
            mensagem = (
                f"🔔 Lembrete #{pendencia['tentativas']}: você tomou o remédio {nome} às {horario}?\n"
                "Responda SIM ou NÃO."
            )
            enviar_mensagem(mensagem)
            novas_pendencias.append(pendencia)
        else:
            log(f"[⚠️ LIMITE ATINGIDO] {nome} às {horario} ({tentativas} tentativas)")

    historico["pendencias"] = novas_pendencias
    salvar_historico(historico)

# ========== EXECUÇÃO ==========
if __name__ == "__main__":
    log("🔁 Monitor de reenvios iniciado.")
    while True:
        verificar_pendencias()
        time.sleep(INTERVALO_REENVIO)
