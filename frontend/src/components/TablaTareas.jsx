// La fecha llega como "2026-11-09". La separo en partes en lugar de usar Date,
// porque Date interpreta ese texto como hora UTC y en Argentina (UTC-3)
// mostraría el día anterior.
function formatearFecha(texto) {
  const [anio, mes, dia] = texto.split('-')
  return `${dia}/${mes}/${anio}`
}

function FilaTarea({ tarea, ocupada, onCambiarEstado }) {
  const bloqueada = ocupada === tarea.id

  return (
    <tr>
      <td>
        <strong>{tarea.titulo}</strong>
        {tarea.proyecto && <span className="badge text-bg-light border ms-1">{tarea.proyecto}</span>}
        {tarea.descripcion && (
          <div className="text-muted small">
            {tarea.descripcion.length > 80
              ? tarea.descripcion.slice(0, 79) + '…'
              : tarea.descripcion}
          </div>
        )}
      </td>
      <td>{tarea.area_display}</td>
      <td>
        {/* Resalto mis propias tareas dentro de la lista completa */}
        {tarea.es_mia ? (
          <>
            <strong>{tarea.responsable_nombre}</strong>{' '}
            <span className="badge text-bg-primary">Vos</span>
          </>
        ) : (
          tarea.responsable_nombre
        )}
      </td>
      <td>{formatearFecha(tarea.fecha_limite)}</td>
      <td>{tarea.prioridad_display}</td>
      <td>{tarea.estado_display}</td>
      <td>
        {/* El servidor ya calculó los colores: acá solo se aplican */}
        <span
          className="badge"
          style={{ background: tarea.color_fondo, color: tarea.color_texto }}
        >
          {tarea.etiqueta_alerta}
        </span>
      </td>
      <td className="text-end text-nowrap">
        {tarea.puede_cambiar_estado && (
          <>
            {tarea.estado === 'PEND' && (
              <button
                className="btn btn-sm btn-outline-primary me-1"
                disabled={bloqueada}
                onClick={() => onCambiarEstado(tarea.id, 'CURSO')}
              >
                Iniciar
              </button>
            )}
            {tarea.estado !== 'HECHA' ? (
              <button
                className="btn btn-sm btn-outline-success"
                disabled={bloqueada}
                onClick={() => onCambiarEstado(tarea.id, 'HECHA')}
              >
                Completar
              </button>
            ) : (
              <button
                className="btn btn-sm btn-outline-secondary"
                disabled={bloqueada}
                onClick={() => onCambiarEstado(tarea.id, 'PEND')}
              >
                Reabrir
              </button>
            )}
          </>
        )}
      </td>
    </tr>
  )
}

export default function TablaTareas({ tareas, ocupada, onCambiarEstado }) {
  return (
    <div className="table-responsive bg-white border rounded">
      <table className="table table-hover align-middle mb-0">
        <thead className="table-light">
          <tr>
            <th>Tarea</th>
            <th>Área</th>
            <th>Responsable</th>
            <th>Fecha límite</th>
            <th>Prioridad</th>
            <th>Estado</th>
            <th>Alerta</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {tareas.length === 0 ? (
            <tr>
              <td colSpan={8} className="text-center text-muted py-4">
                No hay tareas para mostrar con estos filtros.
              </td>
            </tr>
          ) : (
            // key ayuda a React a saber qué fila es cuál cuando la lista cambia
            tareas.map((t) => (
              <FilaTarea key={t.id} tarea={t} ocupada={ocupada} onCambiarEstado={onCambiarEstado} />
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
