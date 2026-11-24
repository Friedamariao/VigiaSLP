import React, { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import Disclaimer from './Disclaimer';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function TendenciasChart({ data }) {
  const chartData = useMemo(() => {
    if (!data || !data.datos || data.datos.length === 0) return null;

    return {
      labels: data.datos.map((d) => d.fecha),
      datasets: [
        {
          label: 'Total de reportes',
          data: data.datos.map((d) => d.total),
          borderColor: '#457b9d',
          backgroundColor: 'rgba(69, 123, 157, 0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 3,
        },
      ],
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: false },
      tooltip: {
        callbacks: {
          afterBody(items) {
            const idx = items[0]?.dataIndex;
            if (idx == null || !data?.datos[idx]) return '';
            const porTipo = data.datos[idx].por_tipo;
            return Object.entries(porTipo)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 5)
              .map(([tipo, n]) => `  ${tipo}: ${n}`)
              .join('\n');
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Reportes' },
      },
      x: {
        title: { display: true, text: `Periodo (${data?.periodo || 'semana'})` },
      },
    },
  };

  if (!chartData) return <p>Sin datos de tendencias.</p>;

  return (
    <div className="chart-card">
      <h3>Tendencias de reportes</h3>
      <div className="chart-container">
        <Line data={chartData} options={options} />
      </div>
      <Disclaimer />
    </div>
  );
}

export default TendenciasChart;
