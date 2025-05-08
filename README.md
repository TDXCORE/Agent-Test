# Agente de Calificación de Leads con Integración MCP Outlook

Este proyecto implementa un agente conversacional para calificar leads de ventas, utilizando el framework BANT (Budget, Authority, Need, Timeline) y agendando citas automáticamente a través de la integración con Microsoft Outlook Calendar mediante MCP (Model Context Protocol).

## Características

- **Flujo completo de calificación de leads**:
  - Obtención de consentimiento GDPR/LPD
  - Recolección de datos personales
  - Cualificación BANT (Budget, Authority, Need, Timeline)
  - Levantamiento de requerimientos funcionales
  - Agendamiento de citas en Outlook

- **Integración MCP con Outlook Calendar**:
  - Verificación de disponibilidad
  - Agendamiento de reuniones online en Microsoft Teams
  - Manejo de errores y fallbacks

## Requisitos

- Python 3.8+
- Acceso a la API de OpenAI (GPT-4o)
- Cuenta de LangSmith (para trazabilidad y observabilidad)
- Configuración MCP para Outlook Calendar

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/lead-qualification-agent.git
   cd lead-qualification-agent
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con tus claves de API
   ```

4. Verificar la configuración MCP:
   - Asegúrate de que el archivo `cline_mcp_settings.json` esté correctamente configurado
   - Este archivo debe contener la configuración para el servidor MCP de Outlook Calendar

## Uso

### Modo Terminal Interactivo

Para ejecutar el agente en modo interactivo en la terminal:

```bash
python main.py
```

### Con LangGraph UI

Para ejecutar el agente con la interfaz gráfica de LangGraph:

```bash
langgraph dev
```

Luego accede a la UI en el navegador usando la URL proporcionada.

## Estructura del Proyecto

- `main.py`: Implementación principal del agente
- `src/agent/graph.py`: Configuración para LangGraph
- `requirements.txt`: Dependencias del proyecto
- `.env.example`: Plantilla para variables de entorno
- `langgraph.json`: Configuración para LangGraph
- `cline_mcp_settings.json`: Configuración MCP para Outlook Calendar

## Flujo de Conversación

1. **Inicio**: El agente se presenta y solicita consentimiento GDPR/LPD
2. **Datos Personales**: Recolecta nombre, empresa, correo y teléfono
3. **Cualificación BANT**:
   - Budget (Presupuesto)
   - Authority (Decisor)
   - Need (Necesidad)
   - Timing (Tiempo)
4. **Requerimientos**: Tipo de app, características, integraciones, etc.
5. **Agendamiento**: Consulta disponibilidad y agenda cita en Outlook

## Integración MCP

El agente utiliza la configuración MCP definida en `cline_mcp_settings.json` para conectarse al servidor MCP de Outlook Calendar. Las herramientas MCP utilizadas son:

- `microsoft_outlook_calendar-get-schedule`: Para consultar disponibilidad
- `microsoft_outlook_calendar-create-calendar-event`: Para agendar reuniones

## Desarrollo

### Añadir Nuevas Herramientas

Para añadir nuevas herramientas al agente:

1. Define la función de la herramienta con el decorador `@tool`
2. Añade la herramienta a la lista `tools` en la función `create_lead_qualification_agent()`
3. Actualiza el prompt del agente para incluir instrucciones sobre cómo usar la nueva herramienta

### Personalizar el Prompt

El prompt del agente se puede personalizar en la función `create_lead_qualification_agent()`. Asegúrate de incluir instrucciones claras sobre:

- El flujo de conversación
- Cómo usar las herramientas disponibles
- Manejo de errores y casos especiales

## Licencia

[MIT](LICENSE)
