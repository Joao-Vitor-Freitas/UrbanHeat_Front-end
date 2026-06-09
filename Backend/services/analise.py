import pandas as pd
import numpy as np

def analisar_tendencia(medicoes: list[dict]) -> dict:
    """
    Usa regressão linear simples (NumPy) para prever
    a temperatura média nas próximas horas.
    """
    df = pd.DataFrame(list(medicoes), columns=['temperatura', 'umidade', 'data_hora'])
    df['temperatura'] = pd.to_numeric(df['temperatura'], errors='coerce')
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    df = df.sort_values('data_hora').tail(50)

    if len(df) < 5:
        return {"tendencia": "Dados insuficientes"}

    # Converte tempo para índice numérico
    x = np.arange(len(df))
    y = df['temperatura'].values

    # Regressão linear com NumPy
    coef = np.polyfit(x, y, deg=1)   # [inclinação, intercepto]
    inclinacao = coef[0]

    # Previsão para as próximas 3 "janelas"
    x_futuro   = np.array([len(df), len(df)+1, len(df)+2])
    y_previsto = np.polyval(coef, x_futuro)

    # Classifica tendência
    if inclinacao > 0.3:
        tendencia = "Aquecimento acelerado"
    elif inclinacao > 0.05:
        tendencia = "Aquecimento gradual"
    elif inclinacao < -0.05:
        tendencia = "Resfriamento"
    else:
        tendencia = "Estável"

    return {
        "tendencia"          : tendencia,
        "inclinacao"         : round(float(inclinacao), 4),
        "previsao_proximas"  : [round(float(t), 1) for t in y_previsto],
        "orientacao"         : _gerar_orientacao(tendencia)
    }

def _gerar_orientacao(tendencia: str) -> str:
    orientacoes = {
        "Aquecimento acelerado" : " Risco crítico. Priorizar arborização emergencial e alertar população.",
        "Aquecimento gradual"   : " Planejar intervenções verdes na região a médio prazo.",
        "Estável"               : " Região sob controle. Manter monitoramento.",
        "Resfriamento"          : " Tendência positiva. Avaliar eficácia das intervenções."
    }
    return orientacoes.get(tendencia, "Monitorar região.")