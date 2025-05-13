-- Habilitar extensión UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de usuarios
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR UNIQUE,
    email VARCHAR UNIQUE,
    full_name VARCHAR NOT NULL,
    company VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de conversaciones
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    platform VARCHAR NOT NULL,
    external_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(platform, external_id)
);

-- Tabla de mensajes
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR NOT NULL DEFAULT 'text',
    media_url VARCHAR,
    external_id VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de calificación de leads
CREATE TABLE lead_qualification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    consent BOOLEAN DEFAULT FALSE,
    current_step VARCHAR DEFAULT 'start',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de datos BANT
CREATE TABLE bant_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_qualification_id UUID REFERENCES lead_qualification(id) ON DELETE CASCADE,
    budget TEXT,
    authority TEXT,
    need TEXT,
    timeline TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de requerimientos
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_qualification_id UUID REFERENCES lead_qualification(id) ON DELETE CASCADE,
    app_type VARCHAR,
    deadline VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de características
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID REFERENCES requirements(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de integraciones
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID REFERENCES requirements(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de reuniones
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    lead_qualification_id UUID REFERENCES lead_qualification(id),
    outlook_meeting_id VARCHAR,
    subject VARCHAR NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'scheduled',
    online_meeting_url VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para mejorar el rendimiento
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_lead_qualification_user_id ON lead_qualification(user_id);
CREATE INDEX idx_lead_qualification_conversation_id ON lead_qualification(conversation_id);
CREATE INDEX idx_bant_data_lead_qualification_id ON bant_data(lead_qualification_id);
CREATE INDEX idx_requirements_lead_qualification_id ON requirements(lead_qualification_id);
CREATE INDEX idx_features_requirement_id ON features(requirement_id);
CREATE INDEX idx_integrations_requirement_id ON integrations(requirement_id);
CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_meetings_lead_qualification_id ON meetings(lead_qualification_id);

-- Habilitar RLS en todas las tablas
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_qualification ENABLE ROW LEVEL SECURITY;
ALTER TABLE bant_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE features ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

-- Crear políticas para el acceso a los datos
-- Estas políticas permiten acceso completo usando la clave de servicio

-- Política para usuarios
CREATE POLICY "Acceso completo con clave de servicio" ON users
    USING (auth.role() = 'service_role');

-- Política para conversaciones
CREATE POLICY "Acceso completo con clave de servicio" ON conversations
    USING (auth.role() = 'service_role');

-- Política para mensajes
CREATE POLICY "Acceso completo con clave de servicio" ON messages
    USING (auth.role() = 'service_role');

-- Política para calificación de leads
CREATE POLICY "Acceso completo con clave de servicio" ON lead_qualification
    USING (auth.role() = 'service_role');

-- Política para datos BANT
CREATE POLICY "Acceso completo con clave de servicio" ON bant_data
    USING (auth.role() = 'service_role');

-- Política para requerimientos
CREATE POLICY "Acceso completo con clave de servicio" ON requirements
    USING (auth.role() = 'service_role');

-- Política para características
CREATE POLICY "Acceso completo con clave de servicio" ON features
    USING (auth.role() = 'service_role');

-- Política para integraciones
CREATE POLICY "Acceso completo con clave de servicio" ON integrations
    USING (auth.role() = 'service_role');

-- Política para reuniones
CREATE POLICY "Acceso completo con clave de servicio" ON meetings
    USING (auth.role() = 'service_role');
