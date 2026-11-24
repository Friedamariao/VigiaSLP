import React from 'react';
import { CATALOGO_DELITOS } from '../utils/catalogo';
import './FiltrosPanel.css';

function FiltrosPanel({ filtros, onChange }) {
  function handleChange(campo, valor) {
    onChange({ ...filtros, [campo]: valor || '' });
  }

  return (
    <section className="filtros-panel" aria-label="Filtros">
      <h2 className="filtros-titulo">Filtros</h2>
      <div className="filtros-grid">
        <label className="filtro-grupo">
          <span>Tipo de delito</span>
          <select
            value={filtros.tipo_delito || ''}
            onChange={(e) => handleChange('tipo_delito', e.target.value)}
          >
            <option value="">Todos</option>
            {Object.entries(CATALOGO_DELITOS).map(([clave, nombre]) => (
              <option key={clave} value={clave}>{clave} - {nombre}</option>
            ))}
          </select>
        </label>
        <label className="filtro-grupo">
          <span>Fecha inicio</span>
          <input
            type="date"
            value={filtros.fecha_inicio || ''}
            onChange={(e) => handleChange('fecha_inicio', e.target.value)}
          />
        </label>
        <label className="filtro-grupo">
          <span>Fecha fin</span>
          <input
            type="date"
            value={filtros.fecha_fin || ''}
            onChange={(e) => handleChange('fecha_fin', e.target.value)}
          />
        </label>
        <label className="filtro-grupo">
          <span>Colonia</span>
          <input
            type="text"
            placeholder="Nombre de colonia"
            value={filtros.colonia || ''}
            onChange={(e) => handleChange('colonia', e.target.value)}
          />
        </label>
      </div>
    </section>
  );
}

export default FiltrosPanel;
