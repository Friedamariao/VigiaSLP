-- VigiaSLP E09: cuentas para autenticacion y RBAC.
-- Ejecutar una vez en bases ya creadas; el volumen existente no reprocesa scripts init.
CREATE TABLE IF NOT EXISTS usuarios (
    id BIGSERIAL PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('ciudadano', 'bot', 'moderador', 'ingesta', 'administrador')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_usuario_formato CHECK (usuario ~ '^[a-z0-9_.-]{3,50}$')
);

CREATE INDEX IF NOT EXISTS idx_usuarios_rol_activo ON usuarios (rol, activo);
