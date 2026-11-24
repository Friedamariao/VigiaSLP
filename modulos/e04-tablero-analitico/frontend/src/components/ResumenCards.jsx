import React from 'react';
import Disclaimer from './Disclaimer';

function ResumenCards({ data }) {
  if (!data) return null;

  const cards = [
    {
      titulo: 'Total de reportes',
      valor: data.total_reportes.toLocaleString('es-MX'),
      icono: '#',
    },
    {
      titulo: 'Reportes esta semana',
      valor: data.reportes_semana.toLocaleString('es-MX'),
      icono: '7d',
    },
    {
      titulo: 'Tipo más frecuente',
      valor: `${data.tipo_mas_frecuente.clave} (${data.tipo_mas_frecuente.total})`,
      subtitulo: data.tipo_mas_frecuente.nombre,
      icono: '!',
    },
    {
      titulo: 'Mayor recurrencia',
      valor: data.colonia_mas_reportes.nombre,
      subtitulo: `${data.colonia_mas_reportes.total} reportes`,
      icono: 'M',
    },
  ];

  return (
    <section aria-label="Resumen de reportes">
      <div className="resumen-grid">
        {cards.map((card) => (
          <div key={card.titulo} className="resumen-card">
            <span className="resumen-icono">{card.icono}</span>
            <div>
              <p className="resumen-titulo">{card.titulo}</p>
              <p className="resumen-valor">{card.valor}</p>
              {card.subtitulo && <p className="resumen-subtitulo">{card.subtitulo}</p>}
            </div>
          </div>
        ))}
      </div>
      <Disclaimer />
    </section>
  );
}

export default ResumenCards;
