# 🌡️ Monitor de Ilhas de Calor Urbanas

> Mapeamento térmico urbano para planejamento ambiental e redução de calor extremo.

**ODS 11** — Cidades e Comunidades Sustentáveis  
**ODS 13** — Ação Contra a Mudança Global do Clima

---

## 👥 Integrantes

| RM | Nome |
|----|------|
| RM 573865 | João Victor Sant'Ana Cortabitart |
| RM 574025 | João Victor Barbon Naymayer |
| RM 573678 | João Vitor Dutra de Freitas |

---

## 📋 Descrição da Solução

O **Monitor de Ilhas de Calor Urbanas** é um sistema completo de monitoramento climático em tempo real que recebe dados de sensores de temperatura e umidade (via Arduino/ESP32), processa e analisa os dados com Python (Pandas e NumPy) e disponibiliza os resultados em um dashboard web interativo com mapa térmico de Porto Alegre.

O sistema foi desenvolvido para apoiar gestores urbanos e pesquisadores na identificação de regiões com alta criticidade térmica, permitindo priorizar intervenções como arborização, pavimentação permeável e políticas públicas de mitigação de ilhas de calor.

---

## 🏗️ Arquitetura

```
[Arduino C/C++]
      │
      │  Serial USB (CSV) ou HTTP POST (ESP32 JSON)
      ▼
[serial_reader.py]  ←── detecta porta, parseia CSV e JSON
      │
      ▼
[FastAPI Backend]
 ├── database.py       → SQLite (regiões, sensores, medições)
 ├── heatscore.py      → Pandas + NumPy (HeatScore)
 ├── services/
 │   └── analise.py    → Regressão linear NumPy (previsão)
 └── api.py            → 7 endpoints REST
      │
      │  JSON via fetch
      ▼
[Dashboard HTML + CSS + JS]
 ├── index.html  → Ranking + alertas + simulador + exportar CSV
 ├── regiao.html → Detalhes + gráfico de tendência + previsão
 └── mapa.html   → Mapa interativo de Porto Alegre (Leaflet.js)
```

---

## 📁 Estrutura de Arquivos

```
GS/
├── Backend/
│   ├── api.py                # 7 endpoints FastAPI
│   ├── database.py           # Banco de dados SQLite
│   ├── heatscore.py          # HeatScore com Pandas + NumPy
│   ├── main.py               # Entry point (API + serial automático)
│   ├── models.py             # Dataclasses
│   ├── serial_reader.py      # Leitura Arduino (CSV e JSON)
│   ├── seed_mock_data.py     # Dados de teste com tendências reais
│   ├── requirements.txt      # Dependências
│   └── services/
│       ├── __init__.py
│       └── analise.py        # Regressão linear (NumPy polyfit)
│
└── Frontend/
    ├── index.html            # Dashboard principal
    ├── regiao.html           # Detalhe por região
    ├── mapa.html             # Mapa térmico interativo
    └── style.css             # Tema dark/light + responsivo
```

---

## ⚙️ Funcionalidades

