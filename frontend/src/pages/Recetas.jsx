import { useEffect, useRef, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

export default function Recetas() {
  const { session } = useAuth();
  const [recetas, setRecetas] = useState([]);
  const [insumos, setInsumos] = useState([]);
  const [error, setError] = useState("");
  const [mostrarForm, setMostrarForm] = useState(false);
  const [nombre, setNombre] = useState("");
  const [precioVenta, setPrecioVenta] = useState("");
  const [lineas, setLineas] = useState([{ insumo_nombre: "", cantidad_requerida: "" }]);
  const [formError, setFormError] = useState("");
  const [importando, setImportando] = useState(false);
  const [avisoImportacion, setAvisoImportacion] = useState("");
  const fileInputRef = useRef(null);

  function cargar() {
    Promise.all([api.getRecetas(session.token), api.getInsumos(session.token)])
      .then(([r, i]) => {
        setRecetas(r);
        setInsumos(i);
      })
      .catch((err) => setError(err.message));
  }

  useEffect(cargar, [session.token]);

  function actualizarLinea(idx, campo, valor) {
    setLineas((prev) => prev.map((l, i) => (i === idx ? { ...l, [campo]: valor } : l)));
  }

  const costoEstimado = lineas.reduce((sum, l) => {
    const insumo = insumos.find((i) => i.nombre === l.insumo_nombre);
    const cantidad = parseFloat(l.cantidad_requerida) || 0;
    return sum + (insumo ? insumo.costo_unitario * cantidad : 0);
  }, 0);

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");
    const validas = lineas.filter((l) => l.insumo_nombre && parseFloat(l.cantidad_requerida) > 0);
    if (!nombre.trim() || validas.length === 0) {
      setFormError("Agrega un nombre y al menos un insumo con cantidad.");
      return;
    }
    try {
      await api.crearReceta(session.token, {
        nombre,
        insumos: validas.map((l) => ({
          insumo_nombre: l.insumo_nombre,
          cantidad_requerida: parseFloat(l.cantidad_requerida),
        })),
        precio_venta: precioVenta ? parseFloat(precioVenta) : null,
      });
      setNombre("");
      setPrecioVenta("");
      setLineas([{ insumo_nombre: "", cantidad_requerida: "" }]);
      setAvisoImportacion("");
      setMostrarForm(false);
      cargar();
    } catch (err) {
      setFormError(err.message);
    }
  }

  async function handleSubirExcel(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFormError("");
    setAvisoImportacion("");
    setImportando(true);
    try {
      const resultado = await api.importarExcelReceta(session.token, file);
      setMostrarForm(true);
      setNombre(resultado.receta_nombre);
      setLineas(
        resultado.lineas.length > 0
          ? resultado.lineas.map((l) => ({
              insumo_nombre: l.existe ? l.insumo_nombre : "",
              cantidad_requerida: String(l.cantidad_requerida),
              _nombre_original: l.insumo_nombre,
              _existe: l.existe,
            }))
          : [{ insumo_nombre: "", cantidad_requerida: "" }]
      );
      setAvisoImportacion(resultado.mensaje);
    } catch (err) {
      setFormError(err.message);
    } finally {
      setImportando(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Recetas</h2>
      <p className="text-slate-500 text-sm mb-6">Costeo automático por receta</p>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Importar receta desde Excel</label>
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          onChange={handleSubirExcel}
          disabled={importando}
          className="w-full text-sm"
        />
        {importando && <p className="text-slate-500 text-xs mt-2">Leyendo archivo...</p>}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold text-navy">Recetas registradas</h3>
          <button
            onClick={() => setMostrarForm((v) => !v)}
            className="bg-orange text-white text-sm font-semibold px-4 py-2 rounded-lg"
          >
            + Nueva receta
          </button>
        </div>

        {mostrarForm && (
          <form onSubmit={handleSubmit} className="bg-cream rounded-lg p-4 mb-4">
            {avisoImportacion && (
              <p className="text-navy text-xs mb-3 bg-white rounded-lg px-3 py-2">{avisoImportacion}</p>
            )}
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              Nombre del producto — revisa que sea el correcto antes de guardar
            </label>
            <input
              placeholder="Nombre del producto (ej: Croissant)"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3"
            />

            {lineas.map((linea, idx) => {
              const insumoSeleccionado = insumos.find((i) => i.nombre === linea.insumo_nombre);
              const unidad = insumoSeleccionado?.unidad;
              return (
                <div key={idx} className="mb-2">
                  <div className="flex gap-2 items-center">
                    <select
                      value={linea.insumo_nombre}
                      onChange={(e) => actualizarLinea(idx, "insumo_nombre", e.target.value)}
                      className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm"
                    >
                      <option value="">Selecciona un insumo</option>
                      {insumos.map((i) => (
                        <option key={i.id} value={i.nombre}>{i.nombre} ({i.unidad})</option>
                      ))}
                    </select>
                    <input
                      type="number"
                      placeholder="Cantidad por unidad"
                      value={linea.cantidad_requerida}
                      onChange={(e) => actualizarLinea(idx, "cantidad_requerida", e.target.value)}
                      className="w-28 border border-slate-200 rounded-lg px-3 py-2 text-sm"
                    />
                    <span className="text-xs text-slate-500 w-10">{unidad || "—"}</span>
                  </div>
                  {linea._existe === false && (
                    <p className="text-orange text-xs mt-1">
                      "{linea._nombre_original}" no existe en tu inventario — regístralo primero o elige el insumo correcto arriba.
                    </p>
                  )}
                </div>
              );
            })}

            <button
              type="button"
              onClick={() => setLineas((prev) => [...prev, { insumo_nombre: "", cantidad_requerida: "" }])}
              className="text-orange text-xs font-semibold mb-3"
            >
              + Agregar insumo
            </button>

            <div className="bg-white rounded-lg px-4 py-2 text-sm font-semibold text-navy mb-3">
              Costo estimado por unidad: ${costoEstimado.toLocaleString("es-CO")}
            </div>

            <label className="block text-xs font-semibold text-slate-600 mb-1.5">
              Precio de venta al distribuidor (opcional — si lo dejas vacío, la ganancia sale en $0)
            </label>
            <input
              type="number"
              placeholder={`Ej: ${Math.round((costoEstimado * 1.4) / 10) * 10 || 0}`}
              value={precioVenta}
              onChange={(e) => setPrecioVenta(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3"
            />
            {precioVenta && (
              <div className="bg-white rounded-lg px-4 py-2 text-sm font-semibold mb-3">
                Ganancia estimada por unidad:{" "}
                <span className={parseFloat(precioVenta) - costoEstimado >= 0 ? "text-green-700" : "text-red-600"}>
                  ${(parseFloat(precioVenta) - costoEstimado).toLocaleString("es-CO")}
                </span>
              </div>
            )}

            {formError && <p className="text-red-600 text-xs mb-2">{formError}</p>}
            <button type="submit" className="bg-navy text-white text-sm font-semibold rounded-lg py-2 w-full">
              Guardar receta
            </button>
          </form>
        )}

        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
              <th className="py-2">Producto</th>
              <th>Insumos</th>
              <th>Costo (por unidad)</th>
              <th>Precio de venta</th>
              <th>Ganancia</th>
            </tr>
          </thead>
          <tbody>
            {recetas.map((r) => (
              <tr key={r.id} className="border-b border-slate-50">
                <td className="py-2">{r.nombre}</td>
                <td className="text-slate-500 text-xs">
                  {r.insumos
                    .map((i) => {
                      const unidad = insumos.find((ins) => ins.nombre === i.insumo_nombre)?.unidad || "";
                      return `${i.insumo_nombre} (${i.cantidad_requerida} ${unidad})`;
                    })
                    .join(", ")}
                </td>
                <td className="font-semibold text-navy">${r.costo_total.toLocaleString("es-CO")}</td>
                <td>
                  {r.precio_venta != null ? (
                    `$${r.precio_venta.toLocaleString("es-CO")}`
                  ) : (
                    <span className="text-slate-400 text-xs">Sin definir</span>
                  )}
                </td>
                <td className={`font-semibold ${r.ganancia_unitaria > 0 ? "text-green-700" : "text-slate-400"}`}>
                  ${r.ganancia_unitaria.toLocaleString("es-CO")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
