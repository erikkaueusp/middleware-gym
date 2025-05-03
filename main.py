import os
import time
from arduino import conectar_arduino
from websocket_client import iniciar_websocket
from dotenv import load_dotenv

load_dotenv()
WS_URL = os.getenv("WS_URL", "ws://localhost:8080/biometria")

def main():
    arduino = conectar_arduino()
    if not arduino:
        return
    
    print("[INFO] Aguardando Arduino inicializar...")
    time.sleep(3)  # <- tempo para o sensor inicializar
    iniciar_websocket(arduino, WS_URL)

if __name__ == "__main__":
    main()
