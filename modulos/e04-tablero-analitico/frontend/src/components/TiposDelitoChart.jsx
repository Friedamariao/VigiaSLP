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
import { COLORES_DELITOS } from '../utils/catalogo';
import Disclaimer from './Disclaimer';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function TiposDelitoChart({ data }) {
  const chartData = useMemo(() => {
    if (!data || !data.tipos || data.tipos.length === 0) return null;

    const tipos = data.tipos;
    return {
      labels: tipos.map((t) => t.clave),
      datasets: [
        {
          label: 'Reportes por tipo',
          data: tipos.map((t) => t.total),
          backgroundColor: tipos.map((t) => COLORES_DELITOS[t.clave] || '#8ecae6'),
          borderRadius: 4,
        },
      ],
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title(items) {
            const idx = items[0]?.dataIndex;
            if (idx == null || !data?.tipos[idx]) return '';
            return data.tipos[idx].nombre;
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
        title: { display: true, text: 'Tipo de delito' },
      },
    },
  };

  if (!chartData) return <p>Sin datos por tipo de delito.</p>;

  return (
    <div className="chart-card">
      <h3>Reportes por tipo de delito</h3>
      <div className="chart-container">
        <Bar data={chartData} options={options} />
      </div>
      <Disclaimer />
    </div>
  );
}

export default TiposDelitoChart;
