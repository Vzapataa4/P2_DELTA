import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const fmt = (n) => `$${Math.round(n).toLocaleString("es-CO")}`;

// HU-11 Ver historial de ventas, con filtros por fecha y distribuidor.
export default function Historial() {
  const { session } = useAuth();
  const [ventas, setVentas] = useState([]);
  const [filtros, setFiltros] = useState({ desde: "", hasta: "", distribuidor: "" });
  const [error, setError] = useState("");

  function buscar(f = filtros) {
    setError("");
    api.getVentas(session.token, f).then(setVentas).catch((err) => setError(err.message));
  }
  useEffect(() => {
    api.getVentas(session.token, {}).then(setVentas).catch((err) => setError(err.message));
  }, [session.token]);

  function limpiar() {
    const vacio = { desde: "", hasta: "", distribuidor: "" };
    setFiltros(vacio);
    buscar(vacio);
  }

  const total = ventas.reduce((acc, v) => acc + v.total, 0);

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Historial de ventas</h2>
      <p className="text-slate-500 text-sm mb-6">Consulta ventas pasadas por fecha o distribuidor</p>

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
        <label className="text-xs text-slate-600">
          Distribuidor
          <input value={filtros.distribuidor} onChange={(e) => setFiltros({ ...filtros, distribuidor: e.target.value })}
            placeholder="Nombre exacto" className="block border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1" />
        </label>
        <button onClick={() => buscar()} className="bg-orange text-white text-sm font-semibold px-4 py-2 rounded-lg">Filtrar</button>
        <button onClick={limpiar} className="text-sm text-slate-500 underline py-2">Limpiar</button>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
              <th className="py-2">Fecha</th>
              <th>Distribuidor</th>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {ventas.map((v) => (
              <tr key={v.id} className="border-b border-slate-50">
                <td className="py-2">{new Date(v.fecha).toLocaleDateString("es-CO")}</td>
                <td>{v.distribuidor_nombre || "—"}</td>
                <td>{v.receta_nombre}</td>
                <td>{v.cantidad}</td>
                <td>{fmt(v.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {ventas.length === 0 && !error && (
          <p className="text-slate-500 text-sm mt-3">No hay ventas con esos filtros.</p>
        )}
        {ventas.length > 0 && (
          <p className="text-sm font-semibold text-navy mt-4">Total en pantalla: {fmt(total)}</p>
        )}
      </div>
    </div>
  );
}
