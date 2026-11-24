import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import App from '../src/App';

const mockResumen = {
  total_reportes: 500,
  reportes_semana: 12,
  tipo_mas_frecuente: { clave: 'RTR', nombre: 'Robo a transeúnte', total: 80 },
  colonia_mas_reportes: { nombre: 'Centro Histórico', total: 45 },
  tendencia: 'alza',
  disclaimer: 'Datos de reportes ciudadanos; no constituyen una cifra oficial.',
};

const mockTendencias = {
  periodo: 'semana',
  datos: [
    { fecha: '2026-10-05', total: 10, por_tipo: { RTR: 5, RCH: 3, DAN: 2 } },
    { fecha: '2026-10-12', total: 15, por_tipo: { RTR: 8, LES: 4, SOS: 3 } },
  ],
  disclaimer: 'Datos de reportes ciudadanos; no constituyen una cifra oficial.',
};

const mockTipos = {
  tipos: [
    { clave: 'RTR', nombre: 'Robo a transeúnte', total: 80 },
    { clave: 'RCH', nombre: 'Robo a casa habitación', total: 50 },
  ],
  disclaimer: 'Datos de reportes ciudadanos; no constituyen una cifra oficial.',
};

const mockHotspots = {
  hotspots: [
    { colonia: 'Centro Histórico', total_reportes: 45, tipos_frecuentes: ['RTR', 'RCH'], lat: 22.15, lng: -100.98 },
  ],
  disclaimer: 'Datos de reportes ciudadanos; no constituyen una cifra oficial.',
};

const mockComparativo = {
  datos: [
    { mes: '2026-10', ciudadano: 90, oficial: 60, tipo_delito: null },
  ],
  nota: 'El dato oficial del SESNSP es municipal y mensual.',
  disclaimer: 'Datos de reportes ciudadanos; no constituyen una cifra oficial.',
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn((url) => {
    let body = {};
    if (url.includes('/resumen')) body = mockResumen;
    else if (url.includes('/tendencias')) body = mockTendencias;
    else if (url.includes('/tipos-delito')) body = mockTipos;
    else if (url.includes('/hotspots')) body = mockHotspots;
    else if (url.includes('/comparativo')) body = mockComparativo;
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
  }));
});

describe('App', () => {
  it('muestra el título de la aplicación', () => {
    render(<App />);
    expect(screen.getByText('VigíaSLP')).toBeInTheDocument();
  });

  it('muestra los números de emergencia', () => {
    render(<App />);
    expect(screen.getByText('911')).toBeInTheDocument();
    expect(screen.getByText('089')).toBeInTheDocument();
  });

  it('muestra el disclaimer en el footer', () => {
    render(<App />);
    const disclaimers = screen.getAllByText(/no constituyen una cifra oficial/i);
    expect(disclaimers.length).toBeGreaterThan(0);
  });
});

describe('Dashboard', () => {
  it('carga y muestra las tarjetas de resumen', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('500')).toBeInTheDocument();
    });
  });

  it('muestra las secciones principales', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Tendencias de reportes')).toBeInTheDocument();
      expect(screen.getByText('Reportes por tipo de delito')).toBeInTheDocument();
      expect(screen.getByText(/Zonas con mayor recurrencia/)).toBeInTheDocument();
      expect(screen.getByText(/Comparativo/)).toBeInTheDocument();
    });
  });

  it('muestra la tabla de hotspots', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Colonia')).toBeInTheDocument();
    });
  });

  it('muestra los filtros', () => {
    render(<App />);
    expect(screen.getByText('Filtros')).toBeInTheDocument();
    expect(screen.getByText('Tipo de delito')).toBeInTheDocument();
  });
});
