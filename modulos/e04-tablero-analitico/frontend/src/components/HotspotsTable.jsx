import React from 'react';
import Disclaimer from './Disclaimer';

function HotspotsTable({ data }) {
  if (!data || !data.hotspots || data.hotspots.length === 0) {
    return <p>Sin datos de zonas con mayor recurrencia.</p>;
  }

  return (
    <div className="chart-card">
      <h3>Zonas con mayor recurrencia de reportes</h3>
      <div className="table-wrapper">
        <table className="hotspots-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Colonia</th>
              <th>Reportes</th>
              <th>Tipos más frecuentes</th>
            </tr>
          </thead>
          <tbody>
            {data.hotspots.map((h, i) => (
              <tr key={h.colonia}>
                <td>{i + 1}</td>
                <td>{h.colonia}</td>
                <td className="num">{h.total_reportes}</td>
                <td>{h.tipos_frecuentes.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Disclaimer />
    </div>
  );
}

export default HotspotsTable;
