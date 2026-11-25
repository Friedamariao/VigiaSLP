-- Datos semilla SINTÉTICOS (sin información real ni personal).
-- Colonias PROVISIONALES: cuadrícula de 6x6 sobre la zona urbana de San Luis Potosí capital,
-- hasta que E5 entregue la cartografía normalizada (PA-06).
INSERT INTO colonias (clave, nombre, ageb, fuente, geom)
SELECT 'PROV-' || lpad((i*6+j+1)::text, 2, '0'),
       'Zona provisional ' || lpad((i*6+j+1)::text, 2, '0'),
       NULL, 'provisional',
       ST_Multi(ST_MakeEnvelope(-101.05 + j*0.025, 22.08 + i*0.02, -101.05 + (j+1)*0.025, 22.08 + (i+1)*0.02, 4326))
FROM generate_series(0,5) AS i, generate_series(0,5) AS j;

SELECT setseed(0.42);
INSERT INTO reportes (folio, tipo_delito_id, descripcion, fecha_hecho, ubicacion, estado)
SELECT 'VIG-2026-' || upper(substr(md5(n::text || 'semilla'), 1, 8)),
       t.id,
       'Reporte sintético de prueba #' || n,
       now() - (random() * interval '180 days'),
       ST_SetSRID(ST_MakePoint(-101.05 + random()*0.15, 22.08 + random()*0.12), 4326),
       CASE WHEN random() < 0.85 THEN 'PUBLICADO' ELSE 'PENDIENTE' END
FROM generate_series(1,500) AS n
JOIN LATERAL (SELECT id FROM tipos_delito WHERE publicable_mapa ORDER BY random() + n*0 LIMIT 1) t ON true;

UPDATE reportes r SET colonia_id = c.id FROM colonias c WHERE ST_Covers(c.geom, r.ubicacion);
