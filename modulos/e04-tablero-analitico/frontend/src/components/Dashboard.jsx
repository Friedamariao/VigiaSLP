import React, { useState, useEffect, useCallback } from 'react';
import FiltrosPanel from './FiltrosPanel';
import ResumenCards from './ResumenCards';
import TendenciasChart from './TendenciasChart';
import TiposDelitoChart from './TiposDelitoChart';
import HotspotsTable from './HotspotsTable';
import ComparativoChart from './ComparativoChart';
import {
  obtenerResumen,
  obtenerTendencias,
  obtenerTiposDelito,
  obtenerHotspots,
  obtenerComparativo,
} from '../api/analitica';
import './Dashboard.css';

function Dashboard() {
  const [filtros, setFiltros] = useState({
    tipo_delito: '',
    fecha_inicio: '',
    fecha_fin: '',
    colonia: '',
  });
  const [resumen, setResumen] = useState(null);
  const [tendencias, setTendencias] = useState(null);
  const [tiposDelito, setTiposDelito] = useState(null);
  const [hotspots, setHotspots] = useState(null);
  const [comparativo, setComparativo] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [res, tend, tipos, hots, comp] = await Promise.all([
        obtenerResumen(filtros),
        obtenerTendencias(filtros),
        obtenerTiposDelito(filtros),
        obtenerHotspots(filtros),
        obtenerComparativo(filtros),
      ]);
      setResumen(res);
      setTendencias(tend);
      setTiposDelito(tipos);
      setHotspots(hots);
      setComparativo(comp);
    } catch (err) {
      setError(`No se pudieron cargar los datos: ${err.message}`);
    } finally {
      setCargando(false);
    }
  }, [filtros]);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  return (
    <div className="dashboard">
      <FiltrosPanel filtros={filtros} onChange={setFiltros} />

      {error && <div className="dashboard-error" role="alert">{error}</div>}

      {cargando ? (
        <div className="dashboard-loading">Cargando datos...</div>
      ) : (
        <>
          <ResumenCards data={resumen} />

          <div className="dashboard-grid">
            <TendenciasChart data={tendencias} />
            <TiposDelitoChart data={tiposDelito} />
          </div>

          <div className="dashboard-grid">
            <HotspotsTable data={hotspots} />
            <ComparativoChart data={comparativo} />
          </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
