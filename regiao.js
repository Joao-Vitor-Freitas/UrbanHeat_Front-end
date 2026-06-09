const API_URL = 'http://127.0.0.1:8000';
const urlParams = new URLSearchParams(window.location.search);
const regionId = urlParams.get('id');

const classMap = {
  'Low': 'baixa',
  'Moderate': 'moderada',
  'High': 'alta',
  'Critical': 'critica'
};

let tChart = null;
let hChart = null;

function linearRegression(y) {
  let n = y.length;
  if (n === 0) return { slope: 0, intercept: 0 };
  let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
  for (let i = 0; i < n; i++) {
    sumX += i; sumY += y[i];
    sumXY += i * y[i]; sumXX += i * i;
  }
  let slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  let intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

async function loadRegionData() {
  if (!regionId) {
    document.getElementById('region-name').innerText = "Região não selecionada";
    return;
  }

  try {
    const [dashRes, rankRes, histRes] = await Promise.all([
      fetch(`${API_URL}/dashboard/`),
      fetch(`${API_URL}/heatscore/ranking`),
      fetch(`${API_URL}/reports/history/${regionId}`)
    ]);

    const dashboard = await dashRes.json();
    const ranking = await rankRes.json();
    const history = await histRes.json();

    const regionDash = dashboard.find(r => r.region_id == regionId);
    const regionRank = ranking.find(r => r.region_id == regionId);

    if (regionDash) document.getElementById('region-name').innerText = regionDash.region_name;

    if (regionRank) {
      const cls = classMap[regionRank.classification] || 'baixa';
      document.getElementById('heatscore-val').innerText = regionRank.score.toFixed(1);
      document.getElementById('heatscore-val').className = `heatscore-num score-${cls}`;
      document.getElementById('hs-circle').style.borderColor = `var(--accent-${cls === 'critica' ? 'red' : cls === 'alta' ? 'orange' : cls === 'moderada' ? 'yellow' : 'green'})`;
      document.getElementById('hs-class').innerText = regionRank.classification;

      document.getElementById('temp-val').innerText = regionRank.average_temperature.toFixed(1);
      document.getElementById('freq-val').innerText = (regionRank.high_temperature_frequency * 100).toFixed(1);
      document.getElementById('dur-val').innerText = (regionRank.critical_duration * 100).toFixed(1);
    }

    if (history.length > 0) {
      history.reverse();
      const labels = history.map(h => new Date(h.created_at).toLocaleTimeString('pt-BR'));
      const temps = history.map(h => h.temperature);
      const hums = history.map(h => h.humidity);

      document.getElementById('hum-val').innerText = hums[hums.length - 1].toFixed(1);

      const reg = linearRegression(temps);
      const slope = reg.slope;

      let trendTxt = "Estável";
      let trendDesc = "As variações de temperatura estão dentro da normalidade estatística.";
      if (slope > 0.3) { trendTxt = "Aquecimento Acelerado ↗"; trendDesc = "Alerta: O modelo indica aumento rápido de temperatura. Risco elevado de estresse térmico."; }
      else if (slope > 0.05) { trendTxt = "Aquecimento Gradual ↗"; trendDesc = "A região apresenta acúmulo gradual de calor. Monitoramento recomendado."; }
      else if (slope < -0.05) { trendTxt = "Resfriamento ↘"; trendDesc = "Tendência de queda na temperatura da região nas últimas medições."; }

      document.getElementById('trend-val').innerText = trendTxt;
      document.getElementById('trend-desc').innerText = trendDesc;

      const forecastHtml = [1, 2, 3].map(step => {
        const nextTemp = reg.intercept + (reg.slope * (temps.length - 1 + step));
        return `
          <div class="previsao-item">
            <div class="previsao-slot">T+${step}</div>
            <div class="previsao-temp">${nextTemp.toFixed(1)}°C</div>
          </div>
        `;
      }).join('');
      document.getElementById('forecast-list').innerHTML = forecastHtml;

      const trendData = temps.map((_, i) => reg.intercept + (reg.slope * i));

      if (tChart) tChart.destroy();
      tChart = new Chart(document.getElementById('tempChart'), {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            { label: 'Temp Real', data: temps, borderColor: '#ff6b35', backgroundColor: '#ff6b3533', fill: true, tension: 0.4 },
            { label: 'Tendência', data: trendData, borderColor: '#00b4ff', borderDash: [5, 5], pointRadius: 0, tension: 0 }
          ]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { grid: { color: '#0e4a7a55' }, ticks: { color: '#7aaecf' } }, x: { display: false } }, plugins: { legend: { labels: { color: '#e8f4ff' } } } }
      });

      if (hChart) hChart.destroy();
      hChart = new Chart(document.getElementById('humChart'), {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{ label: 'Umidade', data: hums, borderColor: '#00ffe7', backgroundColor: '#00ffe733', fill: true, tension: 0.4 }]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { grid: { color: '#0e4a7a55' }, ticks: { color: '#7aaecf' } }, x: { display: false } }, plugins: { legend: { display: false } } }
      });
    }
  } catch (err) {
    console.error("Erro ao carregar dados da região:", err);
  }
}

loadRegionData();
setInterval(loadRegionData, 30000);
