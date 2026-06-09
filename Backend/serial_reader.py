import serial
import serial.tools.list_ports
import json
from datetime import datetime
from database import salvar_medicao, adicionar_sensor


def detectar_porta() -> str:
    """
    Detecta automaticamente a porta serial do Arduino.
    Funciona em Windows (COM*) e Linux/Mac (/dev/ttyUSB*, /dev/ttyACM*).
    """
    portas = list(serial.tools.list_ports.comports())

    for p in portas:
        desc = (p.description or "").lower()
        if any(k in desc for k in ["arduino", "ch340", "cp210", "uart", "usb serial"]):
            print(f"Arduino detectado: {p.device} — {p.description}")
            return p.device

    if portas:
        print("Portas disponíveis:")
        for p in portas:
            print(f"  {p.device} — {p.description}")
        print(f"Usando: {portas[0].device}")
        return portas[0].device

    raise RuntimeError(
        "Nenhuma porta serial encontrada. "
        "Verifique se o Arduino está conectado via USB."
    )


def _inferir_regiao(sensor_id: str) -> str:
    """
    Infere o nome da região a partir do sensor_id.
    Exemplos:
        S-NORTE-01  → Norte
        S-SUL-02    → Sul
        SENSOR-XYZ  → Desconhecida
    """
    regioes_conhecidas = {"NORTE", "SUL", "LESTE", "OESTE", "CENTRO"}
    for parte in sensor_id.upper().split("-"):
        if parte in regioes_conhecidas:
            return parte.capitalize()
    return "Desconhecida"


def _parse_linha(linha: str) -> dict | None:
    """
    Interpreta a linha recebida do Arduino.

    Suporta dois formatos:

    JSON (recomendado para ESP32):
        {"sensor_id":"S-NORTE-01","temperatura":38.5,"umidade":41.0}

    CSV (para Arduino Uno/Mega via Serial):
        S-NORTE-01,38.5,41.0
    """
    linha = linha.strip()
    if not linha:
        return None

    # Tenta JSON
    if linha.startswith("{"):
        try:
            dados = json.loads(linha)
            return {
                "sensor_id"  : str(dados["sensor_id"]),
                "temperatura": float(dados["temperatura"]),
                "umidade"    : float(dados["umidade"]),
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Erro JSON: {linha} — {e}")
            return None

    # Tenta CSV: sensor_id,temperatura,umidade
    partes = linha.split(",")
    if len(partes) == 3:
        try:
            return {
                "sensor_id"  : partes[0].strip(),
                "temperatura": float(partes[1].strip()),
                "umidade"    : float(partes[2].strip()),
            }
        except ValueError as e:
            print(f"Erro CSV: {linha} — {e}")
            return None

    print(f"Formato desconhecido, ignorado: {linha}")
    return None


def iniciar_leitura(porta: str = None, baudrate: int = 9600):
    """
    Inicia a leitura contínua da porta serial do Arduino.

    Parâmetros:
        porta    : Porta serial ('COM3', '/dev/ttyUSB0', etc).
                   Se None, detecta automaticamente.
        baudrate : Taxa de comunicação (deve coincidir com o Arduino).

    Formatos aceitos do Arduino:
        JSON: {"sensor_id":"S-NORTE-01","temperatura":38.5,"umidade":41.0}
        CSV:  S-NORTE-01,38.5,41.0
    """
    if porta is None:
        porta = detectar_porta()

    print(f"Conectando em {porta} ({baudrate} baud)...")

    try:
        ser = serial.Serial(porta, baudrate, timeout=2)
        print(f"✓ Conectado. Aguardando dados do Arduino...\n")
    except serial.SerialException as e:
        print(f"Erro ao abrir porta serial: {e}")
        print("Verifique se o Arduino está conectado e a porta está correta.")
        return

    while True:
        try:
            linha = ser.readline().decode("utf-8", errors="ignore").strip()
            if not linha:
                continue

            dados = _parse_linha(linha)
            if dados is None:
                continue

            # Garante que sensor e região existem no banco antes de salvar
            regiao = _inferir_regiao(dados["sensor_id"])
            adicionar_sensor(dados["sensor_id"], regiao)

            salvar_medicao(
                sensor_id   = dados["sensor_id"],
                temperatura = dados["temperatura"],
                umidade     = dados["umidade"],
                data_hora   = datetime.now()
            )
            print(
                f"✓ [{datetime.now().strftime('%H:%M:%S')}] "
                f"{dados['sensor_id']} ({regiao}) | "
                f"{dados['temperatura']}°C | "
                f"{dados['umidade']}%"
            )

        except serial.SerialException as e:
            print(f"Erro serial: {e}")
            break
        except Exception as e:
            print(f"Erro inesperado: {e}")
