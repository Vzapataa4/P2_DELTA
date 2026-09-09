import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";

export default function IA() {
  const { session } = useAuth();
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api
      .getRecomendaciones(session.token)
      .then(setRecomendaciones)
      .catch((err) => setError(err.message))
      .finally(() => setCargando(false));
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
    </div>
  );
}
