-- Completa la base local hasta 10,000 reportes SINTÉTICOS para la prueba de rendimiento (RNF: 500 ms p95).
-- Uso: docker compose exec -T db psql -U vigia -d vigiaslp -f - < scripts/inflar_reportes.sql
INSERT INTO reportes (folio, tipo_delito_id, descripcion, fecha_hecho, ubicacion, estado)
SELECT 'VIG-2026-' || upper(substr(md5(n::text || 'carga'), 1, 8)),
       (SELECT id FROM tipos_delito WHERE publicable_mapa ORDER BY id OFFSET (n % 26) LIMIT 1),
       'Reporte sintético de carga #' || n,
       now() - (random() * interval '365 days'),
       ST_SetSRID(ST_MakePoint(-101.05 + random()*0.15, 22.08 + random()*0.12), 4326),
       'PUBLICADO'
FROM generate_series(1, GREATEST(0, 10000 - (SELECT count(*) FROM reportes))::int) AS n
ON CONFLICT (folio) DO NOTHING;
UPDATE reportes r SET colonia_id = c.id FROM colonias c WHERE r.colonia_id IS NULL AND ST_Covers(c.geom, r.ubicacion);
ANALYZE reportes;
SELECT count(*) AS total_reportes FROM reportes;
