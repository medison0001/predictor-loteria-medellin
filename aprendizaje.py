"""
Sistema de Aprendizaje y Retroalimentación para el Predictor de Lotería de Medellín
Evalúa predicciones vs resultados reales y ajusta pesos de métodos automáticamente
"""

import json
from datetime import datetime
from modelos import crear_engine, obtener_session, Resultado, Prediccion, Retroalimentacion, ConfiguracionPesos


class SistemaAprendizaje:
    def __init__(self):
        self.engine = crear_engine()
    
    def evaluar_prediccion_vs_resultado(self, sorteo_numero, numero_real, serie_real):
        """
        Evalúa la última predicción contra el resultado real ingresado
        """
        session = obtener_session(self.engine)
        
        try:
            # Buscar el resultado correspondiente al sorteo
            resultado = session.query(Resultado).filter_by(sorteo=sorteo_numero).first()
            if not resultado:
                return {"error": f"No se encontró el sorteo {sorteo_numero}"}
            
            # Buscar la predicción más reciente antes de este resultado
            prediccion = session.query(Prediccion).filter(
                Prediccion.fecha_generada <= resultado.fecha
            ).order_by(Prediccion.fecha_generada.desc()).first()
            
            if not prediccion:
                return {"error": "No hay predicciones previas para evaluar"}
            
            # Realizar la evaluación
            evaluacion = self._evaluar_aciertos(
                prediccion.numero_predicho, numero_real,
                prediccion.serie_predicha, serie_real
            )
            
            # Determinar el método que más influyó en la predicción
            metodos_usados = json.loads(prediccion.metodos_usados)
            metodo_mayor_peso = max(metodos_usados.items(), key=lambda x: x[1])
            
            # Crear registro de retroalimentación
            retroalimentacion = Retroalimentacion(
                prediccion_id=prediccion.id,
                resultado_id=resultado.id,
                numero_predicho=prediccion.numero_predicho,
                numero_real=numero_real,
                serie_predicha=prediccion.serie_predicha,
                serie_real=serie_real,
                acierto_numero=evaluacion["acierto_numero"],
                acierto_serie=evaluacion["acierto_serie"],
                acierto_cifras=evaluacion["acierto_cifras"],
                factor_que_mas_peso=metodo_mayor_peso[0]
            )
            
            # Realizar ajustes de pesos
            ajustes_realizados = self._ajustar_pesos_metodos(
                evaluacion, metodos_usados, session
            )
            
            retroalimentacion.ajuste_aplicado = json.dumps(ajustes_realizados)
            
            # Guardar la retroalimentación
            session.add(retroalimentacion)
            session.commit()
            
            # Generar mensaje de retroalimentación
            mensaje = self._generar_mensaje_retroalimentacion(
                evaluacion, prediccion, numero_real, serie_real,
                metodo_mayor_peso[0], ajustes_realizados
            )
            
            resultado_evaluacion = {
                "evaluacion": evaluacion,
                "mensaje": mensaje,
                "ajustes_aplicados": ajustes_realizados,
                "metodo_mas_influyente": metodo_mayor_peso[0],
                "prediccion_evaluada": {
                    "numero": prediccion.numero_predicho,
                    "serie": prediccion.serie_predicha,
                    "confianza": prediccion.confianza
                }
            }
            
            session.close()
            return resultado_evaluacion
            
        except Exception as e:
            session.rollback()
            session.close()
            return {"error": f"Error en evaluación: {str(e)}"}
    
    def _evaluar_aciertos(self, numero_predicho, numero_real, serie_predicha, serie_real):
        """
        Evalúa los diferentes tipos de aciertos posibles
        """
        # Acierto exacto del número
        acierto_numero = numero_predicho == numero_real
        
        # Acierto de serie
        acierto_serie = serie_predicha == serie_real
        
        # Contar cifras que coinciden en la misma posición
        numero_pred_str = f"{numero_predicho:04d}"
        numero_real_str = f"{numero_real:04d}"
        
        acierto_cifras = 0
        for i in range(4):
            if numero_pred_str[i] == numero_real_str[i]:
                acierto_cifras += 1
        
        # Verificar si el número estaba en top 5 (esto requeriría más contexto)
        # Por simplicidad, lo omitimos aquí
        
        return {
            "acierto_numero": acierto_numero,
            "acierto_serie": acierto_serie,  
            "acierto_cifras": acierto_cifras,
            "numero_predicho": numero_predicho,
            "numero_real": numero_real,
            "serie_predicha": serie_predicha,
            "serie_real": serie_real
        }
    
    def _ajustar_pesos_metodos(self, evaluacion, metodos_usados, session):
        """
        Ajusta los pesos de los métodos basándose en los resultados
        """
        ajustes = {}
        
        # Determinar si la predicción fue exitosa o no
        exito_general = (
            evaluacion["acierto_numero"] or 
            evaluacion["acierto_serie"] or 
            evaluacion["acierto_cifras"] >= 2
        )
        
        # Ajustar pesos según el resultado
        for nombre_metodo, peso_actual in metodos_usados.items():
            config_peso = session.query(ConfiguracionPesos).filter_by(
                nombre_metodo=nombre_metodo
            ).first()
            
            if not config_peso:
                continue
            
            peso_anterior = config_peso.peso_actual
            nuevo_peso = peso_anterior
            razon_ajuste = ""
            
            if exito_general:
                # Si hubo éxito, premiar métodos con mayor peso
                if peso_actual > 0.15:  # Si tenía peso significativo
                    nuevo_peso = min(peso_anterior * 1.02, 0.35)  # Aumentar 2%, max 35%
                    razon_ajuste = "Premiado por éxito"
            else:
                # Si falló, penalizar el método con mayor peso
                if peso_actual == max(metodos_usados.values()):
                    nuevo_peso = max(peso_anterior * 0.98, 0.05)  # Reducir 2%, min 5%
                    razon_ajuste = "Penalizado por fallo principal"
            
            # Aplicar ajuste si hay cambio significativo
            if abs(nuevo_peso - peso_anterior) > 0.001:
                config_peso.peso_actual = nuevo_peso
                config_peso.veces_ajustado += 1
                config_peso.ultima_actualizacion = datetime.now()
                
                ajustes[nombre_metodo] = {
                    "peso_anterior": round(peso_anterior, 4),
                    "peso_nuevo": round(nuevo_peso, 4),
                    "cambio": round(nuevo_peso - peso_anterior, 4),
                    "razon": razon_ajuste
                }
        
        # Normalizar pesos para que sumen 1.0
        self._normalizar_pesos(session)
        
        return ajustes
    
    def _normalizar_pesos(self, session):
        """
        Normaliza todos los pesos para que sumen 1.0
        """
        configuraciones = session.query(ConfiguracionPesos).all()
        suma_actual = sum(config.peso_actual for config in configuraciones)
        
        if suma_actual > 0:
            for config in configuraciones:
                config.peso_actual = config.peso_actual / suma_actual
    
    def _generar_mensaje_retroalimentacion(self, evaluacion, prediccion, 
                                         numero_real, serie_real, 
                                         metodo_principal, ajustes):
        """
        Genera un mensaje en español explicando los resultados
        """
        numero_pred = f"{prediccion.numero_predicho:04d}"
        serie_pred = f"{prediccion.serie_predicha:03d}"
        numero_real_str = f"{numero_real:04d}"
        serie_real_str = f"{serie_real:03d}"
        
        mensaje = f"🎲 **Resultado del Sorteo**\n\n"
        mensaje += f"**Número ganador**: {numero_real_str} - Serie {serie_real_str}\n"
        mensaje += f"**Mi predicción**: {numero_pred} - Serie {serie_pred}\n\n"
        
        # Evaluar aciertos
        if evaluacion["acierto_numero"]:
            mensaje += "🎉 **¡INCREÍBLE! ¡Acerté el número exacto!** 🎊\n"
            mensaje += "Este es un logro extraordinario en predicción de lotería.\n\n"
        elif evaluacion["acierto_serie"]:
            mensaje += "🎯 **¡Excelente! ¡Acerté la serie!** ✨\n"
            mensaje += "Aunque no di con el número, predecir la serie correcta es muy bueno.\n\n"
        elif evaluacion["acierto_cifras"] >= 3:
            mensaje += f"👏 **¡Muy bien! Acerté {evaluacion['acierto_cifras']} cifras en sus posiciones correctas!**\n"
            mensaje += "Esto indica que mis métodos van por buen camino.\n\n"
        elif evaluacion["acierto_cifras"] >= 1:
            mensaje += f"📊 **Acerté {evaluacion['acierto_cifras']} cifra(s) en posición correcta.**\n"
            mensaje += "No está mal, pero puedo mejorar.\n\n"
        else:
            mensaje += "😔 **Esta vez no acerté**, pero cada error me ayuda a aprender.\n\n"
        
        # Explicar el método principal
        metodo_nombre = metodo_principal.replace("_", " ").title()
        mensaje += f"🧠 **Método que más influyó**: {metodo_nombre}\n\n"
        
        # Mostrar ajustes realizados
        if ajustes:
            mensaje += "⚙️ **Ajustes realizados para mejorar**:\n"
            for metodo, ajuste_info in ajustes.items():
                metodo_limpio = metodo.replace("_", " ").title()
                cambio = ajuste_info["cambio"]
                if cambio > 0:
                    mensaje += f"📈 {metodo_limpio}: +{cambio:.2%} (premiado)\n"
                elif cambio < 0:
                    mensaje += f"📉 {metodo_limpio}: {cambio:.2%} (ajustado)\n"
        else:
            mensaje += "⚙️ No se realizaron ajustes significativos en esta evaluación.\n"
        
        mensaje += "\n🔮 **Mi próxima predicción será más precisa gracias a este aprendizaje.**"
        
        return mensaje
    
    def obtener_estadisticas_precision(self):
        """
        Obtiene estadísticas generales de precisión del sistema
        """
        session = obtener_session(self.engine)
        
        try:
            # Contar todas las retroalimentaciones
            total_evaluaciones = session.query(Retroalimentacion).count()
            
            if total_evaluaciones == 0:
                return {"total_evaluaciones": 0, "sin_datos": True}
            
            # Contar aciertos por tipo
            aciertos_numero = session.query(Retroalimentacion).filter_by(acierto_numero=True).count()
            aciertos_serie = session.query(Retroalimentacion).filter_by(acierto_serie=True).count()
            
            # Distribución de aciertos de cifras
            aciertos_cifras = {}
            for i in range(5):  # 0 a 4 cifras
                count = session.query(Retroalimentacion).filter_by(acierto_cifras=i).count()
                aciertos_cifras[i] = count
            
            # Métodos más exitosos
            retroalimentaciones = session.query(Retroalimentacion).all()
            metodos_exitosos = {}
            
            for retro in retroalimentaciones:
                metodo = retro.factor_que_mas_peso
                if metodo not in metodos_exitosos:
                    metodos_exitosos[metodo] = {"total": 0, "exitos": 0}
                
                metodos_exitosos[metodo]["total"] += 1
                
                if retro.acierto_numero or retro.acierto_serie or retro.acierto_cifras >= 2:
                    metodos_exitosos[metodo]["exitos"] += 1
            
            # Calcular tasas de éxito
            for metodo in metodos_exitosos:
                if metodos_exitosos[metodo]["total"] > 0:
                    metodos_exitosos[metodo]["tasa_exito"] = (
                        metodos_exitosos[metodo]["exitos"] / 
                        metodos_exitosos[metodo]["total"] * 100
                    )
            
            estadisticas = {
                "total_evaluaciones": total_evaluaciones,
                "aciertos_numero": aciertos_numero,
                "aciertos_serie": aciertos_serie,
                "tasa_acierto_numero": aciertos_numero / total_evaluaciones * 100,
                "tasa_acierto_serie": aciertos_serie / total_evaluaciones * 100,
                "distribucion_cifras": aciertos_cifras,
                "metodos_exitosos": metodos_exitosos,
                "fecha_actualizacion": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            session.close()
            return estadisticas
            
        except Exception as e:
            session.close()
            return {"error": f"Error obteniendo estadísticas: {str(e)}"}
    
    def obtener_ultima_retroalimentacion(self):
        """
        Obtiene la última retroalimentación generada
        """
        session = obtener_session(self.engine)
        
        try:
            ultima = session.query(Retroalimentacion).order_by(
                Retroalimentacion.fecha_evaluacion.desc()
            ).first()
            
            if not ultima:
                return None
            
            # Reconstruir el mensaje (podría estar guardado, pero lo generamos fresh)
            prediccion = session.query(Prediccion).get(ultima.prediccion_id)
            
            if prediccion:
                evaluacion = {
                    "acierto_numero": ultima.acierto_numero,
                    "acierto_serie": ultima.acierto_serie,
                    "acierto_cifras": ultima.acierto_cifras
                }
                
                ajustes = json.loads(ultima.ajuste_aplicado) if ultima.ajuste_aplicado else {}
                
                mensaje = self._generar_mensaje_retroalimentacion(
                    evaluacion, prediccion,
                    ultima.numero_real, ultima.serie_real,
                    ultima.factor_que_mas_peso, ajustes
                )
                
                resultado = {
                    "mensaje": mensaje,
                    "fecha": ultima.fecha_evaluacion.strftime("%d/%m/%Y %H:%M"),
                    "evaluacion": evaluacion,
                    "ajustes_aplicados": ajustes
                }
                
                session.close()
                return resultado
            
            session.close()
            return None
            
        except Exception as e:
            session.close()
            return {"error": f"Error obteniendo retroalimentación: {str(e)}"}


# Función de conveniencia para uso desde Flask
def procesar_nuevo_resultado(sorteo, numero, serie):
    """
    Procesa un nuevo resultado y genera retroalimentación
    """
    sistema = SistemaAprendizaje()
    return sistema.evaluar_prediccion_vs_resultado(sorteo, numero, serie)


def obtener_estadisticas():
    """
    Obtiene estadísticas de precisión del sistema
    """
    sistema = SistemaAprendizaje()
    return sistema.obtener_estadisticas_precision()


def obtener_ultima_retroalimentacion():
    """
    Obtiene la última retroalimentación
    """
    sistema = SistemaAprendizaje()
    return sistema.obtener_ultima_retroalimentacion()


if __name__ == "__main__":
    print("📊 Sistema de Aprendizaje - Prueba de estadísticas")
    
    stats = obtener_estadisticas()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    ultima = obtener_ultima_retroalimentacion()
    if ultima:
        print("\n📝 Última retroalimentación:")
        print(ultima["mensaje"])