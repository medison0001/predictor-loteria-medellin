/**
 * Aplicación JavaScript para el Predictor de Lotería de Medellín
 * Maneja toda la interacción frontend y comunicación con la API
 */

// === CONFIGURACIÓN GLOBAL ===
const CONFIG = {
    API_BASE: '',  // Base URL para las llamadas API
    ENDPOINTS: {
        PREDICCION: '/api/prediccion',
        HISTORIAL: '/api/historial',
        RESULTADO: '/api/resultado',
        ESTADISTICAS: '/api/estadisticas',
        RETROALIMENTACION: '/api/retroalimentacion'
    },
    TIMEOUTS: {
        API_CALL: 10000,  // 10 segundos
        RETRY_DELAY: 2000 // 2 segundos
    }
};

// === ESTADO DE LA APLICACIÓN ===
const AppState = {
    prediccionActual: null,
    historialCargado: false,
    estadisticasCargadas: false,
    ultimaRetroalimentacion: null
};

// === UTILIDADES ===
const Utils = {
    /**
     * Realiza una petición HTTP con manejo de errores
     */
    async fetchAPI(endpoint, options = {}) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUTS.API_CALL);
            
            const response = await fetch(CONFIG.API_BASE + endpoint, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status} - ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (!data.success && data.error) {
                throw new Error(data.error);
            }
            
            return data;
            
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('La petición tardó demasiado tiempo');
            }
            throw error;
        }
    },
    
    /**
     * Formatea un número con ceros a la izquierda
     */
    formatearNumero(numero, digitos) {
        return numero.toString().padStart(digitos, '0');
    },
    
    /**
     * Convierte fecha a formato español legible
     */
    formatearFecha(fechaStr) {
        // Convertir formato dd/mm/yyyy a formato ISO yyyy-mm-dd
        const partes = fechaStr.split('/');
        if (partes.length === 3) {
            const [dia, mes, año] = partes;
            const fechaISO = `${año}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}`;
            const fecha = new Date(fechaISO + 'T00:00:00');
            
            if (!isNaN(fecha.getTime())) {
                return fecha.toLocaleDateString('es-CO', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            }
        }
        
        // Si hay error, devolver la fecha original
        return fechaStr;
    },
    
    /**
     * Muestra un mensaje de notificación
     */
    mostrarNotificacion(mensaje, tipo = 'info') {
        // Crear elemento de notificación
        const notificacion = document.createElement('div');
        notificacion.className = `notificacion notificacion-${tipo}`;
        notificacion.textContent = mensaje;
        
        // Estilos inline para la notificación
        Object.assign(notificacion.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem 2rem',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '600',
            zIndex: '9999',
            maxWidth: '400px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            animation: 'aparecer 0.3s ease-out'
        });
        
        // Colores según el tipo
        const colores = {
            'success': '#48bb78',
            'error': '#f56565',
            'warning': '#ed8936',
            'info': '#4299e1'
        };
        
        notificacion.style.backgroundColor = colores[tipo] || colores.info;
        
        document.body.appendChild(notificacion);
        
        // Eliminar después de 5 segundos
        setTimeout(() => {
            notificacion.style.animation = 'none';
            notificacion.style.opacity = '0';
            setTimeout(() => {
                if (notificacion.parentNode) {
                    notificacion.parentNode.removeChild(notificacion);
                }
            }, 300);
        }, 5000);
    },
    
    /**
     * Valida un formulario
     */
    validarFormulario(formulario) {
        const errores = [];
        const campos = formulario.querySelectorAll('input[required]');
        
        campos.forEach(campo => {
            if (!campo.value.trim()) {
                errores.push(`El campo ${campo.labels[0].textContent} es obligatorio`);
                campo.classList.add('error');
            } else {
                campo.classList.remove('error');
            }
            
            // Validación específica para fecha DD/MM/YYYY
            if (campo.id === 'fechaResultado' && campo.value.trim()) {
                const fechaRegex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/[0-9]{4}$/;
                if (!fechaRegex.test(campo.value.trim())) {
                    errores.push('La fecha debe estar en formato DD/MM/AAAA');
                    campo.classList.add('error');
                }
            }
        });
        
        return errores;
    }
};

