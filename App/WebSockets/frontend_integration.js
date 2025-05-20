/**
 * Integración del cliente WebSocket en el frontend.
 * 
 * Este archivo muestra cómo integrar el cliente WebSocket en una aplicación
 * frontend basada en React/Next.js, similar a la estructura del proyecto
 * FullStackAgent2025.
 */

// Clase WebSocketClient para el frontend
class WebSocketClient {
  constructor(url, token) {
    this.url = url;
    this.token = token;
    this.socket = null;
    this.connected = false;
    this.clientId = null;
    this.userId = null;
    
    // Callbacks
    this.onConnect = null;
    this.onDisconnect = null;
    this.onError = null;
    this.onMessage = null;
    
    // Callbacks específicos por tipo de evento
    this.eventHandlers = {};
    
    // Callbacks para respuestas a mensajes específicos
    this.responseHandlers = {};
    
    // Intentos de reconexión
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectTimeout = null;
    this.reconnectDelay = 1000; // Comienza con 1 segundo
  }
  
  connect() {
    // Construir URL con token si está disponible
    let fullUrl = this.url;
    if (this.token) {
      if (fullUrl.includes('?')) {
        fullUrl += `&token=${this.token}`;
      } else {
        fullUrl += `?token=${this.token}`;
      }
    }
    
    try {
      console.log(`Conectando a ${fullUrl}`);
      
      // Crear conexión WebSocket
      this.socket = new WebSocket(fullUrl);
      
      // Configurar eventos
      this.socket.onopen = (event) => {
        this.connected = true;
        this.reconnectAttempts = 0;
        console.log('Conexión WebSocket establecida');
      };
      
      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this._handleMessage(message);
        } catch (error) {
          console.error('Error al procesar mensaje:', error);
        }
      };
      
      this.socket.onclose = (event) => {
        this.connected = false;
        console.log(`Conexión WebSocket cerrada: ${event.code} ${event.reason}`);
        
        // Notificar desconexión
        if (this.onDisconnect) {
          this.onDisconnect({
            code: event.code,
            reason: event.reason,
            timestamp: new Date().toISOString()
          });
        }
        
        // Intentar reconectar si no fue un cierre limpio
        if (event.code !== 1000 && event.code !== 1001) {
          this._scheduleReconnect();
        }
      };
      
