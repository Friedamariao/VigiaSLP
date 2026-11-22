# Guía de contribución

## Flujo de ramas

- `main`: versión estable; solo recibe cambios desde `develop` mediante pull request.
- `develop`: integración de todos los equipos.
- `feature/eNN-<módulo>`: rama de cada equipo. Para trabajo puntual, crea ramas cortas desde la rama de tu equipo.

## Commits

Mensajes claros en español, en modo imperativo, con la historia relacionada. Ejemplos:

```
feat(api): agrega consulta por radio (HU-12)
fix(db): corrige índice GIST de reportes
docs: actualiza el contrato OpenAPI
```

Prefijos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

## Pull requests

1. Abre el PR hacia `develop` con la plantilla del repositorio.
2. Enlaza la historia de usuario (`Closes #NN`).
3. Pide revisión al menos a una persona distinta de quien escribió el código.
4. Se integra solo si el pipeline de CI pasa.

## Definición de Hecho

- Código en GitHub, en la rama del equipo, integrado por PR revisado.
- Pruebas unitarias en verde en CI, con cobertura mínima de 60 % del módulo.
- Sin secretos ni vulnerabilidades conocidas.
- Criterios de aceptación cumplidos y contrato OpenAPI actualizado.

## Cambios al contrato de la API

El contrato vive en `docs/interfaces/`. Un cambio requiere un issue, un PR y aviso a los equipos consumidores. La versión v1 se congela después del Avance 2.

## Seguridad y privacidad

- No subas contraseñas, tokens ni archivos `.env`.
- Usa únicamente datos sintéticos; nunca nombres, placas, rostros ni reportes reales.

## Convenciones

- Identificadores de base de datos y API en español, `snake_case` y sin acentos.
- Coordenadas en WGS 84 (EPSG:4326); en GeoJSON, orden longitud, latitud.
- Errores en formato `application/problem+json`.
