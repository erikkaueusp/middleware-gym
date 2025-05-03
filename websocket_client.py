import time
import threading
import websocket
from auth import obter_token

# deve estar fora de qualquer função
modo_scan_ativo = False  # ainda é global

def ativar_modo_scan(arduino):
    global modo_scan_ativo
    if not modo_scan_ativo:
        modo_scan_ativo = True
        print("[MODO SCAN] Ativado automaticamente na inicialização")
        threading.Thread(target=modo_scan_loop, args=(arduino,), daemon=True).start()


def modo_scan_loop(arduino):
    global modo_scan_ativo

    while modo_scan_ativo:
        if not arduino or not arduino.is_open:
            print("[ERRO] Arduino desconectado. Encerrando modo scan.")
            modo_scan_ativo = False
            break

        print("[MODO SCAN] Enviando comando 'scan'")
        arduino.write(b"scan\n")

        while modo_scan_ativo:
            try:
                if arduino.in_waiting:
                    time.sleep(1)
                    resposta = arduino.readline().decode('utf-8').strip()
                    if resposta:
                        print(f"[ARDUINO] {resposta}")

                        if resposta.startswith("ID encontrado:") or "Trava desativada" in resposta:
                            print("[MODO SCAN] Sucesso - aguardando 5s antes de novo scan")
                            time.sleep(5)
                            break  # volta para novo scan


                        elif "Digital não encontrada" in resposta:
                            print("[MODO SCAN] Falha - reiniciando scan aguardando 2s antes de novo scan")
                            time.sleep(2)
                            break  # volta para novo scan

                time.sleep(0.1)
                arduino.write(b"scan\n")
            except Exception as e:
                print("[ERRO] Falha ao ler resposta do Arduino:", e)
                modo_scan_ativo = False
                break


    # Modo scan foi desativado — enviar comando neutro para limpar o estado do sensor
    try:
        print("[MODO SCAN] Desativado. Enviando 'cancelar' para sair do scan.")
        arduino.write(b"cancelar\n")
    except Exception as e:
        print("[ERRO] Falha ao enviar 'cancelar' após desativação:", e)




def iniciar_websocket(arduino, ws_url):
    def on_message(ws, message):
        global modo_scan_ativo
        print("[MESSAGE]", message)

        if not arduino or not arduino.is_open:
            print("[ERRO] Arduino não está conectado.")
            return

        try:
            # Comando especial: ativar/desativar modo scan
            if message.startswith("modo-scan:"):
                acao = message.split(":")[1]
                if acao == "ativar":
                    if not modo_scan_ativo:
                        modo_scan_ativo = True
                        print("[MODO SCAN] Ativado")
                        threading.Thread(target=modo_scan_loop, args=(arduino,), daemon=True).start()
                    else:
                        print("[MODO SCAN] Já está ativo")
                elif acao == "desativar":
                    modo_scan_ativo = False
                    print("[MODO SCAN] Desativado")
                return

            # Comando normal (ex: enroll 3 ou scan)
            if message.startswith("cadastrar-digital:"):
                id_aluno = message.split(":")[1]
                comando = f"enroll {id_aluno}"
            else:
                comando = message.strip()
            
            if message.startswith("destravar"):
                comando = message

            arduino.write((comando + "\n").encode("utf-8"))
            print(f"[INFO] Comando enviado ao Arduino: {comando}")
        except Exception as e:
            print("[ERRO] Erro ao enviar para Arduino:", e)

    def on_error(ws, error):
        print("[ERROR]", error)

    def on_close(ws, code, msg):
        print(f"[CLOSE] code={code} msg={msg}")

    def on_open(ws):
        print("[OPEN] Conexão WebSocket estabelecida.")
        # Inicia thread de leitura contínua da serial
        threading.Thread(target=ler_serial_continuamente, args=(arduino, ws), daemon=True).start()

    def ler_serial_continuamente(arduino, ws):
        while True:
            try:
                if arduino.in_waiting:
                    resposta = arduino.readline().decode('utf-8').strip()
                    if resposta:
                        print(f"[ARDUINO] {resposta}")
                        try:
                            ws.send(f"{resposta}")
                        except:
                            print("[ERRO] Não foi possível enviar resposta ao backend.")
                time.sleep(0.1)
            except Exception as e:
                print("[ERRO] Falha ao ler da serial:", e)
                break
                

    token = obter_token()
    if not token:
        print("[ERRO] Token não obtido. Abortando conexão WebSocket.")
        return

    ws = websocket.WebSocketApp(
        ws_url,
        header=[f"Authorization: {token}"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()