// === CONTROLADOR DE PREDICCIÓN ===
const PrediccionController = {
    /**
     * Carga y muestra la predicción actual
     */
    async cargarPrediccion() {
        const loadingElement = document.getElementById('prediccionLoading');
        const contenidoElement = document.getElementById('prediccionContenido');
        
        try {
            loadingElement.style.display = 'block';
            contenidoElement.style.display = 'none';
            
            console.log('🔮 Cargando predicción...');
            const response = await Utils.fetchAPI(CONFIG.ENDPOINTS.PREDICCION);
            
            if (response.success && response.data) {
                AppState.prediccionActual = response.data;
                this.mostrarPrediccion(response.data);
                console.log('✅ Predicción cargada exitosamente');
            } else {
                throw new Error('No se pudo obtener la predicción');
            }
            
        } catch (error) {
            console.error('❌ Error cargando predicción:', error);
            Utils.mostrarNotificacion(`Error cargando predicción: ${error.message}`, 'error');
            this.mostrarErrorPrediccion(error.message);
        } finally {
            loadingElement.style.display = 'none';
        }
    },
    
    /**
     * Muestra la predicción en la interfaz
     */
    mostrarPrediccion(prediccion) {
        // Actualizar números predichos
        const numeroStr = Utils.formatearNumero(prediccion.numero_predicho, 4);
        const serieStr = Utils.formatearNumero(prediccion.serie_predicha, 3);
        
        // Mostrar dígitos del número con animación
        for (let i = 0; i < 4; i++) {
            const digitoElement = document.getElementById(`digito${i + 1}`);
            if (digitoElement) {
                digitoElement.textContent = numeroStr[i];
                digitoElement.classList.add('aparecer');
            }
        }
        
        // Mostrar dígitos de la serie
        for (let i = 0; i < 3; i++) {
            const serieElement = document.getElementById(`serie${i + 1}`);
            if (serieElement) {
                serieElement.textContent = serieStr[i];
                serieElement.classList.add('aparecer');
            }
        }
        
        // Actualizar nivel de confianza
        const confianzaElement = document.getElementById('confianzaNivel');
        if (confianzaElement) {
            confianzaElement.textContent = prediccion.confianza.toUpperCase();
            confianzaElement.className = `confianza-nivel ${prediccion.confianza}`;
        }
        
        // Actualizar información del próximo sorteo
        if (prediccion.proximo_sorteo) {
            this.mostrarProximoSorteo(prediccion.proximo_sorteo);
        }
        
        // Mostrar top 5 candidatos
        this.mostrarCandidatos(prediccion.top5_numeros, 'top5Numeros', 'numero');
        this.mostrarCandidatos(prediccion.top5_series, 'top5Series', 'serie');
        
        // Mostrar explicación
        const explicacionElement = document.getElementById('explicacionTexto');
        if (explicacionElement && prediccion.explicacion) {
            explicacionElement.innerHTML = this.formatearExplicacion(prediccion.explicacion);
        }
        
        // Mostrar contenido principal
        document.getElementById('prediccionContenido').style.display = 'block';
    },
    
    /**
     * Muestra información del próximo sorteo
     */
    mostrarProximoSorteo(sorteoInfo) {
        const infoElement = document.getElementById('infoSorteo');
        if (!infoElement) return;
        
        const fechaFormateada = Utils.formatearFecha(sorteoInfo.fecha);
        
        let contadorTexto = '';
        if (sorteoInfo.dias_restantes > 0) {
            contadorTexto = `En ${sorteoInfo.dias_restantes} día${sorteoInfo.dias_restantes > 1 ? 's' : ''}`;
        } else if (sorteoInfo.dias_restantes === 0) {
            contadorTexto = '¡Hoy!';
        } else {
            contadorTexto = 'Fecha pasada';
        }
        
        // Usar numero_sorteo si existe, si no usar sorteo como fallback
        const numeroSorteo = sorteoInfo.numero_sorteo || sorteoInfo.sorteo || 'TBD';
        
        infoElement.innerHTML = `
            <span class="fecha-sorteo">${fechaFormateada}</span>
            <span class="contador-dias">${contadorTexto}</span>
        `;
    },
    
    /**
     * Muestra los candidatos (números o series)
     */
    mostrarCandidatos(candidatos, elementId, tipo) {
        const listaElement = document.getElementById(elementId);
        if (!listaElement || !candidatos) return;
        
        listaElement.innerHTML = '';
        
        candidatos.forEach((candidato, index) => {
            const li = document.createElement('li');
            
            const valor = tipo === 'numero' 
                ? candidato.numero_formateado || Utils.formatearNumero(candidato.numero, 4)
                : candidato.serie_formateada || Utils.formatearNumero(candidato.serie, 3);
            
            li.innerHTML = `
                <span class="candidato-numero">#${index + 1} - ${valor}</span>
                <span class="candidato-puntuacion">${candidato.puntuacion.toFixed(1)}%</span>
            `;
            
            listaElement.appendChild(li);
        });
    },
    
    /**
     * Formatea la explicación con markdown básico
     */
    formatearExplicacion(texto) {
        return texto
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/🎯|✅|⚠️|🔻|📊|⚠️/g, '<span style="font-size: 1.2em;">$&</span>');
    },
    
    /**
     * Muestra error en la predicción
     */
    mostrarErrorPrediccion(error) {
        const contenidoElement = document.getElementById('prediccionContenido');
        contenidoElement.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--color-error);">
                <h3>❌ Error al cargar predicción</h3>
                <p>${error}</p>
                <button onclick="PrediccionController.cargarPrediccion()" class="boton-principal" style="margin-top: 1rem;">
                    🔄 Intentar de nuevo
                </button>
            </div>
        `;
        contenidoElement.style.display = 'block';
    }
};

// === CONTROLADOR DE HISTORIAL ===
const HistorialController = {
    /**
     * Carga el historial de resultados
     */
    async cargarHistorial(limite = 20) {
        if (AppState.historialCargado) return;
        
        const loadingElement = document.getElementById('historialLoading');
        const contenedorElement = document.getElementById('historialContenedor');
        
        try {
            loadingElement.style.display = 'block';
            contenedorElement.style.display = 'none';
            
            console.log('📊 Cargando historial...');
            const response = await Utils.fetchAPI(`${CONFIG.ENDPOINTS.HISTORIAL}?limite=${limite}`);
            
            if (response.success && response.data) {
                this.mostrarHistorial(response.data);
                AppState.historialCargado = true;
                console.log(`✅ Historial cargado: ${response.data.length} registros`);
            } else {
                throw new Error('No se pudo cargar el historial');
            }
            
        } catch (error) {
            console.error('❌ Error cargando historial:', error);
            Utils.mostrarNotificacion(`Error cargando historial: ${error.message}`, 'error');
        } finally {
            loadingElement.style.display = 'none';
        }
    },
    
    /**
     * Muestra el historial en la tabla
     */
    mostrarHistorial(resultados) {
        const tbody = document.getElementById('tablaHistorialBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        resultados.forEach(resultado => {
            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>${resultado.fecha}</td>
                <td>${resultado.sorteo}</td>
                <td><span class="numero-historial">${resultado.numero}</span></td>
                <td><span class="serie-historial">${resultado.serie}</span></td>
                <td>${resultado.dia_semana}</td>
            `;
            
            tbody.appendChild(fila);
        });
        
        document.getElementById('historialContenedor').style.display = 'block';
    }
};

