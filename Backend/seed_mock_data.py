import random
from datetime import datetime, timedelta
from database import init_db, adicionar_sensor, salvar_medicao


def gerar_medicoes(sensor_id, regiao, base_temp, umidade_base, tendencia=0.0):
    """
    Gera 24 medicoes simuladas com tendencia configuravel.
    tendencia > 0  = aquecimento (ex: 0.35 = +0.35 grau por leitura)
    tendencia < 0  = resfriamento
    tendencia = 0  = estavel
    """
    agora = datetime.now()
    for i in range(24):
        tempo       = agora - timedelta(minutes=5 * i)
        temperatura = round(base_temp + (i * tendencia) + random.uniform(-0.8, 0.8), 1)
        umidade     = round(umidade_base + random.uniform(-4, 4), 1)
        adicionar_sensor(sensor_id, regiao)
        salvar_medicao(sensor_id, temperatura, umidade, tempo)


def main():
    init_db()

    # regiao, sensor_id, temp_base, umidade_base, tendencia
    regioes = [
        ("Norte", "S-NORTE-01", 36.0, 42.0,  0.35),  # aquecimento acelerado -> critico
        ("Leste", "S-LESTE-01", 33.5, 48.0,  0.12),  # aquecimento gradual   -> alto
        ("Sul",   "S-SUL-01",   31.0, 55.0,  0.02),  # estavel               -> moderado
        ("Oeste", "S-OESTE-01", 29.5, 60.0, -0.08),  # resfriamento          -> baixo
    ]

    print("Gerando dados de mock com tendencias reais...")
    print()
    for regiao, sensor_id, base_temp, umidade_base, tendencia in regioes:
        gerar_medicoes(sensor_id, regiao, base_temp, umidade_base, tendencia)
        if tendencia > 0.2:
            status = "Aquecimento acelerado"
        elif tendencia > 0.05:
            status = "Aquecimento gradual"
        elif tendencia < -0.05:
            status = "Resfriamento"
        else:
            status = "Estavel"
        print(f"  {regiao:<8} | base: {base_temp}C | tendencia: {status}")

    print()
    print("Mock criado! 24 medicoes por regiao com tendencias reais.")


if __name__ == "__main__":
    main()