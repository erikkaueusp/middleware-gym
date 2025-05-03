import os
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8080/auth")
MIDDLEWARE_USUARIO = os.getenv("MIDDLEWARE_USUARIO", "middleware")
MIDDLEWARE_SENHA = os.getenv("MIDDLEWARE_SENHA", "senhaforte123")

def obter_token():
    try:
        resposta = requests.post(AUTH_URL, json={
            "usuario": MIDDLEWARE_USUARIO,
            "senha": MIDDLEWARE_SENHA
        })

        if resposta.status_code != 200:
            print(f"[ERRO] Falha ao autenticar ({resposta.status_code}): {resposta.text}")
            return None

        dados = resposta.json()
        return f"{dados.get('tipo', 'Bearer')} {dados.get('token')}"

    except Exception as e:
        print("[ERRO] Exceção ao obter token:", e)
        return None
