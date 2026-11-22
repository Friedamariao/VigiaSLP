# VigíaSLP

Plataforma ciudadana de mapeo delictivo colaborativo para San Luis Potosí. Proyecto final de Ingeniería de Software II (UPSLP).

> Los reportes ciudadanos **no son cifras oficiales** y la plataforma **no sustituye al 911 ni al 089**.

## Estructura

| Carpeta | Contenido |
|---|---|
| `modulos/` | Una carpeta por equipo (E01 a E10) |
| `api/` | API central FastAPI (E01) |
| `db/` | Esquema, migraciones y datos semilla sintéticos |
| `docs/` | Requerimientos, arquitectura, planeación e interfaces |
| `scripts/` | Utilidades del repositorio |
| `.github/` | Plantillas de issues y pull requests, CODEOWNERS y CI |

## Equipos y ramas

| Equipo | Módulo | Rama |
|---|---|---|
| E01 | Arquitectura, API central y BD geoespacial | `feature/e01-arquitectura-api` |
| E02 | Portal web ciudadano | `feature/e02-portal-web` |
| E03 | Mapa interactivo | `feature/e03-mapa-interactivo` |
| E04 | Tablero analítico | `feature/e04-tablero-analitico` |
| E05 | Fuentes externas (ETL) | `feature/e05-fuentes-externas` |
| E06 | Bot de Telegram: reporte | `feature/e06-bot-reporte` |
| E07 | Bot de Telegram: consulta y alertas | `feature/e07-bot-consulta-alertas` |
| E08 | Panel de moderación | `feature/e08-moderacion` |
| E09 | Seguridad y privacidad | `feature/e09-seguridad-privacidad` |
| E10 | Calidad y pruebas | `feature/e10-calidad-pruebas` |

## Stack

Python 3.11+ con FastAPI, PostgreSQL 15+ con PostGIS, Docker Compose, React + Vite, python-telegram-bot v21+, OpenAPI 3 y GitHub Actions.

## Cómo ejecutar

```bash
cp .env.example .env      # ajustar valores locales; nunca subir .env
docker compose up
```

La API queda en `http://localhost:8000` y Swagger en `/docs`.

## Reglas clave

- Ningún cliente accede directamente a la base de datos: todo pasa por `/api/v1`.
- Solo datos sintéticos en pruebas; cero información personal.
- Sin secretos en el repositorio.

Más detalles en [CONTRIBUTING.md](CONTRIBUTING.md) y en `docs/`.