### Backend — API REST

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/regioes` | GET | Lista regiões cadastradas |
| `/medicoes` | POST | Recebe medição via HTTP (ESP32 ou simulação) |
| `/ranking` | GET | Regiões ordenadas por HeatScore + timestamp |
| `/regiao/{nome}` | GET | Detalhes, HeatScore e histórico |
| `/regiao/{nome}/analise` | GET | Tendência, previsão e orientação de ação |
| `/alertas` | GET | Regiões com HeatScore ≥ 75 (criticidade máxima) |
| `/exportar/csv` | GET | Download CSV com todas as medições (Pandas) |

### Dashboard

- **Banner de alerta automático** quando alguma região atinge criticidade máxima
- **Toggle dark/light** com preferência salva no localStorage
- **Simulador de medição manual** — envia dados sem precisar do Arduino
- **Exportar CSV** — download direto dos dados processados pelo Pandas
- **Animação de números** — valores "contam" ao carregar
- **Timestamp de última leitura** — mostra há quanto tempo foi a última medição
- **Ranking com barra de intensidade** e badge colorido por criticidade
- **Atualização automática** a cada 30 segundos

### Página de Região

- HeatScore em destaque com cor dinâmica por criticidade
- 4 métricas: temperatura média, umidade, % acima de 35°C, total de medições
- **Gráfico de temperatura com 3 datasets**: histórico real, linha de tendência (regressão linear) e limiar crítico de 35°C
- Gráfico de umidade
- Painel de tendência com inclinação, classificação, orientação de ação e previsão das próximas 3 leituras

### Mapa Térmico (mapa.html)

- Mapa real de Porto Alegre com tiles escuros (CartoDB Dark)
- Círculos coloridos por zona com tamanho proporcional ao HeatScore
- 3 modos de visualização: **Temperatura**, **Umidade**, **HeatScore**
- Popup com todos os indicadores ao clicar na zona
- Painel lateral com dados da região selecionada
- Legenda dinâmica que muda conforme o modo

---

## 🧮 HeatScore — Metodologia

O HeatScore é um índice de 0 a 100 que representa a criticidade térmica de uma região.

**Fórmula:**
```
score = (temperatura_média × 0.6) + (percentual_crítico × 0.4)
```

**Classificação:**

| HeatScore | Criticidade |
|-----------|-------------|
| 0 – 24    | Baixa       |
| 25 – 49   | Moderada    |
| 50 – 74   | Alta        |
| 75 – 100  | Crítica     |

**Implementação com Pandas e NumPy:**
```python
serie              = pd.Series(temperaturas, dtype=float)
media              = float(serie.mean())
percentual_critico = float((serie > 35).mean() * 100)
score              = float(np.clip((media * 0.6) + (percentual_critico * 0.4), 0, 100))
classificacao      = labels[int(np.searchsorted([25, 50, 75], score, side='right'))]
```

---

## 📈 Análise de Tendência

Usa **regressão linear** (`numpy.polyfit`) sobre o histórico de temperaturas para prever as próximas leituras.

```python
coef       = np.polyfit(x, y, deg=1)   # [inclinação, intercepto]
inclinacao = coef[0]                    # °C por leitura
y_previsto = np.polyval(coef, x_futuro) # próximas 3 temperaturas
```

| Inclinação | Tendência |
|------------|-----------|
| > 0.3  | Aquecimento acelerado |
| > 0.05 | Aquecimento gradual |
| < -0.05 | Resfriamento |
| entre -0.05 e 0.05 | Estável |

---

## 📡 Comunicação com o Arduino

### Opção A — Serial USB (Arduino Uno/Mega/Nano)

```cpp
// Formato CSV: sensor_id,temperatura,umidade
Serial.print("S-NORTE-01");
Serial.print(",");
Serial.print(temperatura, 1);
Serial.print(",");
Serial.println(umidade, 1);
delay(5000);
```

### Opção B — Wi-Fi HTTP (ESP32)

```cpp
http.begin("http://SEU_IP:8000/medicoes");
http.addHeader("Content-Type", "application/json");
http.POST("{\"sensor_id\":\"S-NORTE-01\",\"temperatura\":38.5,\"umidade\":41.0}");
```

O `sensor_id` deve seguir o padrão `S-REGIAO-XX` para a região ser inferida automaticamente:

| sensor_id | Região |
|-----------|--------|
| S-NORTE-01 | Norte |
| S-SUL-01 | Sul |
| S-LESTE-01 | Leste |
| S-OESTE-01 | Oeste |

---

## 🚀 Instruções de Execução

### 1. Instalar dependências

```bash
cd Backend
pip install fastapi uvicorn pyserial pandas numpy
```

### 2. Gerar dados de teste

```bash
python seed_mock_data.py
```

Gera 24 medições por região com tendências reais:
- **Norte** — aquecimento acelerado (→ Crítico)
- **Leste** — aquecimento gradual (→ Alto)
- **Sul** — estável (→ Moderado)
- **Oeste** — resfriamento (→ Baixo)

### 3. Subir o servidor

**Sem Arduino:**
```bash
python -m uvicorn api:app --reload --port 8000
```

**Com Arduino:**
```bash
python main.py          # detecção automática de porta
python main.py COM3     # Windows — porta explícita
python main.py /dev/ttyUSB0  # Linux — porta explícita
```

### 4. Abrir o dashboard

No PyCharm: clique direito em `Frontend/index.html` → **Open In** → **Browser**

### 5. Testar a API

```
http://127.0.0.1:8000/docs
```

---

## 📦 Dependências

| Biblioteca | Uso |
|------------|-----|
| `fastapi` | Framework web REST |
| `uvicorn` | Servidor ASGI |
| `pandas` | Análise de dados, HeatScore, exportação CSV |
| `numpy` | Cálculos numéricos, regressão linear, classificação |
| `pyserial` | Leitura serial do Arduino |
| `sqlite3` | Banco de dados (built-in Python) |

---

## 📊 Benefícios Mensuráveis

- **Identificação objetiva de risco** — HeatScore transforma dados brutos em índice comparável
- **Priorização de intervenções** — ranking orienta gestores sobre onde agir primeiro
- **Detecção precoce** — regressão linear alerta aquecimento antes de atingir criticidade
- **Alerta automático** — banner dispara quando qualquer região atinge score ≥ 75
- **Rastreabilidade histórica** — todo histórico armazenado e exportável em CSV
- **Monitoramento contínuo** — atualização a cada leitura do sensor sem intervenção manual

---

## 🎨 Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.10+, FastAPI, SQLite |
| Análise | Pandas, NumPy |
| Hardware | Arduino C/C++ (Serial/Wi-Fi) |
| Frontend | HTML5, CSS3, JavaScript |
| Gráficos | Chart.js 4.4 |
| Mapa | Leaflet.js 1.9 + CartoDB Dark Tiles |
| Fontes | Orbitron + Exo 2 (Google Fonts) |

---

*Desenvolvido para a disciplina de Python — Global Solution 2026*
MDEOF
echo "OK README"