// === CONTROLADOR DE FORMULARIOS ===
const FormularioController = {
    /**
     * Inicializa los formularios
     */
    inicializar() {
        const formulario = document.getElementById('formularioResultado');
        if (formulario) {
            formulario.addEventListener('submit', this.manejarEnvioResultado.bind(this));
        }
        
        // Configurar fecha por defecto (hoy)
        const campoFecha = document.getElementById('fechaResultado');
        if (campoFecha) {
            const hoy = new Date().toISOString().split('T')[0];
            campoFecha.value = hoy;
        }
    },
    
    /**
     * Maneja el envío del formulario de resultado
     */
    async manejarEnvioResultado(event) {
        event.preventDefault();
        
        const formulario = event.target;
        const errores = Utils.validarFormulario(formulario);
        
        if (errores.length > 0) {
            Utils.mostrarNotificacion(`Errores en el formulario:\n${errores.join('\n')}`, 'error');
            return;
        }
        
        // Recopilar datos del formulario
        const formData = new FormData(formulario);
        const datos = {
            fecha: formData.get('fecha'),
            sorteo: parseInt(formData.get('sorteo')),
            numero: parseInt(formData.get('numero')),
            serie: parseInt(formData.get('serie'))
        };
        
        // Validaciones adicionales
        if (datos.numero < 0 || datos.numero > 9999) {
            Utils.mostrarNotificacion('El número debe estar entre 0000 y 9999', 'error');
            return;
        }
        
        if (datos.serie < 0 || datos.serie > 999) {
            Utils.mostrarNotificacion('La serie debe estar entre 000 y 999', 'error');
            return;
        }
        
        try {
            // Deshabilitar formulario durante envío
            const boton = formulario.querySelector('button[type="submit"]');
            const textoOriginal = boton.innerHTML;
            boton.innerHTML = '<span class="loader"></span> Procesando...';
            boton.disabled = true;
            
            console.log('💾 Enviando resultado:', datos);
            
            const response = await Utils.fetchAPI(CONFIG.ENDPOINTS.RESULTADO, {
                method: 'POST',
                body: JSON.stringify(datos)
            });
            
            if (response.success) {
                Utils.mostrarNotificacion('✅ Resultado guardado y evaluado exitosamente', 'success');
                
                // Mostrar retroalimentación si está disponible
                if (response.data && response.data.retroalimentacion) {
                    RetroalimentacionController.mostrarRetroalimentacion(response.data.retroalimentacion);
                }
                
                // Limpiar solo los campos de resultado (mantener fecha y sorteo para el próximo)
                document.getElementById('numeroResultado').value = '';
                document.getElementById('serieResultado').value = '';
                
                // Recargar datos
                AppState.historialCargado = false;
                AppState.estadisticasCargadas = false;
                
                await Promise.all([
                    PrediccionController.cargarPrediccion(),
                    HistorialController.cargarHistorial(),
                    EstadisticasController.cargarEstadisticas()
                ]);
                
                // Reinicializar formulario con datos del nuevo próximo sorteo
                const fechaInput = document.getElementById('fechaResultado');
                const sorteoInput = document.getElementById('sorteoResultado');
                await this.inicializarFormularioConDatos(fechaInput, sorteoInput);
                
            } else {
                throw new Error(response.error || 'Error desconocido al guardar');
            }
            
        } catch (error) {
            console.error('❌ Error enviando resultado:', error);
            Utils.mostrarNotificacion(`Error al guardar resultado: ${error.message}`, 'error');
        } finally {
            // Rehabilitar formulario
            const boton = formulario.querySelector('button[type="submit"]');
            boton.innerHTML = textoOriginal;
            boton.disabled = false;
        }
    },

    /**
     * Inicializa el formulario con datos del próximo sorteo
     */
    async inicializarFormularioConDatos(campoFecha, campoSorteo) {
        try {
            console.log('📅 Obteniendo datos del próximo sorteo...');
            
            // Obtener datos de la predicción que incluye el próximo sorteo
            const response = await Utils.fetchAPI(CONFIG.ENDPOINTS.PREDICCION);
            
            if (response.success && response.data && response.data.proximo_sorteo) {
                const proximo = response.data.proximo_sorteo;
                
                // Establecer fecha (formato yyyy-mm-dd para input date)
                const fechaParts = proximo.fecha_corta.split('/'); // dd/mm/yyyy
                const fechaISO = `${fechaParts[2]}-${fechaParts[1].padStart(2, '0')}-${fechaParts[0].padStart(2, '0')}`;
                campoFecha.value = fechaISO;
                
                // Establecer número de sorteo
                campoSorteo.value = proximo.numero_sorteo;
                
                console.log(`✅ Formulario inicializado - Próximo sorteo: ${proximo.fecha_corta} #${proximo.numero_sorteo}`);
            } else {
                // Fallback: fecha manual (viernes siguiente)
                console.log('⚠️ No se pudo obtener datos del próximo sorteo, usando fallback');
                campoFecha.value = '2026-05-08'; // 8 de Mayo
                campoSorteo.value = 4834; // Número estimado
            }
        } catch (error) {
            console.error('❌ Error inicializando formulario:', error);
            // Fallback en caso de error
            campoFecha.value = '2026-05-08';
            campoSorteo.value = 4834;
        }
    }
};

