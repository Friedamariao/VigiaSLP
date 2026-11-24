const BASE_URL = '/api/v1/analitica';

function buildParams(filtros) {
  const params = new URLSearchParams();
  if (filtros.tipo_delito) params.set('tipo_delito', filtros.tipo_delito);
  if (filtros.fecha_inicio) params.set('fecha_inicio', filtros.fecha_inicio);
  if (filtros.fecha_fin) params.set('fecha_fin', filtros.fecha_fin);
  if (filtros.colonia) params.set('colonia', filtros.colonia);
  if (filtros.ageb) params.set('ageb', filtros.ageb);
  return params.toString();
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function obtenerTendencias(filtros = {}, periodo = 'semana') {
  const params = buildParams(filtros);
  const sep = params ? '&' : '';
  return fetchJSON(`${BASE_URL}/tendencias?periodo=${periodo}${sep}${params}`);
}

export async function obtenerHotspots(filtros = {}, limite = 10) {
  const params = buildParams(filtros);
  const sep = params ? '&' : '';
  return fetchJSON(`${BASE_URL}/hotspots?limite=${limite}${sep}${params}`);
}

export async function obtenerComparativo(filtros = {}) {
  const params = buildParams(filtros);
  const q = params ? `?${params}` : '';
  return fetchJSON(`${BASE_URL}/comparativo${q}`);
}

export async function obtenerResumen(filtros = {}) {
  const params = buildParams(filtros);
  const q = params ? `?${params}` : '';
  return fetchJSON(`${BASE_URL}/resumen${q}`);
}

export async function obtenerTiposDelito(filtros = {}) {
  const params = buildParams(filtros);
  const q = params ? `?${params}` : '';
  return fetchJSON(`${BASE_URL}/tipos-delito${q}`);
}
