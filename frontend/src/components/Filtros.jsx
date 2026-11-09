// Los filtros son "controlados": el valor que se ve en pantalla sale siempre
// del estado de App, y cada cambio avisa hacia arriba con onCambio.
// A diferencia del tablero clásico, acá no hay botón "Aplicar": al cambiar
// un filtro, App vuelve a pedir los datos solo.
export default function Filtros({ filtros, areas, puedeFiltrarMias, onCambio }) {
  // Copio los filtros actuales y cambio solo el campo que corresponde
  const cambiar = (campo, valor) => onCambio({ ...filtros, [campo]: valor })

  return (
    <div className="row g-2 align-items-center mb-3">
      <div className="col-md-4">
        <select
          className="form-select"
          value={filtros.vista}
          onChange={(e) => cambiar('vista', e.target.value)}
        >
          <option value="hoy">Hoy (y atrasadas)</option>
          <option value="semana">Esta semana (y atrasadas)</option>
          <option value="todas">Todas las abiertas</option>
        </select>
      </div>
      <div className="col-md-4">
        <select
          className="form-select"
          value={filtros.area}
          onChange={(e) => cambiar('area', e.target.value)}
        >
          <option value="">Todas las áreas</option>
          {areas.map((a) => (
            <option key={a.valor} value={a.valor}>
              {a.etiqueta}
            </option>
          ))}
        </select>
      </div>
      <div className="col-md-4">
        {/* Si el usuario no tiene ficha de Persona, "mis tareas" no tiene sentido */}
        {puedeFiltrarMias && (
          <div className="form-check">
            <input
              className="form-check-input"
              type="checkbox"
              id="mias"
              checked={filtros.mias}
              onChange={(e) => cambiar('mias', e.target.checked)}
            />
            <label className="form-check-label" htmlFor="mias">
              Solo mis tareas
            </label>
          </div>
        )}
      </div>
    </div>
  )
}
