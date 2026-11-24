# E04 - Tablero analítico de incidencia y zonas recurrentes

Módulo de analítica del proyecto VigíaSLP. Presenta tendencias de reportes ciudadanos, zonas con mayor recurrencia, desglose por tipo de delito y comparativo con cifras oficiales del SESNSP.

## Estructura

```
e04-tablero-analitico/
├── backend/          # FastAPI: endpoints de analítica
│   ├── routers/      # Router /api/v1/analitica
│   ├── schemas/      # Modelos Pydantic
│   ├── services/     # Lógica de negocio
│   └── mock_data.py  # Datos sintéticos para desarrollo
├── frontend/         # React + Vite + Chart.js
│   ├── src/
│   │   ├── api/          # Cliente HTTP
│   │   ├── components/   # Dashboard, gráficas, filtros
│   │   └── utils/        # Catálogo de delitos
│   └── tests/
├── tests/            # Pruebas backend (pytest)
├── docs/             # Contrato OpenAPI
├── Dockerfile
└── docker-compose.yml
```

## Levantar en desarrollo

### Backend

```bash
cd modulos/e04-tablero-analitico
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8004
```

### Frontend

```bash
cd modulos/e04-tablero-analitico/frontend
npm install
npm run dev
```

Abre http://localhost:5174. El proxy de Vite redirige `/api` al backend en el puerto 8004.

### Docker Compose

```bash
cd modulos/e04-tablero-analitico
docker compose up --build
```

## Ejecutar pruebas

### Backend

```bash
cd modulos/e04-tablero-analitico
pytest tests/ -v
```

### Frontend

```bash
cd modulos/e04-tablero-analitico/frontend
npm test
```

## Endpoints

| Ruta | Descripción |
|------|-------------|
| `GET /api/v1/analitica/tendencias` | Serie temporal de reportes (dia/semana/mes) |
| `GET /api/v1/analitica/hotspots` | Zonas con mayor recurrencia de reportes |
| `GET /api/v1/analitica/comparativo` | Reportes ciudadanos vs cifra oficial SESNSP |
| `GET /api/v1/analitica/resumen` | Métricas resumidas para tarjetas |
| `GET /api/v1/analitica/tipos-delito` | Desglose por tipo de delito |

Todos los endpoints aceptan filtros: `tipo_delito`, `fecha_inicio`, `fecha_fin`, `colonia`, `ageb`.

## Reglas de negocio

- El tipo VFS (violencia familiar o sexual) se excluye de toda salida.
- Solo se muestran reportes validados por E08.
- Las ubicaciones se agregan por colonia/AGEB; nunca se expone la ubicación exacta.
- Colonias con menos de 3 reportes no aparecen en hotspots.
- Toda gráfica incluye: "Datos de reportes ciudadanos; no constituyen una cifra oficial."
- El comparativo oficial es municipal y mensual (nivel del SESNSP).

## Dependencias entre equipos

- **Dependemos de:** E01 (API central), E05 (datos SESNSP/INEGI), E08 (validación)
- **Entregamos a:** E03 (hotspots para mapa), E07 (recurrencia para alertas Telegram)