// === CONTROLADOR DE RETROALIMENTACIÓN ===
const RetroalimentacionController = {
    /**
     * Muestra la retroalimentación del sistema
     */
    mostrarRetroalimentacion(retroalimentacion) {
        const panel = document.getElementById('panelRetroalimentacion');
        const contenido = document.getElementById('retroalimentacionContenido');
        
        if (!panel || !contenido) return;
        
        // Formatear mensaje con markdown básico
        let mensaje = retroalimentacion.mensaje || '';
        mensaje = mensaje
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/🎲|🎉|🎯|👏|📊|😔|🧠|⚙️|📈|📉|🔮/g, '<span style="font-size: 1.2em;">$&</span>');
        
        contenido.innerHTML = `
            <div class="retroalimentacion-mensaje">
                ${mensaje}
            </div>
            <div class="retroalimentacion-fecha" style="margin-top: 1rem; text-align: right; opacity: 0.8;">
                ${retroalimentacion.fecha || new Date().toLocaleDateString('es-CO')}
            </div>
        `;
        
        // Mostrar panel con animación
        panel.style.display = 'block';
        panel.classList.add('aparecer');
        
        // Scroll suave hacia el panel
        setTimeout(() => {
            panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
    },
    
    /**
     * Carga la última retroalimentación disponible
     */
    async cargarUltimaRetroalimentacion() {
        try {
            const response = await Utils.fetchAPI(CONFIG.ENDPOINTS.RETROALIMENTACION);
            
            if (response.success && response.data) {
                this.mostrarRetroalimentacion(response.data);
            }
            
        } catch (error) {
            console.log('ℹ️ No hay retroalimentación previa disponible');
        }
    }
};

// === CONTROLADOR DE ESTADÍSTICAS ===
const EstadisticasController = {
    /**
     * Carga las estadísticas generales
     */
    async cargarEstadisticas() {
        if (AppState.estadisticasCargadas) return;
        
        try {
            console.log('📈 Cargando estadísticas...');
            const response = await Utils.fetchAPI(CONFIG.ENDPOINTS.ESTADISTICAS);
            
            if (response.success && response.data) {
                this.mostrarEstadisticas(response.data);
                AppState.estadisticasCargadas = true;
                console.log('✅ Estadísticas cargadas');
            }
            
        } catch (error) {
            console.error('❌ Error cargando estadísticas:', error);
        }
    },
    
    /**
     * Muestra las estadísticas en la interfaz
     */
    mostrarEstadisticas(stats) {
        // Mostrar números calientes
        this.mostrarListaNumeros(stats.numeros_calientes, 'listaCalientes', 'frecuencia');
        
        // Mostrar números fríos
        this.mostrarListaNumeros(stats.numeros_frios, 'listaFrios', 'descripcion');
        
        // Mostrar estadísticas de precisión
        this.mostrarPrecision(stats.precision);
    },
    
    /**
     * Muestra una lista de números (calientes o fríos)
     */
    mostrarListaNumeros(numeros, elementId, campo) {
        const lista = document.getElementById(elementId);
        if (!lista || !numeros) return;
        
        lista.innerHTML = '';
        
        numeros.forEach(item => {
            const li = document.createElement('li');
            
            let valorSecundario = '';
            if (campo === 'frecuencia') {
                valorSecundario = `${item.frecuencia} (${item.porcentaje}%)`;
            } else if (campo === 'descripcion') {
                valorSecundario = item.descripcion;
            }
            
            li.innerHTML = `
                <span>${item.numero}</span>
                <span style="font-size: 0.9em; opacity: 0.8;">${valorSecundario}</span>
            `;
            
            lista.appendChild(li);
        });
    },
    
    /**
     * Muestra estadísticas de precisión del sistema
     */
    mostrarPrecision(precision) {
        const contenedor = document.getElementById('precisionContenido');
        if (!contenedor || !precision) return;
        
        if (precision.sin_datos) {
            contenedor.innerHTML = '<p style="text-align: center; color: #718096;">Aún no hay evaluaciones suficientes</p>';
            return;
        }
        
        const items = [
            {
                label: 'Total de evaluaciones',
                valor: precision.total_evaluaciones
            },
            {
                label: 'Aciertos de número exacto',
                valor: `${precision.aciertos_numero} (${precision.tasa_acierto_numero?.toFixed(1) || 0}%)`
            },
            {
                label: 'Aciertos de serie',
                valor: `${precision.aciertos_serie} (${precision.tasa_acierto_serie?.toFixed(1) || 0}%)`
            }
        ];
        
        contenedor.innerHTML = items.map(item => `
            <div class="precision-item">
                <span class="precision-label">${item.label}</span>
                <span class="precision-valor">${item.valor}</span>
            </div>
        `).join('');
    }
};

// === INICIALIZACIÓN DE LA APLICACIÓN ===
class LoteriaMedellinApp {
    constructor() {
        this.inicializada = false;
    }
    
    /**
     * Inicializa toda la aplicación
     */
    async inicializar() {
        if (this.inicializada) return;
        
        console.log('🚀 Inicializando aplicación Lotería de Medellín...');
        
        try {
            // Inicializar controladores
            FormularioController.inicializar();
            
            // Cargar datos iniciales en paralelo
            await Promise.all([
                PrediccionController.cargarPrediccion(),
                HistorialController.cargarHistorial(),
                EstadisticasController.cargarEstadisticas(),
                RetroalimentacionController.cargarUltimaRetroalimentacion()
            ]);
            
            this.inicializada = true;
            console.log('✅ Aplicación inicializada correctamente');
            
            // Mostrar notificación de bienvenida
            Utils.mostrarNotificacion('🎉 ¡Bienvenido al Predictor de Lotería de Medellín!', 'success');
            
        } catch (error) {
            console.error('❌ Error inicializando aplicación:', error);
            Utils.mostrarNotificacion(`Error inicializando aplicación: ${error.message}`, 'error');
        }
    }
    
    /**
     * Actualiza todos los datos de la aplicación
     */
    async actualizarTodo() {
        console.log('🔄 Actualizando todos los datos...');
        
        // Reset de estados
        AppState.historialCargado = false;
        AppState.estadisticasCargadas = false;
        
        try {
            await Promise.all([
                PrediccionController.cargarPrediccion(),
                HistorialController.cargarHistorial(),
                EstadisticasController.cargarEstadisticas()
            ]);
            
            Utils.mostrarNotificacion('✅ Datos actualizados correctamente', 'success');
            
        } catch (error) {
            console.error('❌ Error actualizando datos:', error);
            Utils.mostrarNotificacion(`Error actualizando datos: ${error.message}`, 'error');
        }
    }
}

// === INSTANCIA GLOBAL DE LA APLICACIÓN ===
const app = new LoteriaMedellinApp();

// === INICIALIZACIÓN CUANDO EL DOM ESTÁ LISTO ===
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM cargado, iniciando aplicación...');
    app.inicializar();
});

// === MANEJO DE ERRORES GLOBALES ===
window.addEventListener('error', (event) => {
    console.error('❌ Error global:', event.error);
    Utils.mostrarNotificacion('Error inesperado en la aplicación', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('❌ Promise rechazada:', event.reason);
    Utils.mostrarNotificacion('Error de red o conexión', 'error');
});

// === EXPORTAR PARA USO GLOBAL ===
window.LoteriaMedellinApp = {
    app,
    Utils,
    PrediccionController,
    HistorialController,
    FormularioController,
    RetroalimentacionController,
    EstadisticasController
};