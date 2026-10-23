import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

export default function IA() {
  const { session } = useAuth();
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [sugeridas, setSugeridas] = useState([]);

  useEffect(() => {
    api
      .getRecomendaciones(session.token)
      .then(setRecomendaciones)
      .catch((err) => setError(err.message))
      .finally(() => setCargando(false));
    api
      .getRecetasSugeridas(session.token)
      .then(setSugeridas)
      .catch((err) => setError(err.message));
  }, [session.token]);

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Recomendaciones con IA</h2>
      <p className="text-slate-500 text-sm mb-6">
        Sugerencias generadas a partir de tu consumo e historial de ventas
      </p>

      {error && <p className="text-red-600 text-sm">{error}</p>}
      {cargando && <p className="text-slate-500 text-sm">Analizando consumo histórico...</p>}

      {!cargando && recomendaciones.length === 0 && !error && (
        <p className="text-slate-500 text-sm">
          No hay insumos por debajo de su nivel mínimo en este momento — no se requieren
          recomendaciones de reabastecimiento.
        </p>
      )}

      <div className="space-y-3 max-w-2xl">
        {recomendaciones.map((rec) => (
          <div key={rec.insumo} className="border-l-4 border-orange bg-orange/5 rounded-lg p-4">
            <div className="flex justify-between items-center mb-1">
              <span className="text-orange text-xs font-bold uppercase tracking-wide">
                Reabastecimiento
              </span>
              <span className="text-[10px] text-slate-400 uppercase">
                {rec.fuente === "ia" ? "Generado por IA" : "Regla local (IA no disponible)"}
              </span>
            </div>
            <p className="text-sm text-slate-700">{rec.mensaje}</p>
          </div>
        ))}
      </div>

      <h3 className="text-lg font-bold text-navy mt-10 mb-1">Recetas sugeridas para producir</h3>
      <p className="text-slate-500 text-sm mb-4">
        Solo aparecen recetas que tu inventario actual permite producir, priorizadas por ventas de los últimos 30 días.
      </p>
      {sugeridas.length === 0 && (
        <p className="text-slate-500 text-sm">Con el inventario actual no se puede producir ninguna receta.</p>
      )}
      <div className="space-y-3 max-w-2xl">
        {sugeridas.map((s) => (
          <div key={s.receta} className="border-l-4 border-green-600 bg-green-50 rounded-lg p-4">
            <div className="flex justify-between items-center mb-1">
              <span className="text-green-700 text-sm font-bold">{s.receta}</span>
              <span className="text-[10px] text-slate-400 uppercase">Regla sobre inventario y ventas</span>
            </div>
            <p className="text-sm text-slate-700">{s.motivo}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