      this.socket.onerror = (error) => {
        console.error('Error en WebSocket:', error);
        
        if (this.onError) {
          this.onError({
            code: 'connection_error',
            message: 'Error en la conexión WebSocket'
          });
        }
      };
    } catch (error) {
      console.error('Error al conectar:', error);
      
      if (this.onError) {
        this.onError({
          code: 'connection_error',
          message: `Error al conectar: ${error.message}`
        });
      }
    }
  }
  
  disconnect() {
    if (!this.connected || !this.socket) {
      return;
    }
    
    try {
      // Cancelar cualquier intento de reconexión
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
      
      // Cerrar conexión
      this.socket.close(1000, 'Cierre normal');
      this.socket = null;
      this.connected = false;
      
      console.log('Desconectado');
    } catch (error) {
      console.error('Error al desconectar:', error);
    }
  }
  
  _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Máximo número de intentos de reconexión alcanzado');
      return;
    }
    
    // Incrementar contador y delay (backoff exponencial)
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Intentando reconectar en ${delay}ms (intento ${this.reconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }
  
  send(resource, action, data, callback) {
    if (!this.connected || !this.socket) {
      throw new Error('No conectado al servidor');
    }
    
    // Generar ID único para el mensaje
    const messageId = crypto.randomUUID ? crypto.randomUUID() : `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Construir mensaje
    const message = {
      type: 'request',
      id: messageId,
      resource: resource,
      payload: {
        action: action,
        ...data
      }
    };
    
    // Registrar callback para la respuesta si se proporcionó
    if (callback) {
      this.responseHandlers[messageId] = callback;
    }
    
    // Enviar mensaje
    this.socket.send(JSON.stringify(message));
    console.log('Mensaje enviado:', message);
    
    return messageId;
  }
  
  on(eventType, callback) {
    if (!this.eventHandlers[eventType]) {
      this.eventHandlers[eventType] = [];
    }
    
    this.eventHandlers[eventType].push(callback);
  }
  
  off(eventType, callback) {
    if (!this.eventHandlers[eventType]) {
      return;
    }
    
    if (!callback) {
      this.eventHandlers[eventType] = [];
    } else {
      this.eventHandlers[eventType] = this.eventHandlers[eventType].filter(cb => cb !== callback);
    }
  }
  
  _handleMessage(message) {
    const messageType = message.type;
    const messageId = message.id;
    const payload = message.payload || {};
    
    // Llamar al callback general si está definido
    if (this.onMessage) {
      this.onMessage(message);
    }
    
    // Manejar según tipo de mensaje
    if (messageType === 'connected') {
      this.clientId = payload.client_id;
      this.userId = payload.user_id;
      
      if (this.onConnect) {
        this.onConnect(payload);
      }
    } else if (messageType === 'error') {
      if (this.onError) {
        this.onError(payload);
      }
      
      // Si hay un callback registrado para este mensaje, llamarlo con el error
      if (messageId in this.responseHandlers) {
        const callback = this.responseHandlers[messageId];
        delete this.responseHandlers[messageId];
        callback(null, payload);
      }
    } else if (messageType === 'response') {
      // Si hay un callback registrado para este mensaje, llamarlo con la respuesta
      if (messageId in this.responseHandlers) {
        const callback = this.responseHandlers[messageId];
        delete this.responseHandlers[messageId];
        callback(payload, null);
      }
    } else if (messageType === 'event') {
      const eventType = payload.type;
      const eventData = payload.data || {};
      
      // Llamar a los callbacks registrados para este tipo de evento
      if (eventType && this.eventHandlers[eventType]) {
        for (const callback of this.eventHandlers[eventType]) {
          try {
            callback(eventData);
          } catch (error) {
            console.error(`Error en callback de evento ${eventType}:`, error);
          }
        }
      }
    }
  }
}

/**
 * Ejemplo de integración en un contexto React/Next.js
 */

// src/services/websocketService.js
export const createWebSocketClient = (token) => {
  // Determinar URL del WebSocket basada en el entorno
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
  const wsUrl = `${wsProtocol}://${baseUrl.replace(/^https?:\/\//, '')}/ws`;
  
  return new WebSocketClient(wsUrl, token);
};

// src/contexts/WebSocketContext.js
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { createWebSocketClient } from '../services/websocketService';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [client, setClient] = useState(null);
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    let wsClient = null;
    
    // Crear y conectar cliente WebSocket cuando el usuario está autenticado
    if (isAuthenticated && token) {
      wsClient = createWebSocketClient(token);
      
      wsClient.onConnect = (data) => {
        console.log('WebSocket conectado:', data);
        setConnected(true);
      };
      
      wsClient.onDisconnect = (data) => {
        console.log('WebSocket desconectado:', data);
        setConnected(false);
      };
      
      wsClient.onError = (error) => {
        console.error('Error en WebSocket:', error);
      };
      
      wsClient.connect();
      setClient(wsClient);
    }
    
    // Limpiar al desmontar
    return () => {
      if (wsClient) {
        wsClient.disconnect();
      }
    };
  }, [isAuthenticated, token]);
  
  return (
    <WebSocketContext.Provider value={{ client, connected }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);

// Ejemplo de uso en un componente
// src/components/ConversationList.js
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

const ConversationList = () => {
  const { client, connected } = useWebSocket();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Cargar conversaciones cuando el WebSocket está conectado
    if (connected && client) {
      setLoading(true);
      
      // Solicitar todas las conversaciones
      client.send('conversations', 'get_all', { user_id: 'current' }, (data, error) => {
        setLoading(false);
        
        if (error) {
          console.error('Error al cargar conversaciones:', error);
          return;
        }
        
        setConversations(data.conversations || []);
      });
      
      // Suscribirse a eventos de conversaciones
      const handleNewConversation = (conversation) => {
        setConversations(prev => [...prev, conversation]);
      };
      
      const handleConversationUpdated = (data) => {
        setConversations(prev => 
          prev.map(conv => 
            conv.id === data.conversation_id ? { ...conv, ...data.conversation } : conv
          )
        );
      };
      
      const handleConversationDeleted = (data) => {
        setConversations(prev => 
          prev.filter(conv => conv.id !== data.conversation_id)
        );
      };
      
      // Registrar listeners
      client.on('conversation_created', handleNewConversation);
      client.on('conversation_updated', handleConversationUpdated);
      client.on('conversation_deleted', handleConversationDeleted);
      
      // Limpiar al desmontar
      return () => {
        client.off('conversation_created', handleNewConversation);
        client.off('conversation_updated', handleConversationUpdated);
        client.off('conversation_deleted', handleConversationDeleted);
      };
    }
  }, [connected, client]);
  
  if (loading) {
    return <div>Cargando conversaciones...</div>;
  }
  
  return (
    <div>
      <h2>Conversaciones</h2>
      <ul>
        {conversations.map(conversation => (
          <li key={conversation.id}>
            {conversation.title || 'Sin título'}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ConversationList;
