// Los colores son los mismos que usan las etiquetas de cada tarea
// (definidos en tareas/models.py, COLORES_ALERTA). Si algún día cambio uno,
// hay que cambiarlo también acá: es la única duplicación que tiene el proyecto.
const TARJETAS = [
  { clave: 'vencidas', titulo: 'Vencidas', color: '#c62828' },
  { clave: 'por_vencer', titulo: 'Por vencer (próximos días)', color: '#f9a825' },
  { clave: 'completadas_hoy', titulo: 'Completadas hoy', color: '#2e7d32' },
]

// Recibe los números por "props" y los dibuja. No guarda estado propio:
// es un componente de presentación.
export default function Contadores({ contadores }) {
  return (
    <div className="row g-3 mb-4">
      {TARJETAS.map((t) => (
        <div className="col-md-4" key={t.clave}>
          <div className="card" style={{ borderLeft: `6px solid ${t.color}` }}>
            <div className="card-body py-2">
              <div className="text-muted small">{t.titulo}</div>
              <div className="fs-3 fw-bold">{contadores[t.clave]}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
