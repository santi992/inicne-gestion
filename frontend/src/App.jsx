import { useEffect, useRef, useState } from 'react'
import { cambiarEstado, obtenerTablero } from './api.js'
import Contadores from './components/Contadores.jsx'
import Filtros from './components/Filtros.jsx'
import TablaTareas from './components/TablaTareas.jsx'

// Cada cuántos milisegundos se vuelve a pedir el tablero al servidor
const INTERVALO_MS = 30_000

// Convierte el error del servidor en un mensaje para el usuario
function mensajeDeError(error) {
  // 403: la sesión venció o el usuario cerró sesión en otra pestaña
  if (error.estado === 401 || error.estado === 403) {
    return 'Tu sesión venció o no tenés permiso. Volvé a ingresar.'
  }
  return error.message || 'No se pudo actualizar el tablero.'
}

export default function App() {
  // Los filtros son el estado que el usuario controla
  const [filtros, setFiltros] = useState({ vista: 'semana', area: '', mias: false })
  // Los datos son lo que responde el servidor (null hasta la primera respuesta)
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')
  // Id de la tarea que se está modificando (para bloquear sus botones un momento)
  const [ocupada, setOcupada] = useState(null)
  // Guardo la función de recarga en una "ref" para poder llamarla desde un
  // botón, fuera del useEffect, sin volver a crearla en cada dibujo
  const recargar = useRef(() => {})

  // Este efecto se ejecuta al abrir la página y cada vez que cambian los filtros
  useEffect(() => {
    let controlador = new AbortController()

    async function cargar() {
      // Si una consulta anterior seguía en camino, la cancelo: no quiero
      // que una respuesta vieja pise a una más nueva
      controlador.abort()
      controlador = new AbortController()
      try {
        const respuesta = await obtenerTablero(filtros, controlador.signal)
        setDatos(respuesta)
        setError('')
      } catch (e) {
        // Una consulta cancelada a propósito no es un error
        if (e.name === 'AbortError') return
        setError(mensajeDeError(e))
      }
    }

    recargar.current = cargar
    cargar()

    // Actualización automática. Si la pestaña está oculta no pido nada:
    // no tiene sentido gastar al servidor para una pantalla que nadie mira.
    const temporizador = setInterval(() => {
      if (!document.hidden) cargar()
    }, INTERVALO_MS)

    // Al volver a la pestaña actualizo enseguida, sin esperar el intervalo
    function alCambiarVisibilidad() {
      if (!document.hidden) cargar()
    }
    document.addEventListener('visibilitychange', alCambiarVisibilidad)

    // Función de limpieza: React la ejecuta antes de repetir el efecto o al
    // cerrar la página. Sin esto quedarían temporizadores funcionando de más.
    return () => {
      clearInterval(temporizador)
      document.removeEventListener('visibilitychange', alCambiarVisibilidad)
      controlador.abort()
    }
  }, [filtros])

  async function alCambiarEstado(idTarea, estado) {
    setOcupada(idTarea)
    try {
      await cambiarEstado(idTarea, estado)
      // Después de cambiar, pido todo de nuevo: así se actualizan también
      // los contadores y las reglas (por ejemplo, las completadas)
      await recargar.current()
    } catch (e) {
      setError(mensajeDeError(e))
    } finally {
      setOcupada(null)
    }
  }

  // Hasta la primera respuesta no hay nada que mostrar
  if (!datos) {
    return error ? (
      <div className="alert alert-danger">{error}</div>
    ) : (
      <div className="text-muted">Cargando tablero…</div>
    )
  }

  const hora = new Date(datos.actualizado).toLocaleTimeString('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  return (
    <>
      {error && <div className="alert alert-danger">{error}</div>}

      <Contadores contadores={datos.contadores} />

      <Filtros
        filtros={filtros}
        areas={datos.areas}
        puedeFiltrarMias={datos.usuario.persona_id !== null}
        onCambio={setFiltros}
      />

      <TablaTareas tareas={datos.tareas} ocupada={ocupada} onCambiarEstado={alCambiarEstado} />

      <div className="d-flex justify-content-between align-items-center mt-3 text-muted small">
        <span>
          Actualizado a las {hora} · se actualiza solo cada {INTERVALO_MS / 1000} segundos
        </span>
        <button className="btn btn-sm btn-outline-secondary" onClick={() => recargar.current()}>
          Actualizar ahora
        </button>
      </div>
    </>
  )
}
