import React from 'react';
import Dashboard from './components/Dashboard';
import EmergencyBanner from './components/EmergencyBanner';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>VigíaSLP</h1>
        <p className="app-subtitle">Tablero analítico de incidencia</p>
      </header>
      <EmergencyBanner />
      <main>
        <Dashboard />
      </main>
      <footer className="app-footer">
        <p>Datos de reportes ciudadanos; no constituyen una cifra oficial.</p>
      </footer>
    </div>
  );
}

export default App;
