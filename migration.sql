-- Script para agregar campos necesarios en Supabase

-- 1. Agregar campo 'read' a la tabla messages
ALTER TABLE messages 
ADD COLUMN read BOOLEAN DEFAULT FALSE;

-- 2. Agregar campo 'agent_enabled' a la tabla conversations
ALTER TABLE conversations 
ADD COLUMN agent_enabled BOOLEAN DEFAULT TRUE;

-- 3. Crear índices para mejorar el rendimiento de las consultas
CREATE INDEX idx_messages_read ON messages(read);
CREATE INDEX idx_messages_conversation_read ON messages(conversation_id, read);
CREATE INDEX idx_conversations_agent_enabled ON conversations(agent_enabled);

-- 4. Actualizar mensajes existentes
-- Marcar todos los mensajes existentes del asistente y sistema como leídos
UPDATE messages 
SET read = TRUE 
WHERE role IN ('assistant', 'system');

-- 5. Marcar todos los mensajes existentes del usuario como no leídos
UPDATE messages 
SET read = FALSE 
WHERE role = 'user';

-- 6. Habilitar todas las conversaciones existentes para usar el agente
UPDATE conversations 
SET agent_enabled = TRUE;
