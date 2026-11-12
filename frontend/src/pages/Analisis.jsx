import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const fmt = (n) => `$${Math.round(n).toLocaleString("es-CO")}`;

// Fechas en formato YYYY-MM-DD con la hora local (toISOString usaría UTC).
function iso(d) {
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mes}-${dia}`;
}

function rangosPreset(preset) {
  const hoy = new Date();
  if (preset === "semana") {
    const aDesde = new Date(hoy); aDesde.setDate(hoy.getDate() - 6);
    const bHasta = new Date(aDesde); bHasta.setDate(aDesde.getDate() - 1);
    const bDesde = new Date(bHasta); bDesde.setDate(bHasta.getDate() - 6);
    return { a_desde: iso(aDesde), a_hasta: iso(hoy), b_desde: iso(bDesde), b_hasta: iso(bHasta) };
  }
  // "mes": lo que va del mes contra los mismos días del mes anterior (el 1
  // al 5 contra el 1 al 5), para no comparar 5 días contra un mes completo.
  const aDesde = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  const bDesde = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
  const finMesAnterior = new Date(hoy.getFullYear(), hoy.getMonth(), 0).getDate();
  const bHasta = new Date(hoy.getFullYear(), hoy.getMonth() - 1, Math.min(hoy.getDate(), finMesAnterior));
  return { a_desde: iso(aDesde), a_hasta: iso(hoy), b_desde: iso(bDesde), b_hasta: iso(bHasta) };
}

function Variacion({ valor }) {
  if (valor === null || valor === undefined) return <span className="text-slate-400 text-xs">sin datos para comparar</span>;
  const sube = valor >= 0;
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${sube ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
      {sube ? "▲" : "▼"} {Math.abs(valor)}%
    </span>
  );
}

// HU-18 Comparar periodos de venta
function CompararPeriodos({ token }) {
  const [preset, setPreset] = useState("mes");
  const [rangos, setRangos] = useState(rangosPreset("mes"));
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");

  function comparar(r = rangos) {
    setError("");
    api.compararPeriodos(token, r).then(setDatos).catch((e) => setError(e.message));
  }

  useEffect(() => {
    api.compararPeriodos(token, rangosPreset("mes")).then(setDatos).catch((e) => setError(e.message));
  }, [token]);

  function elegirPreset(p) {
    setPreset(p);
    if (p !== "personalizado") {
      const r = rangosPreset(p);
      setRangos(r);
      comparar(r);
    }
  }

  const campo = (nombre, etiqueta) => (
    <label className="text-xs text-slate-600">
      {etiqueta}
      <input
        type="date"
        value={rangos[nombre]}
        onChange={(e) => { setPreset("personalizado"); setRangos({ ...rangos, [nombre]: e.target.value }); }}
        className="block border border-slate-200 rounded-lg px-3 py-2 text-sm mt-1"
      />
    </label>
  );

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6">
      <h3 className="text-sm font-semibold text-navy mb-3">Comparar periodos de venta</h3>
      <div className="flex flex-wrap gap-2 mb-4">
        {[
          ["mes", "Este mes vs. mismos días del mes anterior"],
          ["semana", "Últimos 7 días vs. 7 anteriores"],
          ["personalizado", "Elegir fechas"],
        ].map(([id, texto]) => (
          <button
            key={id}
            onClick={() => elegirPreset(id)}
            className={`text-sm px-3 py-1.5 rounded-lg border ${preset === id ? "bg-navy text-white border-navy" : "border-slate-200 text-slate-600"}`}
          >
            {texto}
          </button>
        ))}
      </div>

      {preset === "personalizado" && (
        <div className="flex flex-wrap gap-3 items-end mb-4 bg-cream rounded-lg p-3">
          {campo("a_desde", "Periodo A desde")}
          {campo("a_hasta", "Periodo A hasta")}
          {campo("b_desde", "Periodo B desde")}
          {campo("b_hasta", "Periodo B hasta")}
          <button onClick={() => comparar()} className="bg-orange text-white text-sm font-semibold px-4 py-2 rounded-lg">Comparar</button>
        </div>
      )}

      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {datos && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
            <div className="bg-cream rounded-lg p-4">
              <div className="text-xs text-slate-500">Ingresos</div>
              <div className="text-lg font-bold text-navy">{fmt(datos.periodo_a.ingresos)}</div>
              <div className="text-xs text-slate-500 mb-1">antes: {fmt(datos.periodo_b.ingresos)}</div>
              <Variacion valor={datos.variacion_ingresos_pct} />
            </div>
            <div className="bg-cream rounded-lg p-4">
              <div className="text-xs text-slate-500">Unidades vendidas</div>
              <div className="text-lg font-bold text-navy">{datos.periodo_a.unidades}</div>
              <div className="text-xs text-slate-500 mb-1">antes: {datos.periodo_b.unidades}</div>
              <Variacion valor={datos.variacion_unidades_pct} />
            </div>
            <div className="bg-cream rounded-lg p-4">
              <div className="text-xs text-slate-500">Ganancia</div>
              <div className="text-lg font-bold text-navy">{fmt(datos.periodo_a.ganancia)}</div>
              <div className="text-xs text-slate-500">antes: {fmt(datos.periodo_b.ganancia)}</div>
            </div>
          </div>
          <p className="text-xs text-slate-500 mb-2">
            Periodo A: {datos.periodo_a.desde} a {datos.periodo_a.hasta} · Periodo B: {datos.periodo_b.desde} a {datos.periodo_b.hasta}
          </p>
          {datos.productos.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
                  <th className="py-2">Producto</th>
                  <th>Unidades A</th>
                  <th>Unidades B</th>
                  <th>Cambio</th>
                </tr>
              </thead>
              <tbody>
                {datos.productos.map((p) => (
                  <tr key={p.producto} className="border-b border-slate-50">
                    <td className="py-2">{p.producto}</td>
                    <td>{p.unidades_a}</td>
                    <td>{p.unidades_b}</td>
                    <td><Variacion valor={p.variacion_pct} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}

// HU-15 Ver rentabilidad por producto + HU-17 Ranking de productos + HU-18 Comparar periodos.
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
      <h2 className="text-2xl font-bold text-navy mb-1">Análisis de ventas</h2>
      <p className="text-slate-500 text-sm mb-6">Compara periodos y mira qué productos te dejan más y cuáles se venden más</p>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <CompararPeriodos token={session.token} />

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
