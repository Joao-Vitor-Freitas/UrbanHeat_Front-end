import requests
import random
import time

API_URL = "http://127.0.0.1:8000"

regions = ["Centro", "Norte", "Sul", "Leste", "Oeste"]
sensors = {"Centro": "C1", "Norte": "N1", "Sul": "S1", "Leste": "L1", "Oeste": "O1"}


def seed_database():
    print("🚀 Iniciando população do banco de dados...")

    # 1. Criar Regiões
    region_ids = {}
    for r_name in regions:
        res = requests.post(f"{API_URL}/regions/", json={"name": r_name})
        if res.status_code in [201, 409]:  # Ignora se já existir
            pass

    # 2. Pegar os IDs das regiões e criar Sensores
    res = requests.get(f"{API_URL}/regions/")
    for r in res.json():
        r_id = r["id"]
        r_name = r["name"]
        region_ids[r_name] = r_id

        s_code = sensors.get(r_name)
        if s_code:
            requests.post(
                f"{API_URL}/sensors/", json={"sensor_code": s_code, "region_id": r_id}
            )
            print(f"✅ Sensor {s_code} vinculado à região {r_name}.")

    # 3. Enviar 24 medições de histórico (simulando 24 horas)
    print("\n📡 Gerando histórico de medições climáticas...")
    for _ in range(24):
        for r_name, s_code in sensors.items():
            # Forçamos tendências diferentes para o mapa ficar colorido
            if r_name == "Norte":  # Crítico (Muito quente e seco)
                temp = random.uniform(36.0, 42.0)
                hum = random.uniform(20.0, 35.0)
            elif r_name == "Leste":  # Alto
                temp = random.uniform(32.0, 36.0)
                hum = random.uniform(40.0, 50.0)
            elif r_name == "Centro":  # Moderado
                temp = random.uniform(25.0, 32.0)
                hum = random.uniform(50.0, 60.0)
            else:  # Baixo (Sul, Oeste)
                temp = random.uniform(18.0, 24.0)
                hum = random.uniform(65.0, 85.0)

            requests.post(
                f"{API_URL}/measurements/",
                json={
                    "sensor_code": s_code,
                    "temperature": round(temp, 2),
                    "humidity": round(hum, 2),
                },
            )

    # 4. Calcular HeatScore para cada região
    print("\n🧮 Calculando HeatScores com Pandas/NumPy...")
    for r_name, r_id in region_ids.items():
        res = requests.post(f"{API_URL}/heatscore/regions/{r_id}/calculate")
        if res.status_code == 201:
            score = res.json().get("score", 0)
            print(f"🔥 {r_name} -> Score: {score}")

    print("\n🏁 Feito! Pode atualizar sua página index.html.")


if __name__ == "__main__":
    try:
        seed_database()
    except requests.exceptions.ConnectionError:
        print(
            "❌ ERRO: A API não está rodando. Inicie o backend com 'uvicorn api:app --reload' primeiro."
        )
