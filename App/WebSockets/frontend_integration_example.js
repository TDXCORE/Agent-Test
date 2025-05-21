/**
 * Ejemplo de integración de WebSockets con frontend
 * 
 * Este archivo muestra cómo conectarse al servidor WebSocket desde una aplicación frontend
 * y realizar operaciones básicas como enviar solicitudes y recibir eventos.
 */

class WebSocketClient {
    /**
     * Cliente WebSocket para comunicarse con el servidor
     * @param {string} baseUrl - URL base del servidor (ej: "wss://waagentv1.onrender.com")
     * @param {string} token - Token JWT de autenticación (opcional)
     */
    constructor(baseUrl, token = null) {
        this.baseUrl = baseUrl;
        this.token = token;
        this.socket = null;
        this.isConnected = false;
        this.clientId = null;
        this.eventListeners = {};
        this.responseHandlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // 2 segundos
    }

    /**
     * Conecta al servidor WebSocket
     * @returns {Promise} Promesa que se resuelve cuando la conexión se establece
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                // Construir URL con token si está disponible
                let url = `${this.baseUrl}/ws`;
                if (this.token) {
                    url += `?token=${this.token}`;
                }

                console.log(`Conectando a ${url}...`);
                this.socket = new WebSocket(url);

                // Configurar manejadores de eventos
                this.socket.onopen = () => {
                    console.log('Conexión WebSocket establecida');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    resolve();
                };

                this.socket.onmessage = (event) => {
                    this._handleMessage(event.data);
                };

                this.socket.onclose = (event) => {
                    console.log(`Conexión WebSocket cerrada: ${event.code} ${event.reason}`);
                    this.isConnected = false;
                    this._attemptReconnect();
                    
                    // Disparar evento de desconexión
                    this._triggerEvent('disconnect', {
                        code: event.code,
                        reason: event.reason
                    });
                };

                this.socket.onerror = (error) => {
                    console.error('Error en WebSocket:', error);
                    reject(error);
                    
                    // Disparar evento de error
                    this._triggerEvent('error', {
                        error: error
                    });
                };
            } catch (error) {
                console.error('Error al conectar:', error);
                reject(error);
            }
        });
    }

    /**
     * Intenta reconectar al servidor
     * @private
     */
    _attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Intentando reconectar (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect()
                    .then(() => {
                        console.log('Reconexión exitosa');
                        this._triggerEvent('reconnect', {
                            attempt: this.reconnectAttempts
                        });
                    })
                    .catch((error) => {
                        console.error('Error al reconectar:', error);
                    });
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Máximo número de intentos de reconexión alcanzado');
            this._triggerEvent('reconnect_failed', {
                attempts: this.reconnectAttempts
            });
        }
    }

    /**
     * Maneja los mensajes recibidos del servidor
     * @param {string} data - Datos recibidos
     * @private
     */
    _handleMessage(data) {
        try {
            const message = JSON.parse(data);
            console.log('Mensaje recibido:', message);

            // Manejar mensaje de conexión inicial
            if (message.type === 'connected') {
                this.clientId = message.payload?.client_id;
                console.log(`ID de cliente asignado: ${this.clientId}`);
                this._triggerEvent('connect', message.payload);
                return;
            }

            // Manejar respuestas a solicitudes
            if (message.id && this.responseHandlers[message.id]) {
                const handler = this.responseHandlers[message.id];
                handler(message);
                delete this.responseHandlers[message.id];
                return;
            }

            // Manejar eventos
            if (message.type === 'event') {
                this._triggerEvent(message.event, message.payload);
                return;
            }

            // Manejar heartbeat
            if (message.type === 'heartbeat') {
                this._triggerEvent('heartbeat', message.payload);
                return;
            }

            // Otros mensajes
            this._triggerEvent('message', message);
        } catch (error) {
            console.error('Error al procesar mensaje:', error, data);
        }
    }

    /**
     * Dispara un evento para los listeners registrados
     * @param {string} event - Nombre del evento
     * @param {object} data - Datos del evento
     * @private
     */
    _triggerEvent(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error en listener de evento ${event}:`, error);
                }
            });
        }
    }

    /**
     * Genera un ID único para las solicitudes
     * @returns {string} ID único
     * @private
     */
    _generateId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Envía una solicitud al servidor
     * @param {string} resource - Recurso solicitado (conversations, messages, users)
     * @param {string} action - Acción a realizar (get, get_all, create, update, delete)
     * @param {object} data - Datos de la solicitud
     * @returns {Promise} Promesa que se resuelve con la respuesta del servidor
     */
    request(resource, action, data = {}) {
        return new Promise((resolve, reject) => {
            if (!this.isConnected) {
                reject(new Error('No conectado al servidor WebSocket'));
                return;
            }

            const id = this._generateId();
            const request = {
                type: 'request',
                id: id,
                resource: resource,
                payload: {
                    action: action,
                    ...data
                }
            };

            // Registrar handler para la respuesta
            this.responseHandlers[id] = (response) => {
                if (response.type === 'error') {
                    reject(new Error(response.payload?.message || 'Error desconocido'));
                } else {
                    resolve(response.payload);
                }
            };

            // Enviar solicitud
            console.log('Enviando solicitud:', request);
            this.socket.send(JSON.stringify(request));
        });
    }

    /**
     * Cierra la conexión WebSocket
     */
    disconnect() {
        if (this.socket && this.isConnected) {
            this.socket.close();
            this.isConnected = false;
            console.log('Conexión WebSocket cerrada');
        }
    }

    /**
     * Registra un listener para un evento
     * @param {string} event - Nombre del evento
     * @param {function} callback - Función a llamar cuando ocurra el evento
     * @returns {function} Función para eliminar el listener
     */
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);

        // Devolver función para eliminar el listener
        return () => {
            this.off(event, callback);
        };
    }

    /**
     * Elimina un listener para un evento
     * @param {string} event - Nombre del evento
     * @param {function} callback - Función a eliminar
     */
    off(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
        }
    }

    /**
     * Obtiene todas las conversaciones de un usuario
     * @param {string} userId - ID del usuario
     * @returns {Promise} Promesa que se resuelve con las conversaciones
     */
    getConversations(userId) {
        return this.request('conversations', 'get_all', { user_id: userId });
    }

    /**
     * Obtiene una conversación específica
     * @param {string} conversationId - ID de la conversación
     * @returns {Promise} Promesa que se resuelve con la conversación
     */
    getConversation(conversationId) {
        return this.request('conversations', 'get', { conversation_id: conversationId });
    }

    /**
     * Crea una nueva conversación
     * @param {object} conversation - Datos de la conversación
     * @returns {Promise} Promesa que se resuelve con la conversación creada
     */
    createConversation(conversation) {
        return this.request('conversations', 'create', { conversation });
    }

    /**
     * Obtiene los mensajes de una conversación
     * @param {string} conversationId - ID de la conversación
     * @returns {Promise} Promesa que se resuelve con los mensajes
     */
    getMessages(conversationId) {
        return this.request('messages', 'get_by_conversation', { conversation_id: conversationId });
    }

    /**
     * Envía un mensaje a una conversación
     * @param {string} conversationId - ID de la conversación
     * @param {string} content - Contenido del mensaje
     * @param {string} role - Rol del remitente (user, assistant)
     * @returns {Promise} Promesa que se resuelve con el mensaje creado
     */
    sendMessage(conversationId, content, role = 'user') {
        return this.request('messages', 'create', {
            message: {
                conversation_id: conversationId,
                content,
                role
            }
        });
    }

    /**
     * Obtiene información de un usuario
     * @param {string} userId - ID del usuario
     * @returns {Promise} Promesa que se resuelve con los datos del usuario
     */
    getUser(userId) {
        return this.request('users', 'get', { user_id: userId });
    }

    /**
     * Obtiene todos los usuarios
     * @returns {Promise} Promesa que se resuelve con la lista de usuarios
     */
    getUsers() {
        return this.request('users', 'get_all');
    }
}

// Ejemplo de uso
async function ejemploDeUso() {
    // Crear cliente WebSocket
    const client = new WebSocketClient('wss://waagentv1.onrender.com');

    // Registrar listeners para eventos
    client.on('connect', (data) => {
        console.log('Conectado al servidor:', data);
    });

    client.on('disconnect', (data) => {
        console.log('Desconectado del servidor:', data);
    });

    client.on('error', (data) => {
        console.error('Error en WebSocket:', data);
    });

    client.on('new_message', (data) => {
        console.log('Nuevo mensaje recibido:', data);
        // Aquí podrías actualizar la UI con el nuevo mensaje
    });

    client.on('message_deleted', (data) => {
        console.log('Mensaje eliminado:', data);
        // Aquí podrías eliminar el mensaje de la UI
    });

    client.on('conversation_updated', (data) => {
        console.log('Conversación actualizada:', data);
        // Aquí podrías actualizar la UI con los cambios en la conversación
    });

    try {
        // Conectar al servidor
        await client.connect();

        // Obtener conversaciones del usuario
        const userId = 'user-123'; // Reemplazar con el ID real del usuario
        const conversationsResult = await client.getConversations(userId);
        console.log('Conversaciones:', conversationsResult.conversations);

        // Crear una nueva conversación
        const newConversation = await client.createConversation({
            title: 'Nueva conversación',
            created_by: userId
        });
        console.log('Nueva conversación creada:', newConversation.conversation);

        // Enviar un mensaje a la conversación
        const conversationId = newConversation.conversation.id;
        const messageResult = await client.sendMessage(
            conversationId,
            'Hola, este es un mensaje de prueba'
        );
        console.log('Mensaje enviado:', messageResult.message);

        // Obtener mensajes de la conversación
        const messagesResult = await client.getMessages(conversationId);
        console.log('Mensajes:', messagesResult.messages);

        // Desconectar cuando ya no se necesite
        // client.disconnect();
    } catch (error) {
        console.error('Error en el ejemplo:', error);
    }
}

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WebSocketClient };
} else {
    // Para uso en navegador
    window.WebSocketClient = WebSocketClient;
}
