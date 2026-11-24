# CLAUDE.md — Equipo E04 (VigíaSLP, ISW2, UPSLP)

## Proyecto
Módulo de **Analítica de incidencia y tablero de zonas recurrentes**. Contexto completo en `docs/e04/referencia/` (planteamiento general y Avance 1).

## Reglas de trabajo
- Código completo, sin placeholders ni TODOs vacíos. Explícito, legible y mantenible; sin lógica obscura.
- Al editar archivos existentes, conserva todo el contenido original salvo lo que se actualiza.
- Trabaja solo en la rama `feature/e04-*` y en las carpetas de E04. No modifiques código de otros equipos; si necesitas un cambio ahí, descríbelo en un archivo de notas y avísame.
- **Commits y PR:** los hace el usuario con su identidad de git. No agregues líneas `Co-Authored-By`, `Claude-Session`, "Generated with Claude Code" ni ninguna mención a Claude en mensajes de commit, descripciones de PR ni en el código. No hagas `git push` ni abras PR sin que yo lo pida.
- Mensajes de commit en español, formato `tipo(e04): descripción` (feat, fix, test, docs, chore).
- Nunca subas secretos; usa `.env.example`. Datos de prueba siempre sintéticos.

## Reglas de negocio y ética (obligatorias)
- El tablero consume **solo** la API REST `/api/v1`; nunca la BD directamente.
- Todo cálculo y salida excluye el tipo **VFS** (violencia familiar o sexual).
- Se agrega por colonia/AGEB; nunca se expone ubicación exacta de un reporte. No mostrar celdas con menos de 3 reportes.
- Solo reportes con estado validado (E08).
- Cada gráfica y estadística muestra: "Datos de reportes ciudadanos; no constituyen una cifra oficial."
- El tablero muestra visibles el 911 (emergencias) y el 089 (denuncia anónima).
- El SESNSP es municipal y mensual: el comparativo oficial solo existe a ese nivel.
- Usar "zonas con mayor recurrencia de reportes", no "zonas peligrosas".
- Catálogo de delitos: RTR, RCH, RVE, RAP, RNE, RTP, LES, DAN, FRA, ACO, SOS, VFS.

## Stack
Python 3.11+ con FastAPI, PostgreSQL 15+ con PostGIS, React + Vite + Chart.js, pytest, Vitest, Docker Compose, GitHub Actions.
