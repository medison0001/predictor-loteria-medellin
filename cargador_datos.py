"""
Cargador de Datos para el Predictor de Lotería de Medellín
Lee el archivo CSV de resultados históricos y los carga en la base de datos
Incluye manejo de festivos colombianos y fechas especiales
"""

import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
from modelos import crear_engine, crear_tablas, obtener_session, Resultado, inicializar_pesos_por_defecto
import os


def obtener_festivos_colombia():
    """
    Retorna diccionario con festivos fijos y móviles de Colombia para 2024-2027
    """
    festivos = {
        # Festivos fijos (siempre la misma fecha)
        2024: [
            date(2024, 1, 1),   # Año Nuevo
            date(2024, 5, 1),   # Día del Trabajo  
            date(2024, 7, 20),  # Independencia
            date(2024, 8, 7),   # Batalla de Boyacá
            date(2024, 12, 8),  # Inmaculada Concepción
            date(2024, 12, 25), # Navidad
            # Festivos que se trasladan al lunes
            date(2024, 1, 8),   # Epifanía (trasladado)
            date(2024, 3, 25),  # San José (trasladado)
            date(2024, 6, 3),   # Sagrado Corazón (trasladado) 
            date(2024, 6, 24),  # San Pedro y San Pablo (trasladado)
            date(2024, 8, 19),  # Asunción (trasladado)
            date(2024, 10, 14), # Día de la Raza (trasladado)
            date(2024, 11, 4),  # Todos los Santos (trasladado)
            date(2024, 11, 18), # Independencia de Cartagena (trasladado)
            # Semana Santa 2024
            date(2024, 3, 28),  # Jueves Santo
            date(2024, 3, 29),  # Viernes Santo
            date(2024, 5, 13),  # Ascensión (trasladado)
            date(2024, 6, 3),   # Corpus Christi (trasladado)
        ],
        
        2025: [
            date(2025, 1, 1),   # Año Nuevo
            date(2025, 5, 1),   # Día del Trabajo
            date(2025, 7, 20),  # Independencia
            date(2025, 8, 7),   # Batalla de Boyacá
            date(2025, 12, 8),  # Inmaculada Concepción
            date(2025, 12, 25), # Navidad
            # Festivos trasladados al lunes 2025
            date(2025, 1, 6),   # Epifanía (trasladado)
            date(2025, 3, 24),  # San José (trasladado)
            date(2025, 6, 23),  # San Pedro y San Pablo (trasladado)
            date(2025, 8, 18),  # Asunción (trasladado)
            date(2025, 10, 13), # Día de la Raza (trasladado)
            date(2025, 11, 3),  # Todos los Santos (trasladado)
            date(2025, 11, 17), # Independencia de Cartagena (trasladado)
            # Semana Santa 2025
            date(2025, 4, 17),  # Jueves Santo
            date(2025, 4, 18),  # Viernes Santo
            date(2025, 6, 2),   # Ascensión (trasladado)
            date(2025, 6, 23),  # Corpus Christi (trasladado)
        ],
        
        2026: [
            date(2026, 1, 1),   # Año Nuevo
            date(2026, 5, 1),   # Día del Trabajo
            date(2026, 7, 20),  # Independencia
            date(2026, 8, 7),   # Batalla de Boyacá
            date(2026, 12, 8),  # Inmaculada Concepción
            date(2026, 12, 25), # Navidad
            # Festivos trasladados al lunes 2026
            date(2026, 1, 12),  # Epifanía (trasladado)
            date(2026, 3, 23),  # San José (trasladado)
            date(2026, 6, 29),  # San Pedro y San Pablo (trasladado)
            date(2026, 8, 17),  # Asunción (trasladado)
            date(2026, 10, 12), # Día de la Raza (trasladado)
            date(2026, 11, 2),  # Todos los Santos (trasladado)
            date(2026, 11, 16), # Independencia de Cartagena (trasladado)
            # Semana Santa 2026
            date(2026, 4, 2),   # Jueves Santo
            date(2026, 4, 3),   # Viernes Santo
            date(2026, 5, 18),  # Ascensión (trasladado)
            date(2026, 6, 8),   # Corpus Christi (trasladado)
        ],
        
        2027: [
            date(2027, 1, 1),   # Año Nuevo
            date(2027, 5, 1),   # Día del Trabajo
            date(2027, 7, 20),  # Independencia
            date(2027, 8, 7),   # Batalla de Boyacá
            date(2027, 12, 8),  # Inmaculada Concepción
            date(2027, 12, 25), # Navidad
            # Festivos trasladados al lunes 2027
            date(2027, 1, 11),  # Epifanía (trasladado)
            date(2027, 3, 22),  # San José (trasladado)
            date(2027, 6, 28),  # San Pedro y San Pablo (trasladado)
            date(2027, 8, 16),  # Asunción (trasladado)
            date(2027, 10, 18), # Día de la Raza (trasladado)
            date(2027, 11, 1),  # Todos los Santos (trasladado)
            date(2027, 11, 15), # Independencia de Cartagena (trasladado)
            # Semana Santa 2027
            date(2027, 3, 25),  # Jueves Santo
            date(2027, 3, 26),  # Viernes Santo
            date(2027, 5, 10),  # Ascensión (trasladado)
            date(2027, 5, 31),  # Corpus Christi (trasladado)
        ]
    }
    
    return festivos


