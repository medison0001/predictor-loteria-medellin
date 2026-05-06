"""
Aplicación Flask para el Predictor de Lotería de Medellín
Servidor web principal con todas las rutas y API endpoints
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime, date
import os
import json
import sys
import importlib

# Importar nuestros módulos
from modelos import crear_engine, crear_tablas, obtener_session, Resultado, inicializar_pesos_por_defecto
from cargador_datos import cargar_csv_a_db, verificar_integridad_datos
from aprendizaje import procesar_nuevo_resultado, obtener_estadisticas, obtener_ultima_retroalimentacion

# Crear la aplicación Flask
app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = 'loteria-medellin-predictor-2026'
app.config['JSON_AS_ASCII'] = False  # Para caracteres especiales en español


@app.route('/')
def index():
    """Página principal de la aplicación"""
    return render_template('index.html')


@app.route('/api/prediccion', methods=['GET'])
def api_prediccion():
    """
    ENDPOINT ORIGINAL - mantener para compatibilidad pero usar predictor corregido
    """
    try:
        from predictor_corregido import generar_prediccion_NUEVA
        
        prediccion = generar_prediccion_NUEVA()
        
        if "error" in prediccion:
            return jsonify({"error": prediccion["error"]}), 500
        
        return jsonify({
            "success": True,
            "data": prediccion,
            "version": "CORREGIDA"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}"
        }), 500


@app.route('/api/prediccion-corregida', methods=['GET'])
def api_prediccion_corregida():
    """
    Genera y retorna la predicción actual del sistema (VERSIÓN CORREGIDA)
    """
    try:
        # Usar el nuevo predictor corregido
        from predictor_corregido import generar_prediccion_NUEVA
        
        prediccion = generar_prediccion_NUEVA()
        
        if "error" in prediccion:
            return jsonify({"error": prediccion["error"]}), 500
        
        return jsonify({
            "success": True,
            "data": prediccion,
            "version": "CORREGIDA",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error generando predicción: {str(e)}"
        }), 500


@app.route('/api/historial', methods=['GET'])
def api_historial():
    """
    Retorna el historial de resultados de la lotería
    """
    try:
        # Obtener parámetro de límite (por defecto 20)
        limite = int(request.args.get('limite', 20))
        limite = min(limite, 100)  # Máximo 100 resultados
        
        session = obtener_session(crear_engine())
        
        # Obtener los últimos N resultados
        resultados = session.query(Resultado).filter(
            Resultado.numero.isnot(None)
        ).order_by(Resultado.fecha.desc()).limit(limite).all()
        
        historial = []
        for resultado in resultados:
            historial.append({
                "id": resultado.id,
                "fecha": resultado.fecha.strftime("%d/%m/%Y"),
                "sorteo": resultado.sorteo,
                "numero": f"{resultado.numero:04d}",
                "serie": f"{resultado.serie:03d}",
                "dia_semana": resultado.dia_semana,
                "es_festivo": resultado.es_festivo
            })
        
        session.close()
        
        return jsonify({
            "success": True,
            "data": historial,
            "total": len(historial)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error obteniendo historial: {str(e)}"
        }), 500


@app.route('/api/resultado', methods=['POST'])
def api_resultado():
    """
    Ingresa un nuevo resultado de lotería y genera retroalimentación
    """
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data or not all(k in data for k in ['fecha', 'sorteo', 'numero', 'serie']):
            return jsonify({
                "success": False,
                "error": "Faltan datos requeridos: fecha, sorteo, numero, serie"
            }), 400
        
        # Validar y convertir datos
        try:
            fecha_str = data['fecha']
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            sorteo = int(data['sorteo'])
            numero = int(data['numero'])
            serie = int(data['serie'])
        except (ValueError, TypeError) as e:
            return jsonify({
                "success": False,
                "error": f"Error en formato de datos: {str(e)}"
            }), 400
        
        # Validar rangos
        if not (0 <= numero <= 9999):
            return jsonify({
                "success": False,
                "error": "El número debe estar entre 0000 y 9999"
            }), 400
        
        if not (0 <= serie <= 999):
            return jsonify({
                "success": False,
                "error": "La serie debe estar entre 000 y 999"
            }), 400
        
        # Actualizar o crear el resultado en la base de datos
        session = obtener_session(crear_engine())
        
        resultado_existente = session.query(Resultado).filter_by(sorteo=sorteo).first()
        
        if resultado_existente:
            # Actualizar resultado existente
            resultado_existente.numero = numero
            resultado_existente.serie = serie
            resultado_existente.ingresado_en = datetime.now()
        else:
            return jsonify({
                "success": False,
                "error": f"No se encontró el sorteo {sorteo}. Debe existir previamente."
            }), 404
        
        session.commit()
        session.close()
        
        # Generar retroalimentación del aprendizaje
        retroalimentacion = procesar_nuevo_resultado(sorteo, numero, serie)
        
        if "error" in retroalimentacion:
            # Aunque hubo error en retroalimentación, el resultado se guardó
            return jsonify({
                "success": True,
                "message": "Resultado guardado exitosamente",
                "warning": f"Error en retroalimentación: {retroalimentacion['error']}",
                "data": {
                    "numero": f"{numero:04d}",
                    "serie": f"{serie:03d}",
                    "sorteo": sorteo,
                    "fecha": fecha_str
                }
            })
        
        return jsonify({
            "success": True,
            "message": "Resultado ingresado y evaluado exitosamente",
            "data": {
                "numero": f"{numero:04d}",
                "serie": f"{serie:03d}",
                "sorteo": sorteo,
                "fecha": fecha_str,
                "retroalimentacion": retroalimentacion
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error procesando resultado: {str(e)}"
        }), 500


@app.route('/api/estadisticas', methods=['GET'])
def api_estadisticas():
    """
    Retorna estadísticas generales del sistema
    """
    try:
        # Obtener estadísticas de precisión
        stats_precision = obtener_estadisticas()
        
        # Obtener estadísticas generales de la base de datos
        session = obtener_session(crear_engine())
        
        total_sorteos = session.query(Resultado).count()
        sorteos_jugados = session.query(Resultado).filter(
            Resultado.numero.isnot(None)
        ).count()
        sorteos_pendientes = session.query(Resultado).filter(
            Resultado.numero.is_(None)
        ).count()
        
        # Números más frecuentes históricos
        resultados = session.query(Resultado).filter(
            Resultado.numero.isnot(None)
        ).all()
        
        from collections import Counter
        frecuencias = Counter([r.numero for r in resultados])
        mas_frecuentes = frecuencias.most_common(10)
        
        # Números con mayor gap (menos frecuentes recientemente)
        numeros_con_gap = []
        if resultados:
            ultima_aparicion = {}
            for i, resultado in enumerate(resultados):
                ultima_aparicion[resultado.numero] = i
            
            total_resultados = len(resultados)
            gaps = []
            for numero in range(10000):
                if numero in ultima_aparicion:
                    gap = total_resultados - ultima_aparicion[numero] - 1
                    gaps.append((numero, gap))
            
            gaps.sort(key=lambda x: x[1], reverse=True)
            numeros_con_gap = gaps[:10]
        
        session.close()
        
        estadisticas = {
            "resumen": {
                "total_sorteos": total_sorteos,
                "sorteos_jugados": sorteos_jugados,
                "sorteos_pendientes": sorteos_pendientes
            },
            "precision": stats_precision,
            "numeros_calientes": [
                {
                    "numero": f"{numero:04d}",
                    "frecuencia": freq,
                    "porcentaje": round(freq / sorteos_jugados * 100, 2) if sorteos_jugados > 0 else 0
                }
                for numero, freq in mas_frecuentes
            ],
            "numeros_frios": [
                {
                    "numero": f"{numero:04d}",
                    "gap": gap,
                    "descripcion": f"No sale hace {gap} sorteos"
                }
                for numero, gap in numeros_con_gap
            ]
        }
        
        return jsonify({
            "success": True,
            "data": estadisticas
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error obteniendo estadísticas: {str(e)}"
        }), 500


@app.route('/api/retroalimentacion', methods=['GET'])
def api_retroalimentacion():
    """
    Retorna la última retroalimentación generada por el sistema
    """
    try:
        retroalimentacion = obtener_ultima_retroalimentacion()
        
        if not retroalimentacion:
            return jsonify({
                "success": True,
                "data": None,
                "message": "No hay retroalimentación disponible aún"
            })
        
        if "error" in retroalimentacion:
            return jsonify({
                "success": False,
                "error": retroalimentacion["error"]
            }), 500
        
        return jsonify({
            "success": True,
            "data": retroalimentacion
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error obteniendo retroalimentación: {str(e)}"
        }), 500


@app.route('/api/cargar-datos', methods=['POST'])
def api_cargar_datos():
    """
    Endpoint para cargar datos desde CSV (admin)
    """
    try:
        exito = cargar_csv_a_db()
        
        if exito:
            return jsonify({
                "success": True,
                "message": "Datos cargados exitosamente"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Error al cargar los datos"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error en carga de datos: {str(e)}"
        }), 500


# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint no encontrado"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Error interno del servidor"
    }), 500


def inicializar_aplicacion():
    """
    Inicializa la aplicación: base de datos, datos, configuración
    """
    print("🚀 Inicializando aplicación Predictor Lotería de Medellín...")
    
    try:
        # Crear engine y tablas
        engine = crear_engine()
        crear_tablas(engine)
        print("✅ Base de datos inicializada")
        
        # Inicializar pesos por defecto
        session = obtener_session(engine)
        inicializar_pesos_por_defecto(session)
        session.close()
        print("✅ Pesos de métodos configurados")
        
        # Verificar si hay datos
        session = obtener_session(engine)
        total_resultados = session.query(Resultado).count()
        session.close()
        
        if total_resultados == 0:
            print("📥 No hay datos históricos. Cargando desde CSV...")
            exito = cargar_csv_a_db()
            if exito:
                print("✅ Datos históricos cargados exitosamente")
            else:
                print("⚠️ Error al cargar datos históricos")
        else:
            print(f"✅ Base de datos ya contiene {total_resultados} registros")
        
        print("🎉 ¡Aplicación inicializada correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando aplicación: {e}")
        return False


if __name__ == '__main__':
    # Inicializar aplicación
    if inicializar_aplicacion():
        print("\n🌐 Iniciando servidor web...")
        print("📱 Accede a: http://localhost:5000")
        print("🔧 Modo debug activado")
        print("⏹️ Presiona Ctrl+C para detener")
        
        # Ejecutar aplicación Flask
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Evitar doble inicialización
        )
    else:
        print("💥 No se pudo inicializar la aplicación. Revisa los errores anteriores.")