import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

const fmt = (n) => `$${Math.round(n).toLocaleString("es-CO")}`;

// HU-12 Generar factura básica. Esta vista está pensada para imprimirse o
// guardarse como PDF desde el navegador (el menú lateral no sale impreso).
export default function Factura() {
  const { id } = useParams();
  const { session } = useAuth();
  const [factura, setFactura] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getFactura(session.token, id).then(setFactura).catch((err) => setError(err.message));
  }, [session.token, id]);

  if (error) return <p className="text-red-600 text-sm">{error}</p>;
  if (!factura) return <p className="text-slate-500 text-sm">Cargando factura...</p>;

  return (
    <div>
      <div className="no-print flex gap-3 mb-6">
        <Link to="/historial" className="text-sm text-slate-500 underline py-2">← Volver al historial</Link>
        <button onClick={() => window.print()} className="bg-orange text-white text-sm font-semibold px-4 py-2 rounded-lg">
          Imprimir o guardar como PDF
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-8 max-w-2xl factura">
        <div className="flex justify-between items-start border-b border-slate-200 pb-4 mb-4">
          <div>
            <div className="text-xl font-bold text-navy">La Amassadera</div>
            <div className="text-xs text-slate-500">Panadería · Copacabana, Antioquia</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Factura</div>
            <div className="text-lg font-bold text-orange">{factura.numero}</div>
            <div className="text-xs text-slate-500">{new Date(factura.fecha).toLocaleDateString("es-CO")}</div>
          </div>
        </div>

        <div className="text-sm mb-5">
          <span className="text-slate-500">Cliente: </span>
          <span className="font-semibold">{factura.distribuidor_nombre}</span>
        </div>

        <table className="w-full text-sm mb-4">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-200">
              <th className="py-2">Producto</th>
              <th className="text-right">Cantidad</th>
              <th className="text-right">Precio unitario</th>
              <th className="text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {factura.lineas.map((l, idx) => (
              <tr key={idx} className="border-b border-slate-50">
                <td className="py-2">{l.producto}</td>
                <td className="text-right">{l.cantidad}</td>
                <td className="text-right">{fmt(l.precio_unitario)}</td>
                <td className="text-right">{fmt(l.subtotal)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex justify-end">
          <div className="text-right">
            <div className="text-xs text-slate-500">Total a pagar</div>
            <div className="text-2xl font-bold text-navy">{fmt(factura.total)}</div>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 mt-8">
          Comprobante de venta generado por La Amassadera Inteligente. No reemplaza la factura electrónica ante la DIAN.
        </p>
      </div>
    </div>
  );
}
