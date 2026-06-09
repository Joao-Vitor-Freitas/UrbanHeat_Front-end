import pandas as pd
import numpy as np

def calcular_heatscore(temperaturas: list[float]) -> dict:
    if not temperaturas:
        return {
            "score": 0,
            "classificacao": "Baixa",
            "media_temp": 0.0,
            "percentual_critico": 0.0
        }

    # Pandas + NumPy substituindo o Python puro
    serie = pd.Series(temperaturas, dtype=float)

    media              = float(serie.mean())
    percentual_critico = float((serie > 35).mean() * 100)

    # Fórmula com NumPy
    score = float(np.clip(
        (media * 0.6) + (percentual_critico * 0.4),
        0, 100
    ))
    score = round(score)

    limites = [25, 50, 75]
    labels  = ["Baixa", "Moderada", "Alta", "Crítica"]
    classificacao = labels[int(np.searchsorted(limites, score, side="right"))]

    return {
        "score"              : score,
        "classificacao"      : classificacao,
        "media_temp"         : round(media, 1),
        "percentual_critico" : round(percentual_critico, 1)
    }