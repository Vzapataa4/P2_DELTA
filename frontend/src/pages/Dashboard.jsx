import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const PERIODOS = [
  { key: "dia", label: "Diario", campo: "ventas_por_dia", clave: "dia" },
  { key: "semana", label: "Semanal", campo: "ventas_por_semana", clave: "semana" },
  { key: "mes", label: "Mensual", campo: "ventas_por_mes", clave: "mes" },
];

export default function Dashboard() {
  const { session } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [periodo, setPeriodo] = useState("dia");

  useEffect(() => {
    api
      .getDashboard(session.token)
      .then(setData)
      .catch((err) => setError(err.message));
  }, [session.token]);

  if (error) return <p className="text-red-600 text-sm">{error}</p>;
  if (!data) return <p className="text-slate-500 text-sm">Cargando...</p>;

  const periodoActivo = PERIODOS.find((p) => p.key === periodo);
  const serie = data[periodoActivo.campo] || [];

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Panel principal</h2>
      <p className="text-slate-500 text-sm mb-6">Resumen general del negocio</p>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <Card label="Ventas de hoy" value={data.ventas_hoy} />
        <Card label="Insumos en alerta" value={data.insumos_en_alerta} alert={data.insumos_en_alerta > 0} />
        <Card label="Recetas registradas" value={data.recetas_registradas} />
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-semibold text-navy">Ventas por periodo</h3>
            <div className="flex bg-cream rounded-lg p-0.5">
              {PERIODOS.map((p) => (
                <button
                  key={p.key}
                  onClick={() => setPeriodo(p.key)}
                  className={`text-xs font-semibold px-3 py-1 rounded-md transition-colors ${
                    periodo === p.key ? "bg-navy text-white" : "text-slate-500"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
          {serie.length === 0 ? (
            <p className="text-slate-400 text-sm">Aún no hay ventas registradas.</p>
          ) : (
            <ul className="text-sm space-y-1 max-h-64 overflow-y-auto">
              {serie.map((item) => (
                <li key={item[periodoActivo.clave]} className="flex justify-between">
                  <span className="text-slate-500">{item[periodoActivo.clave]}</span>
                  <span className="font-semibold text-navy">
                    ${item.total.toLocaleString("es-CO")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-navy mb-3">Productos más vendidos</h3>
          {data.productos_mas_vendidos.length === 0 ? (
            <p className="text-slate-400 text-sm">Aún no hay ventas registradas.</p>
          ) : (
            <ul className="space-y-2">
              {data.productos_mas_vendidos.map((p) => (
                <li key={p.producto}>
                  <div className="flex justify-between text-xs mb-1">
                    <span>{p.producto}</span>
                    <span className="text-slate-500">{p.pct}%</span>
                  </div>
                  <div className="bg-cream rounded h-2">
                    <div className="bg-navy h-2 rounded" style={{ width: `${p.pct}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-navy mb-1">Análisis por distribuidor</h3>
        <p className="text-slate-400 text-xs mb-3">
          Producto que más se vende y ganancia generada con cada distribuidor
        </p>
        {data.analisis_distribuidores.length === 0 ? (
          <p className="text-slate-400 text-sm">Aún no hay ventas registradas.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
                <th className="py-2">Distribuidor</th>
                <th>Producto que más vende</th>
                <th>Unidades</th>
                <th>Ganancia generada</th>
              </tr>
            </thead>
            <tbody>
              {data.analisis_distribuidores.map((d) => (
                <tr key={d.distribuidor} className="border-b border-slate-50">
                  <td className="py-2">{d.distribuidor}</td>
                  <td>{d.producto_top}</td>
                  <td>{d.unidades_producto_top} uds</td>
                  <td className="font-semibold text-navy">${d.ganancia_total.toLocaleString("es-CO")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Card({ label, value, alert }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <div className="text-xs text-slate-500 mb-1.5">{label}</div>
      <div className={`text-2xl font-bold ${alert ? "text-red-600" : "text-navy"}`}>{value}</div>
    </div>
  );
}
