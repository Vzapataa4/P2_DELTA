import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const fmt = (n) => `$${Math.round(n).toLocaleString("es-CO")}`;

// HU-11 Ver historial de ventas, con filtros por fecha y distribuidor.
// HU-12 Desde aquí también se eligen las ventas de un pedido para facturarlas.
export default function Historial() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const [ventas, setVentas] = useState([]);
  const [filtros, setFiltros] = useState({ desde: "", hasta: "", distribuidor: "" });
  const [error, setError] = useState("");
  const [facturadas, setFacturadas] = useState([]);
  const [facturas, setFacturas] = useState([]);
  const [seleccion, setSeleccion] = useState([]);

  function cargarFacturas() {
    api.getVentasFacturadas(session.token).then(setFacturadas).catch(() => {});
    api.getFacturas(session.token).then(setFacturas).catch(() => {});
  }

  function buscar(f = filtros) {
    setError("");
    setSeleccion([]);
    api.getVentas(session.token, f).then(setVentas).catch((err) => setError(err.message));
  }
  useEffect(() => {
    api.getVentas(session.token, {}).then(setVentas).catch((err) => setError(err.message));
    cargarFacturas();
  }, [session.token]); // eslint-disable-line react-hooks/exhaustive-deps

  function alternar(id) {
    setSeleccion((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function facturar() {
    setError("");
    try {
      const factura = await api.generarFactura(session.token, seleccion);
      navigate(`/facturas/${factura.id}`);
    } catch (err) {
      setError(err.message);
    }
  }

  function limpiar() {
    const vacio = { desde: "", hasta: "", distribuidor: "" };
    setFiltros(vacio);
    buscar(vacio);
  }

  const total = ventas.reduce((acc, v) => acc + v.total, 0);

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Historial de ventas y facturas</h2>
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
        <div className="flex flex-wrap justify-between items-center gap-3 mb-3">
          <p className="text-xs text-slate-500">
            Para hacer una factura, marca las ventas del pedido (todas del mismo distribuidor).
          </p>
          <button
            onClick={facturar}
            disabled={seleccion.length === 0}
            className="bg-navy text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-40"
          >
            Generar factura {seleccion.length > 0 ? `(${seleccion.length})` : ""}
          </button>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
              <th className="py-2 w-8"></th>
              <th className="py-2">Fecha</th>
              <th>Distribuidor</th>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Total</th>
              <th>Factura</th>
            </tr>
          </thead>
          <tbody>
            {ventas.map((v) => {
              const yaFacturada = facturadas.includes(v.id);
              return (
                <tr key={v.id} className="border-b border-slate-50">
                  <td className="py-2">
                    <input
                      type="checkbox"
                      checked={seleccion.includes(v.id)}
                      onChange={() => alternar(v.id)}
                      disabled={yaFacturada}
                      aria-label={`Seleccionar venta ${v.id}`}
                    />
                  </td>
                  <td className="py-2">{new Date(v.fecha).toLocaleDateString("es-CO")}</td>
                  <td>{v.distribuidor_nombre || "—"}</td>
                  <td>{v.receta_nombre}</td>
                  <td>{v.cantidad}</td>
                  <td>{fmt(v.total)}</td>
                  <td>
                    {yaFacturada ? (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-700">Facturada</span>
                    ) : (
                      <span className="text-xs text-slate-400">Pendiente</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {ventas.length === 0 && !error && (
          <p className="text-slate-500 text-sm mt-3">No hay ventas con esos filtros.</p>
        )}
        {ventas.length > 0 && (
          <p className="text-sm font-semibold text-navy mt-4">Total en pantalla: {fmt(total)}</p>
        )}
      </div>

      {facturas.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 mt-6">
          <h3 className="text-sm font-semibold text-navy mb-3">Facturas generadas</h3>
          <ul className="text-sm space-y-1">
            {facturas.map((f) => (
              <li key={f.id}>
                <Link to={`/facturas/${f.id}`} className="text-orange font-semibold underline">{f.numero}</Link>
                <span className="text-slate-500"> · {f.distribuidor_nombre} · {fmt(f.total)} · {new Date(f.fecha).toLocaleDateString("es-CO")}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
