import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const UNIDADES = ["gr", "ml", "unid"];

// Alertas de inventario por nivel con color, pedidas por Mauricio en el
// Acta de Compromiso del 5 de agosto de 2026: Ok (verde), Medio
// (naranjado), Bajo (rojo).
// Nota: "orange" está redefinido en tailwind.config.js como un solo color
// de marca (no una escala 50-900), así que bg-orange-100/text-orange-700
// no existen -- se usan valores arbitrarios de Tailwind en su lugar.
const NIVEL_ESTILOS = {
  ok: { texto: "OK", clase: "bg-green-100 text-green-700" },
  medio: { texto: "Medio", clase: "bg-[#fdecd8] text-[#9a4b12]" },
  bajo: { texto: "Bajo", clase: "bg-red-100 text-red-700" },
};

function NivelBadge({ nivel }) {
  const estilo = NIVEL_ESTILOS[nivel] || NIVEL_ESTILOS.ok;
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${estilo.clase}`}>
      {estilo.texto}
    </span>
  );
}

export default function Inventario() {
  const { session } = useAuth();
  const [insumos, setInsumos] = useState([]);
  const [error, setError] = useState("");
  const [mostrarForm, setMostrarForm] = useState(false);
  const [form, setForm] = useState({
    nombre: "",
    cantidad_disponible: "",
    unidad: "gr",
    nivel_minimo: "",
    proveedor_nombre: "",
  });
  const [formError, setFormError] = useState("");
  const esAdmin = session.rol === "administrador";
  const [editandoId, setEditandoId] = useState(null);
  const [nuevaCantidad, setNuevaCantidad] = useState("");

  async function guardarCantidad(id) {
    setError("");
    const valor = parseFloat(nuevaCantidad);
    if (Number.isNaN(valor) || valor < 0) {
      setError("La cantidad debe ser un número mayor o igual a 0.");
      return;
    }
    try {
      await api.actualizarCantidadInsumo(session.token, id, valor);
      setEditandoId(null);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  function cargar() {
    api
      .getInsumos(session.token)
      .then(setInsumos)
      .catch((err) => setError(err.message));
  }

  useEffect(cargar, [session.token]);

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");
    if (!form.nombre.trim() || !form.cantidad_disponible) {
      setFormError("Completa al menos el nombre y la cantidad disponible.");
      return;
    }
    try {
      await api.crearInsumo(session.token, {
        ...form,
        cantidad_disponible: parseFloat(form.cantidad_disponible),
        nivel_minimo: parseFloat(form.nivel_minimo || 0),
      });
      setForm({ nombre: "", cantidad_disponible: "", unidad: "gr", nivel_minimo: "", proveedor_nombre: "" });
      setMostrarForm(false);
      cargar();
    } catch (err) {
      setFormError(err.message);
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Inventario de insumos</h2>
      <p className="text-slate-500 text-sm mb-6">Consulta y gestiona tus insumos disponibles</p>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold text-navy">Insumos</h3>
          {esAdmin && (
            <button
              onClick={() => setMostrarForm((v) => !v)}
              className="bg-orange text-white text-sm font-semibold px-4 py-2 rounded-lg"
            >
              + Agregar insumo
            </button>
          )}
        </div>

        {esAdmin && mostrarForm && (
          <form onSubmit={handleSubmit} className="bg-cream rounded-lg p-4 mb-4 grid grid-cols-2 gap-3">
            <input
              placeholder="Nombre (ej: Mantequilla)"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
            />
            <input
              type="number"
              placeholder="Cantidad disponible"
              value={form.cantidad_disponible}
              onChange={(e) => setForm({ ...form, cantidad_disponible: e.target.value })}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
            />
            <select
              value={form.unidad}
              onChange={(e) => setForm({ ...form, unidad: e.target.value })}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
            >
              {UNIDADES.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Nivel mínimo"
              value={form.nivel_minimo}
              onChange={(e) => setForm({ ...form, nivel_minimo: e.target.value })}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
            />
            <input
              placeholder="Proveedor"
              value={form.proveedor_nombre}
              onChange={(e) => setForm({ ...form, proveedor_nombre: e.target.value })}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm col-span-2"
            />
            {formError && <p className="text-red-600 text-xs col-span-2">{formError}</p>}
            <button type="submit" className="bg-navy text-white text-sm font-semibold rounded-lg py-2 col-span-2">
              Guardar insumo
            </button>
          </form>
        )}

        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
              <th className="py-2">Insumo</th>
              <th>Cantidad</th>
              <th>Nivel mínimo</th>
              <th>Proveedor</th>
              <th>Estado</th>
              {esAdmin && <th></th>}
            </tr>
          </thead>
          <tbody>
            {insumos.map((i) => (
              <tr key={i.id} className={`border-b border-slate-50 ${i.nivel === "bajo" ? "bg-red-50" : ""}`}>
                <td className="py-2">{i.nombre}</td>
                <td>
                  {editandoId === i.id ? (
                    <span className="flex gap-1 items-center">
                      <input
                        type="number"
                        value={nuevaCantidad}
                        onChange={(e) => setNuevaCantidad(e.target.value)}
                        className="border border-slate-200 rounded px-2 py-1 w-24 text-sm"
                      />
                      <button onClick={() => guardarCantidad(i.id)} className="text-xs text-green-700 font-semibold">Guardar</button>
                      <button onClick={() => setEditandoId(null)} className="text-xs text-slate-500">Cancelar</button>
                    </span>
                  ) : (
                    <>{i.cantidad_disponible} {i.unidad}</>
                  )}
                </td>
                <td>{i.nivel_minimo} {i.unidad}</td>
                <td>{i.proveedor_nombre || "—"}</td>
                <td>
                  <NivelBadge nivel={i.nivel} />
                </td>
                {esAdmin && (
                  <td>
                    <button
                      onClick={() => { setEditandoId(i.id); setNuevaCantidad(String(i.cantidad_disponible)); }}
                      className="text-xs text-navy underline"
                    >
                      Actualizar cantidad
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
