def handler(request, context):
    """
    Maneja las solicitudes a la ruta raíz.
    
    Args:
        request: Objeto de solicitud HTTP
        context: Contexto de la función
        
    Returns:
        Respuesta HTTP
    """
    return {
        "statusCode": 200,
        "body": "Webhook para WhatsApp Business API. Usa /webhook para la verificación."
    }
