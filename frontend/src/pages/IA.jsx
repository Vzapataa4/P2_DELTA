import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

// Recomendaciones descartadas (pedido en las pruebas de usabilidad del
// 21/10/2026: "poder archivar las notificaciones para que no se acumulen").
// Se guardan en este navegador con la fecha del día: si al día siguiente el
// insumo sigue bajo, la recomendación vuelve a salir.
const CLAVE_DESCARTADAS = "amassadera.recomendaciones-descartadas";

function hoy() {
  return new Date().toISOString().slice(0, 10);
}

function leerDescartadas() {
  try {
    const guardado = JSON.parse(localStorage.getItem(CLAVE_DESCARTADAS) || "{}");
    // Solo valen las de hoy
    return Object.fromEntries(Object.entries(guardado).filter(([, fecha]) => fecha === hoy()));
  } catch {
    return {};
  }
}

function guardarDescartadas(valor) {
  try {
    localStorage.setItem(CLAVE_DESCARTADAS, JSON.stringify(valor));
  } catch {
    // modo privado o almacenamiento bloqueado: se descarta solo mientras la página esté abierta
  }
}

export default function IA() {
  const { session } = useAuth();
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [sugeridas, setSugeridas] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [cargandoIdeas, setCargandoIdeas] = useState(true);
  const [descartadas, setDescartadas] = useState(leerDescartadas);
  const [verDescartadas, setVerDescartadas] = useState(false);

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
    api
      .getIdeasMarketing(session.token)
      .then(setIdeas)
      .catch((err) => setError(err.message))
      .finally(() => setCargandoIdeas(false));
  }, [session.token]);

  function descartar(insumo) {
    const nuevo = { ...descartadas, [insumo]: hoy() };
    setDescartadas(nuevo);
    guardarDescartadas(nuevo);
  }

  function restaurar(insumo) {
    const nuevo = { ...descartadas };
    delete nuevo[insumo];
    setDescartadas(nuevo);
    guardarDescartadas(nuevo);
  }

  const visibles = recomendaciones.filter((r) => verDescartadas || !descartadas[r.insumo]);
  const numDescartadas = recomendaciones.filter((r) => descartadas[r.insumo]).length;

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Recomendaciones con IA</h2>
      <p className="text-slate-500 text-sm mb-6">
        Sugerencias generadas a partir de tu consumo e historial de ventas
      </p>

      {error && <p className="text-red-600 text-sm">{error}</p>}
      {cargando && <p className="text-slate-500 text-sm">Analizando consumo histórico...</p>}

      <div className="flex justify-between items-center max-w-2xl mb-3">
        <h3 className="text-lg font-bold text-navy">Qué comprar</h3>
        {numDescartadas > 0 && (
          <button onClick={() => setVerDescartadas((v) => !v)} className="text-xs text-slate-500 underline">
            {verDescartadas ? "Ocultar descartadas" : `Ver descartadas hoy (${numDescartadas})`}
          </button>
        )}
      </div>

      {!cargando && recomendaciones.length === 0 && !error && (
        <p className="text-slate-500 text-sm">
          No hay insumos por debajo de su nivel mínimo en este momento — no se requieren
          recomendaciones de reabastecimiento.
        </p>
      )}
      {!cargando && recomendaciones.length > 0 && visibles.length === 0 && (
        <p className="text-slate-500 text-sm">Ya revisaste todas las recomendaciones de hoy.</p>
      )}

      <div className="space-y-3 max-w-2xl">
        {visibles.map((rec) => {
          const esDescartada = Boolean(descartadas[rec.insumo]);
          return (
            <div
              key={rec.insumo}
              className={`border-l-4 rounded-lg p-4 ${esDescartada ? "border-slate-300 bg-slate-50 opacity-70" : "border-orange bg-orange/5"}`}
            >
              <div className="flex justify-between items-center mb-1 gap-2">
                <span className="text-orange text-xs font-bold uppercase tracking-wide">
                  Reabastecimiento
                </span>
                <span className="text-[11px] text-slate-400 uppercase">
                  {rec.fuente === "ia" ? "Generado por IA" : "Regla local (IA no disponible)"}
                </span>
              </div>
              <p className="text-sm text-slate-700">{rec.mensaje}</p>
              <button
                onClick={() => (esDescartada ? restaurar(rec.insumo) : descartar(rec.insumo))}
                className="text-xs text-slate-500 underline mt-2"
              >
                {esDescartada ? "Volver a mostrar" : "Ya lo revisé, descartar"}
              </button>
            </div>
          );
        })}
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
              <span className="text-[11px] text-slate-400 uppercase">Regla sobre inventario y ventas</span>
            </div>
            <p className="text-sm text-slate-700">{s.motivo}</p>
          </div>
        ))}
      </div>

      {/* HU-22 Sugerir ideas de marketing */}
      <h3 className="text-lg font-bold text-navy mt-10 mb-1">Ideas para vender más</h3>
      <p className="text-slate-500 text-sm mb-4">
        Salen de comparar tus ventas de los últimos 30 días con los 30 anteriores, por producto y por distribuidor.
      </p>
      {cargandoIdeas && <p className="text-slate-500 text-sm">Buscando ideas...</p>}
      {!cargandoIdeas && ideas.length === 0 && (
        <p className="text-slate-500 text-sm">
          Todavía no hay ventas en el último mes para sacar ideas. Registra tus pedidos y vuelve en unos días.
        </p>
      )}
      <div className="space-y-3 max-w-2xl">
        {ideas.map((idea) => (
          <div key={idea.titulo} className="border-l-4 border-navy bg-white border border-slate-200 rounded-lg p-4">
            <div className="flex justify-between items-center mb-1 gap-2">
              <span className="text-navy text-sm font-bold">{idea.titulo}</span>
              <span className="text-[11px] text-slate-400 uppercase">
                {idea.fuente === "ia" ? "Generado por IA" : "Regla sobre tus ventas"}
              </span>
            </div>
            <p className="text-sm text-slate-700">{idea.idea}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
