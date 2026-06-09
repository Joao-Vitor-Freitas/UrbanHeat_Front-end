import threading
import sys
from database import init_db
from serial_reader import iniciar_leitura
import uvicorn


def main():
    init_db()
    print("✓ Banco de dados inicializado.\n")

    # Porta serial: argumento opcional na linha de comando
    # Windows:   python main.py COM3
    # Linux/Mac: python main.py /dev/ttyUSB0
    # Auto:      python main.py
    porta = sys.argv[1] if len(sys.argv) > 1 else None

    if porta:
        print(f"Porta serial informada: {porta}")
    else:
        print("Porta não informada — detectando automaticamente...")

    thread_serial = threading.Thread(
        target=iniciar_leitura,
        args=(porta,),
        daemon=True
    )
    thread_serial.start()

    print("\n API em http://0.0.0.0:8000")
    print("   Docs: http://127.0.0.1:8000/docs\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
