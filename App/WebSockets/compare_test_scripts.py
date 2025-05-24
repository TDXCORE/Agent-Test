"""
🔍 COMPARADOR DE SCRIPTS DE TESTING
==================================
Script para comparar las funcionalidades entre el script original
y el script enhanced de testing WebSocket.
"""

import os
import sys
from pathlib import Path

def print_header(title: str):
    """Imprime un header formateado."""
    print("\n" + "=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)

def print_section(title: str):
    """Imprime una sección formateada."""
    print(f"\n📋 {title}")
    print("-" * 60)

def analyze_file(file_path: str):
    """Analiza un archivo y extrae métricas básicas."""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Contar diferentes elementos
    classes = len([line for line in lines if line.strip().startswith('class ')])
    functions = len([line for line in lines if line.strip().startswith('def ')])
    async_functions = len([line for line in lines if 'async def' in line])
    imports = len([line for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')])
    comments = len([line for line in lines if line.strip().startswith('#')])
    docstrings = content.count('"""')
    
    # Buscar funcionalidades específicas
    has_logging = 'logging' in content
    has_traceback = 'traceback' in content
    has_dataclass = '@dataclass' in content
    has_retry_logic = 'retry' in content.lower()
    has_validation = 'validation' in content.lower()
    has_metrics = 'metrics' in content.lower()
    
    return {
        'file_size': len(content),
        'lines': len(lines),
        'classes': classes,
        'functions': functions,
        'async_functions': async_functions,
        'imports': imports,
        'comments': comments,
        'docstrings': docstrings // 2,  # Dividir por 2 porque cada docstring tiene apertura y cierre
        'has_logging': has_logging,
        'has_traceback': has_traceback,
        'has_dataclass': has_dataclass,
        'has_retry_logic': has_retry_logic,
        'has_validation': has_validation,
        'has_metrics': has_metrics
    }

def compare_scripts():
    """Compara los dos scripts de testing."""
    print_header("COMPARACIÓN DE SCRIPTS DE TESTING WEBSOCKET")
    
    # Rutas de los archivos
    original_path = "App/WebSockets/test_new_handlers.py"
    enhanced_path = "App/WebSockets/test_new_handlers_enhanced.py"
    
    # Analizar archivos
    original_stats = analyze_file(original_path)
    enhanced_stats = analyze_file(enhanced_path)
    
    if not original_stats:
        print(f"❌ No se pudo encontrar el archivo original: {original_path}")
        return
    
    if not enhanced_stats:
        print(f"❌ No se pudo encontrar el archivo enhanced: {enhanced_path}")
        return
    
    print_section("MÉTRICAS BÁSICAS")
    
    metrics = [
        ("Tamaño del archivo (caracteres)", "file_size"),
        ("Líneas de código", "lines"),
        ("Clases definidas", "classes"),
        ("Funciones totales", "functions"),
        ("Funciones async", "async_functions"),
        ("Imports", "imports"),
        ("Comentarios", "comments"),
        ("Docstrings", "docstrings")
    ]
    
    print(f"{'Métrica':<35} {'Original':<15} {'Enhanced':<15} {'Diferencia':<15}")
    print("-" * 80)
    
    for metric_name, metric_key in metrics:
        original_val = original_stats[metric_key]
        enhanced_val = enhanced_stats[metric_key]
        diff = enhanced_val - original_val
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        
        print(f"{metric_name:<35} {original_val:<15} {enhanced_val:<15} {diff_str:<15}")
    
    print_section("FUNCIONALIDADES AVANZADAS")
    
    features = [
        ("Sistema de Logging", "has_logging"),
        ("Stack Traces", "has_traceback"),
        ("Dataclasses", "has_dataclass"),
        ("Lógica de Retry", "has_retry_logic"),
        ("Validación de Datos", "has_validation"),
        ("Métricas Avanzadas", "has_metrics")
    ]
    
    print(f"{'Funcionalidad':<25} {'Original':<15} {'Enhanced':<15}")
    print("-" * 55)
    
    for feature_name, feature_key in features:
        original_has = "✅" if original_stats[feature_key] else "❌"
        enhanced_has = "✅" if enhanced_stats[feature_key] else "❌"
        
        print(f"{feature_name:<25} {original_has:<15} {enhanced_has:<15}")
    
    print_section("NUEVAS FUNCIONALIDADES EN ENHANCED")
    
    new_features = [
        "🚀 Logging detallado con timestamps precisos",
        "🔍 Stack traces completos para errores",
        "📊 Métricas avanzadas de rendimiento",
        "🌐 Información detallada de conexión WebSocket",
        "💾 Guardado automático de logs en archivos",
        "🎯 Validación de campos esperados vs recibidos",
        "📈 Scores de validación de datos (0-100%)",
        "🔄 Retry automático con backoff exponencial",
        "🖥️ Información completa del sistema",
        "📋 Análisis detallado de errores con categorización",
        "⏱️ Medición de latencia de red vs tiempo de servidor",
        "💻 Monitoreo de uso de memoria y CPU",
        "🔗 Estado detallado de conexiones WebSocket",
        "📁 Organización automática de logs por timestamp"
    ]
    
    for feature in new_features:
        print(f"  {feature}")
    
    print_section("RECOMENDACIONES DE USO")
    
    recommendations = [
        ("🔧 Desarrollo y debugging", "Enhanced", "Más información para identificar problemas"),
        ("🚀 Testing rápido", "Original", "Más simple y directo"),
        ("📊 Análisis de rendimiento", "Enhanced", "Métricas detalladas disponibles"),
        ("🐛 Solución de problemas", "Enhanced", "Stack traces y logging completo"),
        ("📈 Monitoreo de producción", "Enhanced", "Logs persistentes y métricas"),
        ("✅ Validación básica", "Original", "Suficiente para casos simples"),
        ("🔍 Investigación de errores", "Enhanced", "Información completa del contexto"),
        ("⚡ Ejecución automatizada", "Ambos", "Ambos soportan ejecución automática")
    ]
    
    print(f"{'Caso de Uso':<30} {'Recomendado':<15} {'Razón':<35}")
    print("-" * 80)
    
    for use_case, recommended, reason in recommendations:
        print(f"{use_case:<30} {recommended:<15} {reason:<35}")
    
    print_section("COMANDOS DE EJECUCIÓN")
    
    print("📝 Script Original:")
    print("   python App/WebSockets/test_new_handlers.py")
    print()
    print("🚀 Script Enhanced:")
    print("   python App/WebSockets/test_new_handlers_enhanced.py")
    print()
    print("📁 Logs Enhanced se guardan en:")
    print("   App/WebSockets/logs/websocket_test_YYYYMMDD_HHMMSS.log")
    
    print_section("PRÓXIMOS PASOS")
    
    next_steps = [
        "1. 🧪 Ejecutar ambos scripts para comparar resultados",
        "2. 📊 Revisar los logs detallados del script enhanced",
        "3. 🔍 Usar enhanced para debugging de problemas específicos",
        "4. 📈 Implementar métricas en dashboard de monitoreo",
        "5. 🔄 Configurar ejecución automática en CI/CD",
        "6. 📝 Documentar patrones de errores encontrados",
        "7. 🎯 Optimizar funciones basado en métricas de rendimiento"
    ]
    
    for step in next_steps:
        print(f"  {step}")
    
    print("\n" + "=" * 80)
    print("✅ Comparación completada. Ambos scripts están listos para usar.")
    print("📋 Consulta README_ENHANCED_TESTING.md para más detalles.")
    print("=" * 80)

if __name__ == "__main__":
    try:
        compare_scripts()
    except Exception as e:
        print(f"❌ Error durante la comparación: {str(e)}")
        import traceback
        traceback.print_exc()
