from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sqlite3
import pandas as pd
import io
from datetime import datetime
from heatscore import calcular_heatscore
from services.analise import analisar_tendencia

app = FastAPI(
    title="Monitor de Ilhas de Calor Urbanas",
    description="API de monitoramento termico urbano - ODS 11 e ODS 13",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MedicaoInput(BaseModel):
    sensor_id   : str
    temperatura : float
    umidade     : float
    data_hora   : str | None = None


@app.get("/regioes", summary="Lista todas as regioes cadastradas")
def listar_regioes():
    conn = sqlite3.connect("ilhas_calor.db")
    cur  = conn.cursor()
    cur.execute("SELECT nome FROM regioes")
    regioes = [r[0] for r in cur.fetchall()]
    conn.close()
    return {"regioes": regioes}


@app.post("/medicoes", summary="Recebe medicao via HTTP - Arduino ESP32 ou simulacao manual")
def receber_medicao(medicao: MedicaoInput):
    from database import salvar_medicao, adicionar_sensor
    from serial_reader import _inferir_regiao

    regiao = _inferir_regiao(medicao.sensor_id)
    adicionar_sensor(medicao.sensor_id, regiao)

    try:
        data_hora = datetime.fromisoformat(medicao.data_hora) if medicao.data_hora else datetime.now()
    except ValueError:
        data_hora = datetime.now()

    salvar_medicao(medicao.sensor_id, medicao.temperatura, medicao.umidade, data_hora)
    return {
        "status"   : "ok",
        "sensor_id": medicao.sensor_id,
        "regiao"   : regiao,
        "salvo_em" : data_hora.isoformat()
    }


@app.get("/ranking", summary="Ranking de regioes por HeatScore")
def ranking():
    from database import get_medicoes_por_regiao

    conn = sqlite3.connect("ilhas_calor.db")
    cur  = conn.cursor()
    cur.execute("SELECT nome FROM regioes")
    regioes = [r[0] for r in cur.fetchall()]
    conn.close()

    resultado = []
    for regiao in regioes:
        medicoes = get_medicoes_por_regiao(regiao)
        if not medicoes:
            continue
        temps  = [m[0] for m in medicoes]
        hs     = calcular_heatscore(temps)
        ultima = medicoes[0][2] if medicoes else None
        resultado.append({"regiao": regiao, "ultima_medicao": ultima, **hs})

    resultado.sort(key=lambda x: x["score"], reverse=True)
    return resultado


@app.get("/regiao/{nome}", summary="Detalhes de uma regiao")
def detalhes_regiao(nome: str):
    from database import get_medicoes_por_regiao

    medicoes = get_medicoes_por_regiao(nome)
    if not medicoes:
        raise HTTPException(status_code=404, detail=f"Regiao '{nome}' sem dados.")

    temps = [m[0] for m in medicoes]
    hs    = calcular_heatscore(temps)

    return {
        "regiao"        : nome,
        "heatscore"     : hs,
        "ultima_medicao": medicoes[0][2],
        "historico"     : [{"temperatura": m[0], "umidade": m[1], "data_hora": m[2]} for m in medicoes]
    }


@app.get("/regiao/{nome}/analise", summary="Analise de tendencia termica com regressao linear")
def analise_regiao(nome: str):
    from database import get_medicoes_por_regiao

    medicoes = get_medicoes_por_regiao(nome)
    if not medicoes:
        raise HTTPException(status_code=404, detail=f"Regiao '{nome}' sem dados.")

    tendencia = analisar_tendencia(medicoes)
    return {"regiao": nome, "analise": tendencia}


@app.get("/alertas", summary="Regioes em estado critico - HeatScore maior ou igual a 75")
def alertas():
    from database import get_medicoes_por_regiao

    conn = sqlite3.connect("ilhas_calor.db")
    cur  = conn.cursor()
    cur.execute("SELECT nome FROM regioes")
    regioes = [r[0] for r in cur.fetchall()]
    conn.close()

    criticas = []
    for regiao in regioes:
        medicoes = get_medicoes_por_regiao(regiao)
        if not medicoes:
            continue
        hs = calcular_heatscore([m[0] for m in medicoes])
        if hs["score"] >= 75:
            criticas.append({
                "regiao"        : regiao,
                "score"         : hs["score"],
                "classificacao" : hs["classificacao"],
                "media_temp"    : hs["media_temp"],
                "ultima_medicao": medicoes[0][2]
            })

    criticas.sort(key=lambda x: x["score"], reverse=True)
    return {"total": len(criticas), "alertas": criticas}


@app.get("/exportar/csv", summary="Exporta todas as medicoes em CSV usando Pandas")
def exportar_csv():
    from database import get_medicoes_por_regiao

    conn = sqlite3.connect("ilhas_calor.db")
    cur  = conn.cursor()
    cur.execute("SELECT nome FROM regioes")
    regioes = [r[0] for r in cur.fetchall()]
    conn.close()

    frames = []
    for regiao in regioes:
        medicoes = get_medicoes_por_regiao(regiao)
        if not medicoes:
            continue
        df = pd.DataFrame(list(medicoes), columns=["temperatura", "umidade", "data_hora"])
        df["regiao"] = regiao
        hs = calcular_heatscore(list(df["temperatura"]))
        df["heatscore"]     = hs["score"]
        df["classificacao"] = hs["classificacao"]
        frames.append(df)

    if not frames:
        raise HTTPException(status_code=404, detail="Nenhum dado disponivel.")

    df_final = pd.concat(frames).sort_values(["regiao", "data_hora"])
    df_final = df_final[["regiao", "data_hora", "temperatura", "umidade", "heatscore", "classificacao"]]

    stream = io.StringIO()
    df_final.to_csv(stream, index=False, encoding="utf-8")
    stream.seek(0)

    nome_arquivo = f"ilhas_calor_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"}
    )