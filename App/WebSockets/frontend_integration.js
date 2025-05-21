/**
 * Cliente WebSocket para integración con el frontend.
 * Este archivo puede ser importado en aplicaciones React/Next.js para
 * establecer una conexión WebSocket con el servidor.
 */

/**
 * Crea un cliente WebSocket.
 * @param {string} token - Token de autenticación JWT.
 * @param {Object} options - Opciones de configuración.
 * @param {string} options.url - URL del servidor WebSocket (por defecto: basada en la URL actual).
 * @param {number} options.reconnectInterval - Intervalo de reconexión en ms (por defecto: 1000).
 * @param {number} options.maxReconnectAttempts - Número máximo de intentos de reconexión (por defecto: 5).
 * @param {number} options.reconnectBackoffMultiplier - Multiplicador para backoff exponencial (por defecto: 1.5).
 * @returns {Object} Cliente WebSocket.
 */
export function createWebSocketClient(token, options = {}) {
  // Opciones por defecto
  const defaultOptions = {
    url: getDefaultWebSocketUrl(),
    reconnectInterval: 1000,
    maxReconnectAttempts: 5,
    reconnectBackoffMultiplier: 1.5
  };

  // Combinar opciones
  const config = { ...defaultOptions, ...options };

  // Estado interno
  let socket = null;
  let isConnected = false;
  let reconnectAttempts = 0;
  let reconnectTimeout = null;
  let messageQueue = [];
  let eventListeners = {};
  let pendingRequests = {};

  // Callbacks personalizables
  const callbacks = {
    onConnect: () => {},
    onDisconnect: () => {},
    onError: () => {}
  };

  /**
   * Obtiene la URL del WebSocket basada en la URL actual.
   * @returns {string} URL del WebSocket.
   */
  function getDefaultWebSocketUrl() {
    if (typeof window === 'undefined') {
      return 'ws://localhost:8000/ws';
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
  }

  /**
   * Conecta al servidor WebSocket.
   */
  function connect() {
    if (socket) {
      return;
    }

    try {
      // Construir URL con token si se proporciona
      let url = config.url;
      if (token) {
        url += (url.includes('?') ? '&' : '?') + `token=${encodeURIComponent(token)}`;
      }

      // Crear conexión WebSocket
      socket = new WebSocket(url);

      // Configurar manejadores de eventos
      socket.onopen = handleOpen;
      socket.onclose = handleClose;
      socket.onmessage = handleMessage;
      socket.onerror = handleError;

      console.log(`Conectando a ${url}...`);
    } catch (error) {
      console.error('Error al crear conexión WebSocket:', error);
      scheduleReconnect();
    }
  }

  /**
   * Maneja el evento de apertura de conexión.
   */
  function handleOpen() {
    console.log('Conexión WebSocket establecida');
    isConnected = true;
    reconnectAttempts = 0;

    // Procesar mensajes en cola
    while (messageQueue.length > 0) {
      const message = messageQueue.shift();
      sendRaw(message);
    }

    // Notificar conexión
    callbacks.onConnect({
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Maneja el evento de cierre de conexión.
   * @param {Event} event - Evento de cierre.
   */
  function handleClose(event) {
    console.log(`Conexión WebSocket cerrada: ${event.code} - ${event.reason}`);
    isConnected = false;
    socket = null;

    // Notificar desconexión
    callbacks.onDisconnect({
      code: event.code,
      reason: event.reason,
      timestamp: new Date().toISOString()
    });

    // Rechazar todas las solicitudes pendientes
    Object.keys(pendingRequests).forEach(id => {
      const { reject } = pendingRequests[id];
      reject(new Error('Conexión cerrada'));
      delete pendingRequests[id];
    });

    // Intentar reconectar
    scheduleReconnect();
  }

  /**
   * Maneja el evento de mensaje recibido.
   * @param {MessageEvent} event - Evento de mensaje.
   */
  function handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      console.log('Mensaje recibido:', message);

      // Procesar según el tipo de mensaje
      switch (message.type) {
        case 'response':
          handleResponse(message);
          break;
        case 'event':
          handleEvent(message);
          break;
        case 'error':
          handleErrorMessage(message);
          break;
        case 'connected':
          // Mensaje de bienvenida, ya manejado por onOpen
          break;
        case 'heartbeat':
          // Heartbeat, no requiere acción especial
          break;
        default:
          console.warn('Tipo de mensaje desconocido:', message.type);
      }
    } catch (error) {
      console.error('Error al procesar mensaje:', error);
    }
  }

  /**
   * Maneja respuestas a solicitudes.
   * @param {Object} message - Mensaje de respuesta.
   */
  function handleResponse(message) {
    const requestId = message.id;
    if (requestId && pendingRequests[requestId]) {
      const { resolve } = pendingRequests[requestId];
      resolve(message.payload);
      delete pendingRequests[requestId];
    }
  }

  /**
   * Maneja eventos.
   * @param {Object} message - Mensaje de evento.
   */
  function handleEvent(message) {
    const eventType = message.payload?.type;
    if (eventType && eventListeners[eventType]) {
      // Notificar a todos los listeners de este tipo de evento
      eventListeners[eventType].forEach(listener => {
        try {
          listener(message.payload.data);
        } catch (error) {
          console.error(`Error en listener de evento ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Maneja mensajes de error.
   * @param {Object} message - Mensaje de error.
   */
  function handleErrorMessage(message) {
    const requestId = message.id;
    
    // Si es respuesta a una solicitud específica
    if (requestId && pendingRequests[requestId]) {
      const { reject } = pendingRequests[requestId];
      reject(new Error(message.payload.message || 'Error desconocido'));
      delete pendingRequests[requestId];
    }
    
    // Notificar error general
    callbacks.onError({
      code: message.payload.code,
      message: message.payload.message,
      details: message.payload.details,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Maneja errores de conexión.
   * @param {Event} event - Evento de error.
   */
  function handleError(event) {
    console.error('Error en conexión WebSocket:', event);
    
    // Notificar error
    callbacks.onError({
      message: 'Error de conexión WebSocket',
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Programa un intento de reconexión.
   */
  function scheduleReconnect() {
    // Limpiar timeout anterior si existe
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
    }

    // Verificar si se alcanzó el límite de intentos
    if (reconnectAttempts >= config.maxReconnectAttempts) {
      console.error(`Máximo número de intentos de reconexión (${config.maxReconnectAttempts}) alcanzado`);
      return;
    }

    // Calcular tiempo de espera con backoff exponencial
    const delay = config.reconnectInterval * Math.pow(config.reconnectBackoffMultiplier, reconnectAttempts);
    
    console.log(`Intentando reconectar en ${delay}ms (intento ${reconnectAttempts + 1}/${config.maxReconnectAttempts})`);
    
    // Programar reconexión
    reconnectTimeout = setTimeout(() => {
      reconnectAttempts++;
      connect();
    }, delay);
  }

  /**
   * Envía un mensaje raw al servidor.
   * @param {Object} message - Mensaje a enviar.
   * @returns {boolean} true si se envió, false si se encoló.
   */
  function sendRaw(message) {
    if (!isConnected) {
      messageQueue.push(message);
      return false;
    }

    try {
      socket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      messageQueue.push(message);
      return false;
    }
  }

  /**
   * Envía una solicitud al servidor y espera la respuesta.
   * @param {string} resource - Recurso solicitado (conversations, messages, users).
   * @param {string} action - Acción a realizar (get_all, get_by_id, create, update, delete).
   * @param {Object} data - Datos de la solicitud.
   * @param {Function} callback - Callback opcional para manejar la respuesta.
   * @returns {Promise} Promesa que se resuelve con la respuesta.
   */
  function send(resource, action, data = {}, callback = null) {
    return new Promise((resolve, reject) => {
      // Generar ID único para la solicitud
      const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      // Crear mensaje
      const message = {
        type: 'request',
        id: requestId,
        resource,
        payload: {
          action,
          ...data
        }
      };
      
      // Registrar solicitud pendiente
      pendingRequests[requestId] = { resolve, reject };
      
      // Enviar mensaje
      const sent = sendRaw(message);
      
      // Si se proporcionó callback, usarlo también
      if (callback && typeof callback === 'function') {
        // Envolver resolve/reject para llamar al callback
        pendingRequests[requestId] = {
          resolve: (data) => {
            resolve(data);
            callback(data, null);
          },
          reject: (error) => {
            reject(error);
            callback(null, error);
          }
        };
      }
      
      // Si no se pudo enviar y no se encoló, rechazar inmediatamente
      if (!sent && !isConnected && reconnectAttempts >= config.maxReconnectAttempts) {
        delete pendingRequests[requestId];
        const error = new Error('No se pudo enviar el mensaje: no hay conexión');
        if (callback) callback(null, error);
        reject(error);
      }
    });
  }

  /**
   * Registra un listener para un tipo de evento.
   * @param {string} eventType - Tipo de evento.
   * @param {Function} listener - Función listener.
   * @returns {Function} Función para eliminar el listener.
   */
  function on(eventType, listener) {
    if (!eventListeners[eventType]) {
      eventListeners[eventType] = [];
    }
    
    eventListeners[eventType].push(listener);
    
    // Devolver función para eliminar el listener
    return () => {
      eventListeners[eventType] = eventListeners[eventType].filter(l => l !== listener);
    };
  }

  /**
   * Elimina un listener para un tipo de evento.
   * @param {string} eventType - Tipo de evento.
   * @param {Function} listener - Función listener a eliminar.
   */
  function off(eventType, listener) {
    if (eventListeners[eventType]) {
      eventListeners[eventType] = eventListeners[eventType].filter(l => l !== listener);
    }
  }

  /**
   * Cierra la conexión WebSocket.
   */
  function disconnect() {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close(1000, 'Cierre normal');
    }
    
    // Limpiar timeout de reconexión
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    
    // Limpiar estado
    isConnected = false;
    socket = null;
    reconnectAttempts = 0;
    messageQueue = [];
    
    // Rechazar todas las solicitudes pendientes
    Object.keys(pendingRequests).forEach(id => {
      const { reject } = pendingRequests[id];
      reject(new Error('Conexión cerrada manualmente'));
      delete pendingRequests[id];
    });
  }

  // API pública
  return {
    connect,
    disconnect,
    send,
    on,
    off,
    
    // Getters
    get isConnected() { return isConnected; },
    
    // Setters para callbacks
    set onConnect(callback) { callbacks.onConnect = callback; },
    set onDisconnect(callback) { callbacks.onDisconnect = callback; },
    set onError(callback) { callbacks.onError = callback; }
  };
}

/**
 * Ejemplo de uso:
 * 
 * import { createWebSocketClient } from '../services/websocketService';
 * 
 * // Crear cliente
 * const client = createWebSocketClient('mi-token-jwt');
 * 
 * // Conectar
 * client.connect();
 * 
 * // Registrar callbacks
 * client.onConnect = (data) => {
 *   console.log('Conectado:', data);
 * };
 * 
 * // Solicitar datos
 * client.send('conversations', 'get_all', { user_id: 'user123' })
 *   .then(data => {
 *     console.log('Conversaciones:', data.conversations);
 *   })
 *   .catch(error => {
 *     console.error('Error:', error);
 *   });
 * 
 * // Suscribirse a eventos
 * const unsubscribe = client.on('new_message', (message) => {
 *   console.log('Nuevo mensaje:', message);
 * });
 * 
 * // Más tarde, desuscribirse
 * unsubscribe();
 * 
 * // O desconectar completamente
 * client.disconnect();
 */
