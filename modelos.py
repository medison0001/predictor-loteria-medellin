"""
Modelos de Base de Datos para el Predictor de Lotería de Medellín
Contiene todas las tablas necesarias para el análisis y predicción
"""

from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, REAL, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Resultado(Base):
    """Tabla que almacena los resultados históricos y futuros de la lotería"""
    __tablename__ = 'resultados'
    
    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    sorteo = Column(Integer, unique=True, nullable=False)
    numero = Column(Integer)  # 4 dígitos, puede ser NULL si no se ha jugado
    serie = Column(Integer)   # 3 dígitos, puede ser NULL si no se ha jugado
    dia_semana = Column(String(10))  # lunes/martes/.../sábado
    es_festivo = Column(Boolean, default=False)
    ingresado_en = Column(DateTime, default=datetime.now)
    
    # Relaciones
    retroalimentaciones = relationship("Retroalimentacion", back_populates="resultado")
    
    def __repr__(self):
        return f"<Resultado(sorteo={self.sorteo}, fecha={self.fecha}, numero={self.numero}, serie={self.serie})>"


class Prediccion(Base):
    """Tabla que almacena las predicciones generadas por el sistema"""
    __tablename__ = 'predicciones'
    
    id = Column(Integer, primary_key=True)
    fecha_generada = Column(DateTime, default=datetime.now)
    numero_predicho = Column(Integer, nullable=False)
    serie_predicha = Column(Integer, nullable=False)
    confianza = Column(String(10))  # bajo/medio/alto
    metodos_usados = Column(Text)   # JSON con qué análisis se aplicaron
    explicacion = Column(Text)
    
    # Relaciones
    retroalimentaciones = relationship("Retroalimentacion", back_populates="prediccion")
    
    def __repr__(self):
        return f"<Prediccion(numero={self.numero_predicho:04d}, serie={self.serie_predicha:03d}, confianza={self.confianza})>"


class Retroalimentacion(Base):
    """Tabla que almacena la evaluación de predicciones vs resultados reales"""
    __tablename__ = 'retroalimentaciones'
    
    id = Column(Integer, primary_key=True)
    prediccion_id = Column(Integer, ForeignKey('predicciones.id'))
    resultado_id = Column(Integer, ForeignKey('resultados.id'))
    numero_predicho = Column(Integer)
    numero_real = Column(Integer)
    serie_predicha = Column(Integer)
    serie_real = Column(Integer)
    acierto_numero = Column(Boolean, default=False)
    acierto_serie = Column(Boolean, default=False)
    acierto_cifras = Column(Integer)  # cuántas cifras del número coincidieron (0,1,2,3,4)
    fecha_evaluacion = Column(DateTime, default=datetime.now)
    factor_que_mas_peso = Column(String(50))  # método que más influyó
    ajuste_aplicado = Column(Text)  # JSON con los ajustes realizados
    
    # Relaciones
    prediccion = relationship("Prediccion", back_populates="retroalimentaciones")
    resultado = relationship("Resultado", back_populates="retroalimentaciones")
    
    def __repr__(self):
        return f"<Retroalimentacion(numero_pred={self.numero_predicho}, numero_real={self.numero_real}, aciertos={self.acierto_cifras})>"


class ConfiguracionPesos(Base):
    """Tabla para almacenar y ajustar los pesos de cada método de análisis"""
    __tablename__ = 'configuracion_pesos'
    
    id = Column(Integer, primary_key=True)
    nombre_metodo = Column(String(50), unique=True, nullable=False)
    peso_actual = Column(REAL, nullable=False)
    peso_original = Column(REAL, nullable=False)
    veces_ajustado = Column(Integer, default=0)
    ultima_actualizacion = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<ConfiguracionPesos(metodo={self.nombre_metodo}, peso={self.peso_actual})>"


# Configuración de la base de datos
def crear_engine(archivo_db='loteria_medellin.db'):
    """Crea el engine de SQLAlchemy para la base de datos"""
    ruta_db = os.path.join(os.path.dirname(__file__), archivo_db)
    engine = create_engine(f'sqlite:///{ruta_db}', echo=False)
    return engine


def crear_tablas(engine):
    """Crea todas las tablas en la base de datos"""
    Base.metadata.create_all(engine)


def obtener_session(engine):
    """Obtiene una sesión de SQLAlchemy"""
    Session = sessionmaker(bind=engine)
    return Session()


def inicializar_pesos_por_defecto(session):
    """Inicializa los pesos por defecto de los métodos de análisis"""
    pesos_defecto = [
        {"nombre_metodo": "frecuencia_historica", "peso": 0.20},
        {"nombre_metodo": "analisis_ciclos_gaps", "peso": 0.20},
        {"nombre_metodo": "patrones_posicion_digitos", "peso": 0.15},
        {"nombre_metodo": "analisis_series", "peso": 0.10},
        {"nombre_metodo": "suma_digitos", "peso": 0.10},
        {"nombre_metodo": "vecinos_matrices", "peso": 0.15},
        {"nombre_metodo": "patrones_fecha_dia", "peso": 0.10}
    ]
    
    for peso_info in pesos_defecto:
        peso_existente = session.query(ConfiguracionPesos).filter_by(
            nombre_metodo=peso_info["nombre_metodo"]
        ).first()
        
        if not peso_existente:
            nuevo_peso = ConfiguracionPesos(
                nombre_metodo=peso_info["nombre_metodo"],
                peso_actual=peso_info["peso"],
                peso_original=peso_info["peso"]
            )
            session.add(nuevo_peso)
    
    session.commit()


if __name__ == "__main__":
    # Crear base de datos y tablas para pruebas
    engine = crear_engine()
    crear_tablas(engine)
    session = obtener_session(engine)
    inicializar_pesos_por_defecto(session)
    session.close()
    print("✅ Base de datos creada y configurada correctamente")