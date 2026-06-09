import sqlite3
from datetime import datetime, timedelta

DB_PATH = "ilhas_calor.db"

# Faixas fisicas validas para validacao das medicoes
TEMP_MIN, TEMP_MAX = -10.0, 60.0   # graus Celsius
UMID_MIN, UMID_MAX =   0.0, 100.0  # percentual


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS regioes (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensores (
            sensor_id TEXT PRIMARY KEY,
            regiao_id INTEGER,
            FOREIGN KEY (regiao_id) REFERENCES regioes(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medicoes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id   TEXT,
            temperatura REAL,
            umidade     REAL,
            data_hora   TEXT,
            FOREIGN KEY (sensor_id) REFERENCES sensores(sensor_id)
        )
    """)
    conn.commit()
    conn.close()


def adicionar_regiao(nome: str):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO regioes (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()


def adicionar_sensor(sensor_id: str, regiao_nome: str):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO regioes (nome) VALUES (?)", (regiao_nome,))
    cur.execute("SELECT id FROM regioes WHERE nome = ?", (regiao_nome,))
    regiao_id = cur.fetchone()[0]
    cur.execute(
        "INSERT OR IGNORE INTO sensores (sensor_id, regiao_id) VALUES (?, ?)",
        (sensor_id, regiao_id)
    )
    conn.commit()
    conn.close()


def validar_medicao(temperatura: float, umidade: float) -> tuple[bool, str]:
    """
    Valida se temperatura e umidade estao dentro de faixas fisicas validas.

    Retorna:
        (True, "")           — medicao valida
        (False, "mensagem")  — medicao invalida com motivo
    """
    if not (TEMP_MIN <= temperatura <= TEMP_MAX):
        return False, (
            f"Temperatura {temperatura}°C fora da faixa valida "
            f"({TEMP_MIN}°C a {TEMP_MAX}°C)"
        )
    if not (UMID_MIN <= umidade <= UMID_MAX):
        return False, (
            f"Umidade {umidade}% fora da faixa valida "
            f"({UMID_MIN}% a {UMID_MAX}%)"
        )
    return True, ""


def salvar_medicao(sensor_id: str, temperatura: float, umidade: float, data_hora: datetime):
    """
    Valida e salva uma medicao no banco.
    Lanca ValueError se os valores estiverem fora das faixas fisicas validas.
    """
    valida, motivo = validar_medicao(temperatura, umidade)
    if not valida:
        raise ValueError(f"Medicao invalida — {motivo}")

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO medicoes (sensor_id, temperatura, umidade, data_hora) VALUES (?, ?, ?, ?)",
        (sensor_id, temperatura, umidade, data_hora.isoformat())
    )
    conn.commit()
    conn.close()


def get_medicoes_por_regiao(regiao_nome: str, dias: int = 30) -> list:
    """
    Retorna as medicoes de uma regiao dos ultimos N dias.

    Parametros:
        regiao_nome : nome da regiao
        dias        : janela de tempo em dias (padrao: 30)

    Retorna lista de tuplas (temperatura, umidade, data_hora).
    """
    limite_data = (datetime.now() - timedelta(days=dias)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        SELECT m.temperatura, m.umidade, m.data_hora
        FROM   medicoes  m
        JOIN   sensores  s ON m.sensor_id  = s.sensor_id
        JOIN   regioes   r ON s.regiao_id  = r.id
        WHERE  r.nome    = ?
          AND  m.data_hora >= ?
        ORDER  BY m.data_hora DESC
        LIMIT  500
    """, (regiao_nome, limite_data))
    rows = cur.fetchall()
    conn.close()
    return rows