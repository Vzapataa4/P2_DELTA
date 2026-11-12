import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const fmt = (n) => `$${Math.round(n).toLocaleString("es-CO")}`;
const FORM_VACIO = { insumo_nombre: "", cantidad: "", costo_total: "", proveedor_nombre: "" };

// HU-07 Ver compras por proveedor. Registrar una compra también suma la
// cantidad al inventario, así no hay que actualizarla a mano después.
export default function Compras() {
  const { session } = useAuth();
  const [insumos, setInsumos] = useState([]);
  const [porProveedor, setPorProveedor] = useState([]);
  const [compras, setCompras] = useState([]);
  const [form, setForm] = useState(FORM_VACIO);
  const [filtros, setFiltros] = useState({ desde: "", hasta: "" });
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  function cargar(f = filtros) {
    Promise.all([
      api.getInsumos(session.token),
      api.getComprasPorProveedor(session.token, f),
      api.getCompras(session.token, f),
    ])
      .then(([i, p, c]) => {
        setInsumos(i);
        setPorProveedor(p);
        setCompras(c);
        setForm((prev) => (prev.insumo_nombre ? prev : { ...prev, insumo_nombre: i[0]?.nombre || "" }));
      })
      .catch((err) => setError(err.message));
  }

  useEffect(cargar, [session.token]); // eslint-disable-line react-hooks/exhaustive-deps

  const insumoElegido = insumos.find((i) => i.nombre === form.insumo_nombre);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setAviso("");
    const cantidad = parseFloat(form.cantidad);
    const costo = parseFloat(form.costo_total);
    if (!form.insumo_nombre || !(cantidad > 0) || Number.isNaN(costo) || costo < 0) {
      setError("Elige el insumo y escribe la cantidad comprada y cuánto pagaste.");
      return;
    }
    try {
      const compra = await api.registrarCompra(session.token, {
        insumo_nombre: form.insumo_nombre,
        cantidad,
        costo_total: costo,
        proveedor_nombre: form.proveedor_nombre.trim() || null,
      });
      setAviso(
        `Compra guardada: ${compra.cantidad} ${compra.unidad} de ${compra.insumo} a ${compra.proveedor}. El inventario ya se actualizó.`
      );
      setForm({ ...FORM_VACIO, insumo_nombre: form.insumo_nombre });
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Compras a proveedores</h2>
      <p className="text-slate-500 text-sm mb-6">
        Registra lo que le compras a cada proveedor y mira cuánto le has pagado
      </p>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-5 max-w-xl mb-6 grid grid-cols-2 gap-3">
        <h3 className="text-sm font-semibold text-navy col-span-2">Registrar una compra</h3>
        <label className="text-xs text-slate-600 col-span-2">
          Insumo
          <select
            value={form.insumo_nombre}
            onChange={(e) => setForm({ ...form, insumo_nombre: e.target.value })}
            className="block w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1"
          >
            {insumos.map((i) => (
              <option key={i.id} value={i.nombre}>{i.nombre}</option>
            ))}
          </select>
        </label>
        <label className="text-xs text-slate-600">
          Cantidad comprada {insumoElegido ? `(${insumoElegido.unidad})` : ""}
          <input
            type="number"
            value={form.cantidad}
            onChange={(e) => setForm({ ...form, cantidad: e.target.value })}
            placeholder="Ej: 5000"
            className="block w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1"
          />
        </label>
        <label className="text-xs text-slate-600">
          Total pagado ($)
          <input
            type="number"
            value={form.costo_total}
            onChange={(e) => setForm({ ...form, costo_total: e.target.value })}
            placeholder="Ej: 12800"
            className="block w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1"
          />
        </label>
        <label className="text-xs text-slate-600 col-span-2">
          Proveedor
          <input
            value={form.proveedor_nombre}
            onChange={(e) => setForm({ ...form, proveedor_nombre: e.target.value })}
            placeholder={insumoElegido?.proveedor_nombre ? `Si lo dejas vacío: ${insumoElegido.proveedor_nombre}` : "¿A quién se lo compraste?"}
            className="block w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1"
          />
        </label>
        {error && <p className="text-red-600 text-xs col-span-2">{error}</p>}
        {aviso && <p className="text-green-700 text-xs col-span-2 bg-green-50 rounded-lg px-3 py-2">{aviso}</p>}
        <button type="submit" className="bg-orange text-white text-sm font-semibold rounded-lg py-2.5 col-span-2">
          Guardar compra
        </button>
      </form>

      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6 flex flex-wrap gap-3 items-end">
        <label className="text-xs text-slate-600">
          Desde
          <input type="date" value={filtros.desde} onChange={(e) => setFiltros({ ...filtros, desde: e.target.value })}
            className="block border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1" />
        </label>
        <label className="text-xs text-slate-600">
          Hasta
          <input type="date" value={filtros.hasta} onChange={(e) => setFiltros({ ...filtros, hasta: e.target.value })}
            className="block border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1" />
        </label>
        <button onClick={() => cargar()} className="bg-navy text-white text-sm font-semibold px-4 py-2 rounded-lg">Filtrar</button>
        <button
          onClick={() => { const vacio = { desde: "", hasta: "" }; setFiltros(vacio); cargar(vacio); }}
          className="text-sm text-slate-500 underline py-2"
        >
          Limpiar
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6">
        <h3 className="text-sm font-semibold text-navy mb-3">Resumen por proveedor</h3>
        {porProveedor.length === 0 ? (
          <p className="text-slate-500 text-sm">Todavía no hay compras registradas en este rango.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
                <th className="py-2">Proveedor</th>
                <th>Compras</th>
                <th>Total pagado</th>
                <th>Insumos que le compras</th>
                <th>Última compra</th>
              </tr>
            </thead>
            <tbody>
              {porProveedor.map((p) => (
                <tr key={p.proveedor} className="border-b border-slate-50">
                  <td className="py-2 font-semibold">{p.proveedor}</td>
                  <td>{p.numero_compras}</td>
                  <td>{fmt(p.total_gastado)}</td>
                  <td>{p.insumos.join(", ")}</td>
                  <td>{p.ultima_compra ? new Date(p.ultima_compra).toLocaleDateString("es-CO") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-navy mb-3">Detalle de compras</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
              <th className="py-2">Fecha</th>
              <th>Proveedor</th>
              <th>Insumo</th>
              <th>Cantidad</th>
              <th>Pagado</th>
            </tr>
          </thead>
          <tbody>
            {compras.map((c) => (
              <tr key={c.id} className="border-b border-slate-50">
                <td className="py-2">{new Date(c.fecha).toLocaleDateString("es-CO")}</td>
                <td>{c.proveedor}</td>
                <td>{c.insumo}</td>
                <td>{c.cantidad} {c.unidad}</td>
                <td>{fmt(c.costo_total)}</td>
              </tr>
            ))}
            {compras.length === 0 && (
              <tr>
                <td colSpan={5} className="text-slate-400 text-sm py-3">Sin compras en este rango.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
