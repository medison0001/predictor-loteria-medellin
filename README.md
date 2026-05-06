# 🔮 Predicción - Predictor de Lotería de Medellín

![Lotería de Medellín](https://img.shields.io/badge/Lotería-Medellín-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-red)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue)

Sistema inteligente de predicción para la Lotería de Medellín basado en análisis estadístico avanzado con 7 métodos diferentes y aprendizaje automático.

---

## 📋 ¿Qué es la Lotería de Medellín?

La **Lotería de Medellín** es una de las loterías más tradicionales de Colombia, operada por la empresa Lotería de Medellín desde 1955. Características principales:

- 🗓️ **Frecuencia**: Todos los viernes (se traslada al sábado si el viernes es festivo nacional)
- 🎯 **Premio Mayor**: Número de 4 dígitos (0000 a 9999) 
- 🎲 **Serie**: 3 dígitos (000 a 999)
- 💰 **Premios**: Diversos premios según cifras acertadas y aproximaciones
- 📊 **Historia**: Datos disponibles desde enero de 2007 hasta la fecha

---

## 🧠 ¿Cómo Funciona el Predictor?

Este sistema utiliza **7 métodos de análisis estadístico** que trabajan en conjunto para generar predicciones:

### 🔥 Método 1: Frecuencia Histórica (20%)
Identifica los números que han salido más frecuentemente (números "calientes") y los que han salido menos (números "fríos"). Los números fríos tienen probabilidad teórica de salir pronto.

### ⏰ Método 2: Análisis de Ciclos y Gaps (20%) 
Calcula cuántos sorteos han pasado desde que cada número salió por última vez. Números con "gaps" altos tienen mayor probabilidad estadística.

### 🎯 Método 3: Patrones por Posición (15%)
Analiza la frecuencia de cada dígito (0-9) en cada posición del número (miles, centenas, decenas, unidades) para construir combinaciones probables.

### 🎲 Método 4: Análisis de Series (10%)
Estudia los patrones específicos de las series (000-999) por frecuencia y gaps temporales.

### ➕ Método 5: Suma de Dígitos (10%)
Identifica qué sumas de los 4 dígitos son más comunes históricamente y genera números que cumplan esas sumas favorables.

### 🔗 Método 6: Vecinos y Matrices (15%)
Construye matrices de transición para identificar qué números tienden a salir después de otros números específicos.

### 📅 Método 7: Patrones Temporales (10%)
Analiza si ciertos números salen más en determinados meses, semanas del mes o épocas del año.

---

## 🤖 Sistema de Aprendizaje Automático

El sistema **aprende de sus aciertos y errores**:

- 📊 **Evaluación Automática**: Cuando ingresas un resultado real, compara con la predicción
- ⚖️ **Ajuste de Pesos**: Los métodos que aciertan aumentan su influencia, los que fallan la reducen
- 🎯 **Retroalimentación**: Explica por qué acertó o falló y qué ajustes realizó
- 📈 **Mejora Continua**: Cada sorteo mejora la precisión del sistema

---

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clona o descarga el proyecto**
   ```bash
   git clone https://github.com/tu-usuario/predictor-loteria-medellin.git
   cd predictor-loteria-medellin
   ```

2. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Coloca el archivo de datos**
   - Asegúrate de que el archivo `RESULTADOS_PREMIO_MAYOR_LOTERIA_DE_MEDELLIN_20260505.csv` esté en la carpeta raíz del proyecto
   - El sistema cargará automáticamente estos datos históricos en la primera ejecución

4. **Ejecuta la aplicación**
   ```bash
   python app.py
   ```

5. **Abre tu navegador**
   ```
   http://localhost:5000
   ```

---

## 📱 Cómo Usar la Aplicación

### 🔮 Ver Predicción Actual
- La predicción se genera automáticamente al cargar la página
- Muestra el número y serie más probables
- Incluye nivel de confianza (Alto/Medio/Bajo)
- Lista los top 5 candidatos tanto para números como series

### 📝 Ingresar Nuevo Resultado
Cuando salga el sorteo del viernes:

1. Ve a la sección "Ingresar Nuevo Resultado"
2. Completa los datos:
   - **Fecha del Sorteo**: La fecha cuando se jugó (formato YYYY-MM-DD)
   - **Número de Sorteo**: El número consecutivo del sorteo
   - **Número Ganador**: El número de 4 dígitos que salió
   - **Serie Ganadora**: La serie de 3 dígitos que salió
3. Haz clic en "Guardar Resultado y Evaluar Predicción"
4. El sistema mostrará inmediatamente la retroalimentación

### 📊 Consultar Estadísticas
- **Números Calientes**: Los más frecuentes en la historia
- **Números Fríos**: Los que más tiempo llevan sin salir  
- **Precisión del Sistema**: Estadísticas de aciertos y fallos
- **Historial**: Últimos 20 resultados de la lotería

---

## 🎯 Métodos de Análisis Explicados

### 📊 Análisis de Frecuencia
**Principio**: Los números no salen con la misma frecuencia. Algunos son "favoritos" del azar.
**Aplicación**: Identifica números calientes (muy frecuentes) y fríos (poco frecuentes que "deben" salir).

### ⏳ Análisis de Gaps
**Principio**: Si un número no sale por mucho tiempo, aumenta su probabilidad teórica.
**Aplicación**: Calcula cuántos sorteos han pasado desde la última aparición de cada número.

### 🔢 Patrones de Posición  
**Principio**: Cada posición del número (miles, centenas, etc.) tiene dígitos favoritos.
**Aplicación**: Combina los dígitos más frecuentes en cada posición para formar números candidatos.

### 🎲 Análisis de Series
**Principio**: Las series también siguen patrones de frecuencia y gaps.
**Aplicación**: Identifica series calientes, frías y con mayor gap temporal.

### ➕ Suma de Dígitos
**Principio**: Ciertas sumas de los 4 dígitos aparecen más frecuentemente.
**Aplicación**: Genera números cuya suma de dígitos coincida con las sumas más exitosas históricamente.

### 🔗 Matrices de Transición
**Principio**: Algunos números tienden a "seguir" a otros específicos.
**Aplicación**: Basándose en el último número ganador, predice cuáles podrían seguir.

### 📅 Patrones Temporales
**Principio**: Algunos números prefieren ciertas épocas del año o del mes.
**Aplicación**: Pondera números que históricamente salen en fechas similares al próximo sorteo.

---

## ⚙️ Configuración Técnica

### 📂 Estructura de Archivos
```
predictor-loteria-medellin/
│
├── app.py                      # Aplicación Flask principal
├── modelos.py                  # Modelos de base de datos  
├── cargador_datos.py           # Cargador de datos históricos
├── predictor.py                # Motor de predicción (7 métodos)
├── aprendizaje.py              # Sistema de aprendizaje automático
├── requirements.txt            # Dependencias de Python
├── README.md                   # Esta documentación
│
├── templates/
│   └── index.html              # Página principal HTML
│
├── static/
│   ├── css/
│   │   └── estilos.css         # Estilos CSS
│   └── js/
│       └── app.js              # JavaScript frontend
│
└── datos/
    └── [archivos CSV]          # Datos históricos
```

### 🗄️ Base de Datos
El sistema usa **SQLite** con las siguientes tablas:

- **`resultados`**: Historial completo de sorteos y resultados
- **`predicciones`**: Predicciones generadas por el sistema  
- **`retroalimentaciones`**: Evaluaciones de predicciones vs resultados reales
- **`configuracion_pesos`**: Pesos de cada método (se ajustan automáticamente)

### 🔧 Configuración de Pesos Iniciales
```python
Frecuencia Histórica:     20%
Análisis de Ciclos:       20%  
Patrones de Posición:     15%
Análisis de Series:       10%
Suma de Dígitos:          10%
Vecinos y Matrices:       15%
Patrones Temporales:      10%
```
*Estos pesos se ajustan automáticamente según los resultados.*

---

## 📈 Métricas y Evaluación

### 🎯 Tipos de Acierto Evaluados
1. **Número Exacto**: Predicción idéntica al resultado (muy raro, máximo premio)
2. **Serie Exacta**: Serie predicha coincide con la real
3. **Cifras en Posición**: Cuántas cifras del número coinciden en su posición correcta
4. **Presencia en Top 5**: Si el número real estaba entre los 5 candidatos predichos

### 📊 Métricas del Sistema
- **Tasa de Acierto de Número**: % de números exactos predichos
- **Tasa de Acierto de Serie**: % de series exactas predichas  
- **Promedio de Cifras Acertadas**: Promedio de dígitos en posición correcta
- **Efectividad de Top 5**: % de veces que el número real está en el top 5 predicho

---

## ⚠️ Advertencias Importantes

### 🎲 Naturaleza Aleatoria
**La lotería es un juego completamente aleatorio.** Ningún sistema, algoritmo o método puede garantizar predicciones correctas. Los números se extraen al azar y cada combinación tiene la misma probabilidad matemática.

### 📊 Propósito Educativo  
Este sistema fue creado con fines:
- **Educativos**: Para demostrar análisis estadístico y programación
- **Entretenimiento**: Como ejercicio intelectual interesante
- **Académicos**: Para estudiar patrones en datos aleatorios

### 💰 Juego Responsable
- No uses este sistema como base para apostar dinero que no puedes permitirte perder
- La lotería debe ser siempre un entretenimiento, nunca una inversión
- Establece límites de gasto y respétalos siempre
- Si tienes problemas con el juego, busca ayuda profesional

### 📈 Interpretación de Resultados
- **Alta confianza** no significa certeza, solo consenso entre métodos
- Los números "calientes" o "fríos" no alteran las probabilidades reales
- Los patrones históricos no garantizan repetición futura
- Cada sorteo es independiente de los anteriores

---

## 🔧 Desarrollo y Contribución

### 🛠️ Tecnologías Utilizadas
- **Backend**: Python 3.8+, Flask 3.0, SQLAlchemy 2.0
- **Frontend**: HTML5, CSS3, JavaScript ES6+ (Vanilla)
- **Base de Datos**: SQLite
- **Análisis de Datos**: Pandas, NumPy
- **Estilos**: CSS Grid, Flexbox, Animaciones CSS

### 🎨 Diseño
- **Paleta de Colores**: Inspirada en la Lotería de Medellín
  - Verde oscuro (#1a472a) - Color primario
  - Dorado (#c9a84c) - Color secundario/acentos  
  - Blanco roto (#f5f0e8) - Fondo principal
- **Responsive**: Mobile-first, adaptable a todas las pantallas
- **Tipografía**: Segoe UI para texto, Courier New para números
- **Animaciones**: Suaves y elegantes, inspiradas en displays de lotería

### 🐛 Reportar Problemas
Si encuentras algún error o tienes sugerencias:
1. Revisa la consola del navegador (F12) para errores JavaScript
2. Verifica los logs del servidor Python en la terminal
3. Asegúrate de tener las dependencias correctas instaladas
4. Verifica que el archivo CSV esté en el lugar correcto

### 🤝 Contribuir
Este es un proyecto educativo. Las contribuciones son bienvenidas:
- Mejoras en los métodos de análisis
- Optimizaciones de rendimiento  
- Nuevas funcionalidades estadísticas
- Mejoras en la interfaz de usuario
- Documentación adicional

---

## 📊 Datos Históricos

### 📅 Rango de Datos
- **Inicio**: Enero 2007 (Sorteo #3834)
- **Fin**: Abril 2026 (Sorteo #4831)  
- **Total**: 999+ sorteos históricos
- **Frecuencia**: Semanal (viernes o sábado)

### 📈 Estadísticas Generales
- **Número más frecuente**: Se calcula dinámicamente
- **Número menos frecuente**: Se actualiza constantemente  
- **Distribución por día**: Mayoría viernes, algunos sábados (festivos)
- **Patrones estacionales**: Analizados por el sistema

### 🔄 Actualización de Datos
- Los datos se cargan automáticamente desde el CSV en la primera ejecución
- Nuevos resultados se ingresan manualmente a través de la interfaz web
- La base de datos se actualiza en tiempo real
- No es necesario reiniciar el servidor para nuevos datos

---

## 🏆 Créditos y Reconocimientos

### 👨‍💻 Desarrollo
- **Concepto y Desarrollo**: Sistema de análisis estadístico avanzado
- **Algoritmos**: 7 métodos de predicción implementados desde cero
- **Interfaz**: Diseño responsivo y amigable inspirado en la Lotería de Medellín

### 📊 Fuentes de Datos
- **Lotería de Medellín**: Datos históricos oficiales desde 2007
- **Festivos Colombianos**: Calendario oficial de días festivos en Colombia

### 🎨 Inspiración de Diseño
- **Colores**: Paleta oficial de la Lotería de Medellín
- **Tipografía**: Fuentes que evocan los displays clásicos de lotería
- **Animaciones**: Inspiradas en la revelación de números en sorteos reales

---

## 📄 Licencia

Este proyecto es de código abierto para fines educativos y de entretenimiento. 

### ✅ Permitido:
- Uso personal y educativo
- Modificación y mejora del código
- Distribución del código fuente
- Uso como base para otros proyectos educativos

### ❌ No permitido:
- Uso comercial sin autorización
- Comercialización de predicciones como garantizadas
- Publicidad engañosa sobre la efectividad del sistema
- Uso para promover juego irresponsable

---

## 📞 Soporte y Contacto

### 🐛 Problemas Técnicos
- Revisa la documentación de instalación
- Verifica que todas las dependencias estén instaladas
- Consulta los logs del servidor y del navegador

### 💡 Sugerencias y Mejoras
Este es un proyecto educativo en constante evolución. Las ideas para mejorarlo son siempre bienvenidas.

### ⚠️ Recordatorio Final
**Este sistema es únicamente para análisis estadístico y entretenimiento. La lotería es aleatoria y ningún método puede predecir resultados futuros con certeza. Juega responsablemente.**

---

## 🎉 ¡Disfruta del Predicción!

Esperamos que este sistema te ayude a entender mejor los patrones estadísticos y te proporcione horas de entretenimiento analizando la fascinante Lotería de Medellín.

**¡Que la estadística te acompañe!** 🍀

---

*Última actualización: Mayo 2026 | Versión: 1.0*