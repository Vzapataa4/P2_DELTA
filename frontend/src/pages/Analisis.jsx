import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const fmt = (n) => `$${Math.round(n).toLocaleString("es-CO")}`;

// HU-15 Ver rentabilidad por producto + HU-17 Ranking de productos.
export default function Analisis() {
  const { session } = useAuth();
  const [rentabilidad, setRentabilidad] = useState([]);
  const [ranking, setRanking] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getRentabilidad(session.token).then(setRentabilidad).catch((e) => setError(e.message));
    api.getRanking(session.token, 10).then(setRanking).catch((e) => setError(e.message));
  }, [session.token]);

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Rentabilidad y ranking</h2>
      <p className="text-slate-500 text-sm mb-6">Qué productos te dejan más y cuáles se venden más</p>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6">
        <h3 className="text-sm font-semibold text-navy mb-3">Rentabilidad por producto</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
              <th className="py-2">Producto</th>
              <th>Costo</th>
              <th>Precio</th>
              <th>Ganancia unit.</th>
              <th>Margen</th>
              <th>Vendidas</th>
              <th>Ganancia total</th>
            </tr>
          </thead>
          <tbody>
            {rentabilidad.map((r) => (
              <tr key={r.receta} className="border-b border-slate-50">
                <td className="py-2">{r.receta}</td>
                <td>{fmt(r.costo_unitario)}</td>
                <td>{fmt(r.precio_venta)}</td>
                <td>{fmt(r.ganancia_unitaria)}</td>
                <td>{r.margen_pct}%</td>
                <td>{r.unidades_vendidas}</td>
                <td>{fmt(r.ganancia_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-navy mb-3">Ranking de productos más vendidos</h3>
        {ranking.length === 0 ? (
          <p className="text-slate-500 text-sm">Aún no hay ventas registradas.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
                <th className="py-2">#</th>
                <th>Producto</th>
                <th>Unidades</th>
                <th>Ingresos</th>
              </tr>
            </thead>
            <tbody>
              {ranking.map((r) => (
                <tr key={r.producto} className="border-b border-slate-50">
                  <td className="py-2 font-semibold">{r.posicion}</td>
                  <td>{r.producto}</td>
                  <td>{r.unidades}</td>
                  <td>{fmt(r.ingresos)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
