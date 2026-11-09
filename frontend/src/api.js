// Todas las llamadas al servidor están acá, juntas. Los componentes no
// conocen las direcciones ni los detalles de fetch: solo llaman a estas funciones.

// Error propio, para que los componentes sepan qué código devolvió el servidor
export class ErrorApi extends Error {
  constructor(estado, detalle) {
    super(detalle)
    this.estado = estado
  }
}

// Django guarda un token anti-falsificación (CSRF) en una cookie. Para hacer
// un POST tengo que leerlo y mandarlo en un encabezado: así el servidor sabe
// que el pedido salió de nuestra propia página y no de otro sitio.
function leerCookie(nombre) {
  const par = document.cookie.split('; ').find((c) => c.startsWith(nombre + '='))
  return par ? decodeURIComponent(par.split('=')[1]) : ''
}

async function leerRespuesta(respuesta) {
  if (respuesta.ok) return respuesta.json()
  // Si el servidor mandó un mensaje ("detalle"), lo uso; si no, uno genérico
  let detalle = 'Error al comunicarse con el servidor.'
  try {
    const cuerpo = await respuesta.json()
    if (cuerpo.detalle) detalle = cuerpo.detalle
  } catch {
    // la respuesta no era JSON: dejo el mensaje genérico
  }
  throw new ErrorApi(respuesta.status, detalle)
}

// GET /api/tablero/?vista=...&area=...&mias=1
export async function obtenerTablero(filtros, senal) {
  const parametros = new URLSearchParams()
  parametros.set('vista', filtros.vista)
  if (filtros.area) parametros.set('area', filtros.area)
  if (filtros.mias) parametros.set('mias', '1')

  const respuesta = await fetch(`/api/tablero/?${parametros}`, {
    // same-origin: manda la cookie de sesión del login de Django
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
    // senal permite cancelar el pedido si ya no hace falta
    signal: senal,
  })
  return leerRespuesta(respuesta)
}

// POST /api/tareas/<id>/estado/
export async function cambiarEstado(idTarea, estado) {
  const respuesta = await fetch(`/api/tareas/${idTarea}/estado/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': leerCookie('csrftoken'),
    },
    body: JSON.stringify({ estado }),
  })
  return leerRespuesta(respuesta)
}
