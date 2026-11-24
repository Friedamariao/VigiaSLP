import React, { useMemo } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import Disclaimer from './Disclaimer';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function ComparativoChart({ data }) {
  const chartData = useMemo(() => {
    if (!data || !data.datos || data.datos.length === 0) return null;

    return {
      labels: data.datos.map((d) => d.mes),
      datasets: [
        {
          label: 'Reportes ciudadanos',
          data: data.datos.map((d) => d.ciudadano),
          backgroundColor: '#457b9d',
          borderRadius: 4,
        },
        {
          label: 'Cifra oficial (SESNSP)',
          data: data.datos.map((d) => d.oficial),
          backgroundColor: '#e63946',
          borderRadius: 4,
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
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Incidentes' },
      },
      x: {
        title: { display: true, text: 'Mes' },
      },
    },
  };

  if (!chartData) return <p>Sin datos comparativos.</p>;

  return (
    <div className="chart-card">
      <h3>Comparativo: reportes ciudadanos vs cifra oficial</h3>
      <p className="chart-nota">{data.nota}</p>
      <div className="chart-container">
        <Bar data={chartData} options={options} />
      </div>
      <Disclaimer />
    </div>
  );
}

export default ComparativoChart;