def es_viernes_festivo(fecha_sorteo):
    """
    Verifica si una fecha es viernes festivo en Colombia
    Si es viernes festivo, el sorteo se mueve al sábado siguiente
    """
    festivos = obtener_festivos_colombia()
    
    # Verificar si la fecha está en la lista de festivos del año correspondiente
    if fecha_sorteo.year in festivos:
        if fecha_sorteo in festivos[fecha_sorteo.year]:
            # Verificar si ese festivo cae en viernes
            return fecha_sorteo.weekday() == 4  # 4 = viernes
    
    return False


def obtener_dia_semana_espanol(fecha):
    """Convierte el día de la semana al español"""
    dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    return dias[fecha.weekday()]


def limpiar_y_convertir_fecha(fecha_str):
    """
    Convierte string de fecha del CSV al formato date de Python
    Formato entrada: "2007 Jan 05 12:00:00 AM"
    """
    try:
        # Parsear la fecha del formato original
        fecha_dt = pd.to_datetime(fecha_str, format="%Y %b %d %I:%M:%S %p")
        return fecha_dt.date()
    except:
        print(f"Error al convertir fecha: {fecha_str}")
        return None


def cargar_csv_a_db(ruta_csv=None):
    """
    Función principal que carga el archivo CSV a la base de datos
    """
    if ruta_csv is None:
        ruta_csv = os.path.join(os.path.dirname(__file__), "datos", "RESULTADOS_PREMIO_MAYOR_LOTERIA_DE_MEDELLIN_HASTA_ABRIL_2026.csv")
    
    if not os.path.exists(ruta_csv):
        print(f"❌ Error: No se encontró el archivo {ruta_csv}")
        return False
    
    try:
        # Crear engine y tablas
        engine = crear_engine()
        crear_tablas(engine)
        session = obtener_session(engine)
        
        # Inicializar pesos por defecto
        inicializar_pesos_por_defecto(session)
        
        # Leer archivo CSV
        print("📂 Leyendo archivo CSV...")
        df = pd.read_csv(ruta_csv)
        
        print(f"📊 Encontrados {len(df)} registros en el CSV")
        
        # Procesar cada fila del CSV
        registros_procesados = 0
        registros_saltados = 0
        
        for _, fila in df.iterrows():
            try:
                # Limpiar y convertir datos
                fecha = limpiar_y_convertir_fecha(fila['FECHA DE JUEGO'])
                if fecha is None:
                    registros_saltados += 1
                    continue
                
                sorteo = int(fila['SORTEO'])
                
                # Convertir número a 4 dígitos
                numero_str = str(fila['NÚMERO']).zfill(4) if pd.notna(fila['NÚMERO']) else None
                numero = int(numero_str) if numero_str else None
                
                # Convertir serie a 3 dígitos
                serie_str = str(fila['SERIE']).zfill(3) if pd.notna(fila['SERIE']) else None
                serie = int(serie_str) if serie_str else None
                
                # Calcular día de la semana en español
                dia_semana = obtener_dia_semana_espanol(fecha)
                
                # Verificar si es festivo
                es_festivo = es_viernes_festivo(fecha)
                
                # Verificar si ya existe este sorteo
                resultado_existente = session.query(Resultado).filter_by(sorteo=sorteo).first()
                if resultado_existente:
                    registros_saltados += 1
                    continue
                
                # Crear nuevo resultado
                nuevo_resultado = Resultado(
                    fecha=fecha,
                    sorteo=sorteo,
                    numero=numero,
                    serie=serie,
                    dia_semana=dia_semana,
                    es_festivo=es_festivo
                )
                
                session.add(nuevo_resultado)
                registros_procesados += 1
                
            except Exception as e:
                print(f"⚠️ Error procesando fila: {e}")
                registros_saltados += 1
                continue
        
        # Agregar los dos registros faltantes (sorteos futuros)
        print("📅 Agregando sorteos futuros pendientes...")
        
        # Sorteo 4832 - 24 abril 2026
        fecha_4832 = date(2026, 4, 24)
        resultado_4832 = session.query(Resultado).filter_by(sorteo=4832).first()
        if not resultado_4832:
            nuevo_4832 = Resultado(
                fecha=fecha_4832,
                sorteo=4832,
                numero=None,
                serie=None,
                dia_semana=obtener_dia_semana_espanol(fecha_4832),
                es_festivo=es_viernes_festivo(fecha_4832)
            )
            session.add(nuevo_4832)
            registros_procesados += 1
        
        # Sorteo 4833 - 2 mayo 2026
        fecha_4833 = date(2026, 5, 2)
        resultado_4833 = session.query(Resultado).filter_by(sorteo=4833).first()
        if not resultado_4833:
            nuevo_4833 = Resultado(
                fecha=fecha_4833,
                sorteo=4833,
                numero=None,
                serie=None,
                dia_semana=obtener_dia_semana_espanol(fecha_4833),
                es_festivo=es_viernes_festivo(fecha_4833)
            )
            session.add(nuevo_4833)
            registros_procesados += 1
        
        # Guardar todos los cambios
        session.commit()
        
        print(f"✅ Carga completada:")
        print(f"   📥 Registros procesados: {registros_procesados}")
        print(f"   ⏭️ Registros saltados: {registros_saltados}")
        print(f"   🎯 Total en base de datos: {session.query(Resultado).count()}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error durante la carga: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def verificar_integridad_datos():
    """
    Verifica la integridad de los datos cargados
    """
    engine = crear_engine()
    session = obtener_session(engine)
    
    try:
        print("\n🔍 Verificando integridad de datos...")
        
        # Contar total de registros
        total = session.query(Resultado).count()
        print(f"📊 Total de registros: {total}")
        
        # Contar resultados con números (ya jugados)
        con_numeros = session.query(Resultado).filter(Resultado.numero.isnot(None)).count()
        print(f"🎲 Sorteos con resultados: {con_numeros}")
        
        # Contar pendientes
        pendientes = session.query(Resultado).filter(Resultado.numero.is_(None)).count()
        print(f"⏳ Sorteos pendientes: {pendientes}")
        
        # Verificar rango de fechas
        fecha_min = session.query(Resultado.fecha).order_by(Resultado.fecha.asc()).first()[0]
        fecha_max = session.query(Resultado.fecha).order_by(Resultado.fecha.desc()).first()[0]
        print(f"📅 Rango de fechas: {fecha_min} a {fecha_max}")
        
        # Verificar continuidad de sorteos
        sorteos = session.query(Resultado.sorteo).order_by(Resultado.sorteo.asc()).all()
        sorteos_nums = [s[0] for s in sorteos]
        
        saltos = []
        for i in range(1, len(sorteos_nums)):
            if sorteos_nums[i] != sorteos_nums[i-1] + 1:
                saltos.append(f"{sorteos_nums[i-1]} -> {sorteos_nums[i]}")
        
        if saltos:
            print(f"⚠️ Saltos en secuencia de sorteos: {saltos[:5]}")  # Mostrar solo los primeros 5
        else:
            print("✅ Secuencia de sorteos es continua")
        
        # Verificar distribución por día de la semana
        print("\n📈 Distribución por día de la semana:")
        for dia in ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']:
            count = session.query(Resultado).filter(Resultado.dia_semana == dia).count()
            print(f"   {dia}: {count} sorteos")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        session.close()


if __name__ == "__main__":
    print("🚀 Iniciando carga de datos de la Lotería de Medellín...")
    
    # Cargar datos desde CSV
    exito = cargar_csv_a_db()
    
    if exito:
        # Verificar integridad
        verificar_integridad_datos()
        print("\n🎉 ¡Carga de datos completada exitosamente!")
    else:
        print("\n💥 Error en la carga de datos. Revisa los logs anteriores.")