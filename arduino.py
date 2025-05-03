import serial
import serial.tools.list_ports

def detectar_porta_arduino():
    for porta in serial.tools.list_ports.comports():
        if "Arduino" in porta.description or "CH340" in porta.description:
            return porta.device
    return None

def conectar_arduino():
    porta = detectar_porta_arduino()
    if not porta:
        print("[ERRO] Arduino não encontrado.")
        return None
    try:
        print(f"[INFO] Conectando ao Arduino na porta {porta}...")
        
        return serial.Serial(porta, 9600, timeout=1)
    except Exception as e:
        print("[ERRO] Falha ao conectar na porta serial:", e)
        return None
