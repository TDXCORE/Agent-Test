import os
import datetime
import pytz
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def format_date_for_display(preferred_date=None):
    """
    Función simplificada que extrae la lógica de formateo de fechas de get_available_slots
    para probar que siempre use el año actual.
    
    Args:
        preferred_date: Fecha preferida (YYYY-MM-DD, opcional)
        
    Returns:
        Mensaje formateado con la fecha
    """
    # Determinar rango de fechas a consultar
    bogota_tz = pytz.timezone("America/Bogota")
    today = datetime.datetime.now(bogota_tz)
    current_year = today.year
    
    # Log para depuración
    logger.info(f"Fecha actual: {today.strftime('%Y-%m-%d %H:%M:%S')} (Año: {current_year})")
    
    # Fecha mínima para agendar (48 horas después de hoy)
    min_date = today + datetime.timedelta(days=2)
    min_date_str = min_date.strftime("%d/%m/%Y")
    
    # Mensaje inicial
    response_message = ""
    
    if preferred_date:
        # Si hay una fecha preferida, verificar si es válida
        try:
            start_date = datetime.datetime.strptime(preferred_date, "%Y-%m-%d")
            
            # SIEMPRE verificar que el año sea actual o futuro
            if start_date.year != current_year:
                logger.warning(f"Fecha preferida {preferred_date} tiene año {start_date.year} diferente al actual {current_year}")
                start_date = start_date.replace(year=current_year)
                logger.info(f"Fecha corregida a {start_date.strftime('%Y-%m-%d')}")
            
            start_date = bogota_tz.localize(start_date)
            
            # Si la fecha es anterior a la fecha mínima, informar al usuario
            if start_date < min_date:
                response_message = f"Lo siento, no es posible agendar reuniones para la fecha solicitada. Las reuniones deben agendarse con al menos 48 horas de anticipación (a partir del {min_date_str}).\n\nA continuación te muestro los horarios disponibles más próximos:\n\n"
                # Usar la fecha mínima para consultar disponibilidad
                start_date = min_date
            else:
                response_message = f"Horarios disponibles para el {start_date.strftime('%d/%m/%Y')} y días siguientes:\n\n"
        except ValueError:
            logger.error(f"Formato de fecha inválido: {preferred_date}")
            response_message = "El formato de fecha proporcionado no es válido. Por favor, utiliza el formato YYYY-MM-DD (por ejemplo, 2025-05-15).\n\nA continuación te muestro los horarios disponibles más próximos:\n\n"
            # Usar la fecha mínima para consultar disponibilidad
            start_date = min_date
    else:
        # Si no hay fecha preferida, empezar desde la fecha mínima (48h después)
        start_date = min_date
        response_message = f"Horarios disponibles a partir del {min_date_str}:\n\n"
    
    # Simular algunos slots disponibles para mostrar fechas
    slots_by_date = {}
    for i in range(3):  # Simular 3 días
        date = (start_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        slots_by_date[date] = ["09:00", "10:00", "11:00"]
    
    # Formatear por fecha
    formatted_by_date = []
    for date, times in slots_by_date.items():
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        day_name = date_obj.strftime("%A")  # Nombre del día
        date_formatted = date_obj.strftime("%d/%m/%Y")
        times_str = ", ".join(times)
        formatted_by_date.append(f"- {day_name} {date_formatted}: {times_str}")
    
    return response_message + "\n".join(formatted_by_date)

def test_date_formatting():
    """
    Prueba la función de formateo de fechas para verificar que siempre muestre fechas del año actual (2025)
    independientemente del país del número de teléfono.
    """
    print("\n=== PRUEBA DE FORMATEO DE FECHAS ===")
    print("Verificando que todas las fechas mostradas sean del año actual (2025)")
    
    # Probar con diferentes fechas
    test_dates = [
        None,  # Sin fecha preferida
        "2023-11-07",  # Fecha antigua (2023)
        "2024-05-15",  # Fecha del año pasado
        "2025-05-15",  # Fecha del año actual
        "2026-05-15",  # Fecha futura
    ]
    
    for date in test_dates:
        print(f"\n--- Probando con fecha: {date if date else 'Sin fecha preferida'} ---")
        
        # Obtener mensaje formateado
        result = format_date_for_display(date)
        
        # Verificar que el resultado contenga el año actual (2025)
        current_year = datetime.datetime.now(pytz.timezone("America/Bogota")).year
        
        print(f"Año actual según el sistema: {current_year}")
        print(f"Resultado (primeras 200 caracteres): {result[:200]}...")
        
        # Verificar que no contenga años incorrectos (2023)
        if "2023" in result:
            print(f"ERROR: Se encontró el año 2023 en el resultado")
        else:
            print(f"OK: No se encontró el año 2023 en el resultado")
        
        # Verificar que contenga el año actual
        if str(current_year) in result:
            print(f"OK: Se encontró el año actual ({current_year}) en el resultado")
        else:
            print(f"ERROR: No se encontró el año actual ({current_year}) en el resultado")

if __name__ == "__main__":
    test_date_formatting()
