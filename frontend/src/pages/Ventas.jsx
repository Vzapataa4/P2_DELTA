import { useEffect, useRef, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const LINEA_VACIA = { receta_nombre: "", cantidad: "" };

export default function Ventas() {
  const { session } = useAuth();
  const [recetas, setRecetas] = useState([]);
  const [ventas, setVentas] = useState([]);
  const [distribuidor, setDistribuidor] = useState("");
  const [lineas, setLineas] = useState([{ ...LINEA_VACIA }]);
  const [error, setError] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [importando, setImportando] = useState(false);
  const [avisoImportacion, setAvisoImportacion] = useState("");
  const fileInputRef = useRef(null);

  function cargar() {
    Promise.all([api.getRecetas(session.token), api.getVentas(session.token)])
      .then(([r, v]) => {
        setRecetas(r);
        setLineas((prev) =>
          prev.map((l) => (l.receta_nombre ? l : { ...l, receta_nombre: r[0]?.nombre || "" }))
        );
        setVentas(v);
      })
      .catch((err) => setError(err.message));
  }

  useEffect(cargar, [session.token]); // eslint-disable-line react-hooks/exhaustive-deps

  function actualizarLinea(idx, campo, valor) {
    setLineas((prev) => prev.map((l, i) => (i === idx ? { ...l, [campo]: valor } : l)));
  }

  function agregarLinea() {
    setLineas((prev) => [...prev, { receta_nombre: recetas[0]?.nombre || "", cantidad: "" }]);
  }

  function eliminarLinea(idx) {
    setLineas((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setConfirmacion("");
    const validas = lineas.filter((l) => l.receta_nombre && parseInt(l.cantidad, 10) > 0);
    if (!distribuidor.trim() || validas.length === 0) {
      setError("Agrega el distribuidor y al menos un producto con cantidad.");
      return;
    }
    try {
      if (validas.length === 1) {
        await api.registrarVenta(session.token, {
          distribuidor_nombre: distribuidor,
          receta_nombre: validas[0].receta_nombre,
          cantidad: parseInt(validas[0].cantidad, 10),
        });
      } else {
        await api.registrarVentasLote(session.token, {
          distribuidor_nombre: distribuidor,
          lineas: validas.map((l) => ({
            receta_nombre: l.receta_nombre,
            cantidad: parseInt(l.cantidad, 10),
          })),
        });
      }
      setConfirmacion("Venta registrada. Inventario actualizado automáticamente según cada receta.");
      setLineas([{ receta_nombre: recetas[0]?.nombre || "", cantidad: "" }]);
      setAvisoImportacion("");
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSubirFactura(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setAvisoImportacion("");
    setImportando(true);
    try {
      const resultado = await api.importarFactura(session.token, file);
      setAvisoImportacion(resultado.mensaje);
      if (resultado.distribuidor_nombre) setDistribuidor(resultado.distribuidor_nombre);
      if (resultado.lineas.length > 0) {
        setLineas(resultado.lineas.map((l) => ({ receta_nombre: l.receta_nombre, cantidad: String(l.cantidad) })));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setImportando(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Registrar venta / pedido</h2>
      <p className="text-slate-500 text-sm mb-6">Registra un pedido de un distribuidor, a mano o subiendo la foto de la factura</p>

      <div className="bg-white border border-slate-200 rounded-xl p-5 max-w-md mb-4">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Subir foto de factura (opcional)</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleSubirFactura}
          disabled={importando}
          className="w-full text-sm"
        />
        {importando && <p className="text-slate-500 text-xs mt-2">Leyendo factura...</p>}
        {avisoImportacion && (
          <p className="text-navy text-xs mt-2 bg-cream rounded-lg px-3 py-2">{avisoImportacion}</p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-5 max-w-md mb-6">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Distribuidor</label>
        <input
          value={distribuidor}
          onChange={(e) => setDistribuidor(e.target.value)}
          placeholder="Ej: Mercados L. Pinedo"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-4"
        />

        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Productos</label>
        {lineas.map((linea, idx) => (
          <div key={idx} className="flex gap-2 mb-2">
            <select
              value={linea.receta_nombre}
              onChange={(e) => actualizarLinea(idx, "receta_nombre", e.target.value)}
              className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm"
            >
              {recetas.map((r) => (
                <option key={r.id} value={r.nombre}>{r.nombre}</option>
              ))}
            </select>
            <input
              type="number"
              value={linea.cantidad}
              onChange={(e) => actualizarLinea(idx, "cantidad", e.target.value)}
              placeholder="Cant."
              className="w-24 border border-slate-200 rounded-lg px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={() => eliminarLinea(idx)}
              className="text-slate-400 text-sm px-2"
              aria-label="Quitar producto"
            >
              ✕
            </button>
          </div>
        ))}
        <button type="button" onClick={agregarLinea} className="text-orange text-xs font-semibold mb-4">
          + Agregar producto
        </button>

        {error && <p className="text-red-600 text-xs mb-3">{error}</p>}
        {confirmacion && <p className="text-green-700 text-xs mb-3 bg-green-50 rounded-lg px-3 py-2">{confirmacion}</p>}

        <button type="submit" className="w-full bg-orange text-white font-semibold rounded-lg py-2.5 text-sm">
          Registrar venta
        </button>
      </form>

      <div className="bg-white border border-slate-200 rounded-xl p-5 max-w-2xl">
        <h3 className="text-sm font-semibold text-navy mb-3">Ventas registradas</h3>
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
                <td className="py-2">{new Date(v.fecha).toLocaleString("es-CO")}</td>
                <td>{v.distribuidor_nombre}</td>
                <td>{v.receta_nombre}</td>
                <td>{v.cantidad} uds</td>
                <td>${v.total.toLocaleString("es-CO")}</td>
              </tr>
            ))}
            {ventas.length === 0 && (
              <tr>
                <td colSpan={5} className="text-slate-400 text-sm py-3">Aún no hay ventas registradas.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
