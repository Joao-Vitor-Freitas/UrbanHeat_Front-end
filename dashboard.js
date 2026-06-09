const API_URL = 'http://127.0.0.1:8000';
let chartInstance = null;

const classMap = {
  'Low': 'baixa',
  'Moderate': 'moderada',
  'High': 'alta',
  'Critical': 'critica'
};

const colorMap = {
  'Low': '#30d158',
  'Moderate': '#ffd60a',
  'High': '#ff6b35',
  'Critical': '#ff2d55'
};

async function loadDashboard() {
  try {
    const [dashRes, rankRes] = await Promise.all([
      fetch(`${API_URL}/dashboard/`),
      fetch(`${API_URL}/heatscore/ranking`)
    ]);

    const dashboard = await dashRes.json();
    const ranking = await rankRes.json();

    // Update Stats
    document.getElementById('total-regions').innerText = dashboard.length;

    let maxScore = 0;
    let maxRegion = '—';
    let criticalCount = 0;
    let lastTimestamp = 0;

    dashboard.forEach(d => {
      if (d.heatscore && d.heatscore.score > maxScore) {
        maxScore = d.heatscore.score;
        maxRegion = d.region_name;
      }
      if (d.heatscore && d.heatscore.classification === 'Critical') {
        criticalCount++;
      }
      if (d.last_measurement) {
        const ts = new Date(d.last_measurement).getTime();
        if (ts > lastTimestamp) lastTimestamp = ts;
      }
    });

    document.getElementById('highest-heatscore').innerText = maxScore.toFixed(1);
    document.getElementById('highest-heatscore-region').innerText = maxRegion;
    document.getElementById('critical-regions').innerText = criticalCount;

    if (lastTimestamp > 0) {
      const dt = new Date(lastTimestamp);
      document.getElementById('last-update').innerText = dt.toLocaleTimeString('pt-BR');
    }

    // Render Ranking
    const container = document.getElementById('ranking-container');
    container.innerHTML = `
      <div class="ranking-row header-row">
        <span>#</span>
        <span>Região</span>
        <span style="text-align: center;">Score</span>
        <span>Intensidade</span>
        <span style="text-align: center;">Nível</span>
      </div>
    `;

    const chartLabels = [];
    const chartData = [];
    const chartColors = [];

    ranking.forEach((r, index) => {
      const cls = classMap[r.classification] || 'baixa';
      const row = document.createElement('a');
      row.href = `regiao.html?id=${r.region_id}`;
      row.className = 'ranking-row';
      row.innerHTML = `
        <span class="rank-num ${index < 3 ? 'top' : ''}">${index + 1}</span>
        <span class="region-name">${r.region_name}</span>
        <span class="heat-score-val score-${cls}">${r.score.toFixed(1)}</span>
        <div class="heat-bar-wrap"><div class="heat-bar bar-${cls}" style="width: ${r.score}%"></div></div>
        <span class="badge badge-${cls}">${r.classification}</span>
      `;
      container.appendChild(row);

      chartLabels.push(r.region_name);
      chartData.push(r.score);
      chartColors.push(colorMap[r.classification]);
    });

    // Render Chart
    const ctx = document.getElementById('heatscoreChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: chartLabels,
        datasets: [{
          label: 'HeatScore',
          data: chartData,
          backgroundColor: chartColors,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: '#0e4a7a55' }, ticks: { color: '#7aaecf' } },
          x: { grid: { display: false }, ticks: { color: '#7aaecf' } }
        }
      }
    });

  } catch (err) {
    console.error('Erro ao carregar dados:', err);
  }
}

loadDashboard();
setInterval(loadDashboard, 30000);
