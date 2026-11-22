-- VigíaSLP · Esquema de base de datos (E01) · PostgreSQL 15+ con PostGIS
-- Coordenadas en WGS 84 (SRID 4326). Identificadores en español, snake_case, sin acentos.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE catalogo_version (
    version      text PRIMARY KEY,
    descripcion  text NOT NULL,
    vigente      boolean NOT NULL DEFAULT false,
    creada_en    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tipos_delito (
    id               serial PRIMARY KEY,
    codigo           text NOT NULL UNIQUE,
    categoria        text NOT NULL,
    tipo             text NOT NULL,
    subtipo          text NOT NULL,
    codigo_sesnsp    text,                       -- por homologar con E5 (PA-07)
    version_catalogo text NOT NULL REFERENCES catalogo_version(version),
    es_vfs           boolean NOT NULL DEFAULT false,
    publicable_mapa  boolean NOT NULL DEFAULT true,
    activo           boolean NOT NULL DEFAULT true,   -- baja lógica
    creado_en        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_vfs_no_publicable CHECK (NOT es_vfs OR publicable_mapa = false)
);

CREATE TABLE colonias (
    id      serial PRIMARY KEY,
    clave   text NOT NULL UNIQUE,
    nombre  text NOT NULL,
    ageb    text,
    fuente  text NOT NULL DEFAULT 'provisional',
    geom    geometry(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX idx_colonias_geom ON colonias USING gist (geom);

CREATE TABLE reportes (
    id               bigserial PRIMARY KEY,
    folio            text NOT NULL UNIQUE,
    tipo_delito_id   integer NOT NULL REFERENCES tipos_delito(id),
    descripcion      text,
    canal_origen     text NOT NULL DEFAULT 'web' CHECK (canal_origen IN ('web','telegram','ingesta')),
    fuente           text NOT NULL DEFAULT 'ciudadano',
    referencia_externa text,
    fecha_hecho      timestamptz NOT NULL,
    ubicacion        geometry(Point, 4326) NOT NULL,
    colonia_id       integer REFERENCES colonias(id),
    estado           text NOT NULL DEFAULT 'PENDIENTE',
    creado_en        timestamptz NOT NULL DEFAULT now(),
    actualizado_en   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_estado CHECK (estado IN ('PENDIENTE','PUBLICADO','RECHAZADO','DUPLICADO')),
    CONSTRAINT ck_longitud CHECK (ST_X(ubicacion) BETWEEN -180 AND 180 AND ST_Y(ubicacion) BETWEEN -90 AND 90)
);
-- Índices espaciales: geometría (bbox, polígono) y geografía (radio en metros).
CREATE INDEX idx_reportes_ubicacion      ON reportes USING gist (ubicacion);
CREATE INDEX idx_reportes_ubicacion_geog ON reportes USING gist ((ubicacion::geography));
CREATE UNIQUE INDEX uq_reportes_fuente_ref ON reportes (fuente, referencia_externa) WHERE referencia_externa IS NOT NULL;
CREATE INDEX idx_reportes_fecha          ON reportes (fecha_hecho);
CREATE INDEX idx_reportes_tipo           ON reportes (tipo_delito_id);
CREATE INDEX idx_reportes_colonia        ON reportes (colonia_id);
CREATE INDEX idx_reportes_estado         ON reportes (estado);

CREATE TABLE historial_estado_reporte (
    id               bigserial PRIMARY KEY,
    reporte_id       bigint NOT NULL REFERENCES reportes(id) ON DELETE CASCADE,
    estado_anterior  text,
    estado_nuevo     text NOT NULL,
    motivo           text,
    cambiado_en      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_historial_reporte ON historial_estado_reporte (reporte_id);
