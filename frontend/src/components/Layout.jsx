import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

// Íconos del menú (pedido en las pruebas de usabilidad: a un usuario nuevo le
// costó encontrar "Insumos" solo con texto). Trazos simples de 24x24.
const ICONOS = {
  panel: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z",
  inventario: "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
  compras: "M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.3 2.3c-.6.6-.2 1.7.7 1.7H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z",
  venta: "M12 4v16m8-8H4",
  historial: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
  recetas: "M12 6.25v13m0-13C10.8 5.5 9.2 5 7.5 5S4.2 5.5 3 6.25v13C4.2 18.5 5.8 18 7.5 18s3.3.5 4.5 1.25m0-13C13.2 5.5 14.8 5 16.5 5c1.7 0 3.3.5 4.5 1.25v13C19.8 18.5 18.2 18 16.5 18c-1.7 0-3.3.5-4.5 1.25",
  analisis: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  ia: "M9.7 17h4.6M12 3v1m6.4 1.6l-.7.7M21 12h-1M4 12H3m3.3-5.7l-.7-.7m2.9 9.9a5 5 0 117 0l-.6.5A3.4 3.4 0 0014 18.5V19a2 2 0 11-4 0v-.5c0-.9-.4-1.8-1-2.4l-.5-.5z",
  usuarios: "M17 20h5v-2a3 3 0 00-5.4-1.9M17 20H7m10 0v-2c0-.7-.1-1.3-.4-1.9M7 20H2v-2a3 3 0 015.4-1.9M7 20v-2c0-.7.1-1.3.4-1.9m0 0a5 5 0 019.3 0M15 7a3 3 0 11-6 0 3 3 0 016 0z",
  ayuda: "M8.2 9a4 4 0 017.6 1c0 2-3 2.5-3 4.5M12 18h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

function Icono({ nombre }) {
  return (
    <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d={ICONOS[nombre]} />
    </svg>
  );
}

// "soloAdmin": el backend también lo valida (RNF de Roles y permisos); aquí
// solo se oculta para que el empleado no vea opciones que no puede usar.
const NAV_ITEMS = [
  { to: "/", label: "Panel principal", icono: "panel", end: true, soloAdmin: true },
  { to: "/inventario", label: "Inventario de insumos", icono: "inventario" },
  { to: "/compras", label: "Compras a proveedores", icono: "compras", soloAdmin: true },
  { to: "/ventas", label: "Registrar venta", icono: "venta", soloAdmin: true },
  { to: "/historial", label: "Historial y facturas", icono: "historial", soloAdmin: true },
  { to: "/recetas", label: "Recetas", icono: "recetas", soloAdmin: true },
  { to: "/analisis", label: "Análisis de ventas", icono: "analisis", soloAdmin: true },
  { to: "/ia", label: "Recomendaciones IA", icono: "ia", soloAdmin: true },
  { to: "/usuarios", label: "Usuarios", icono: "usuarios", soloAdmin: true },
];

// El manual en PDF vive en frontend/public, así se abre desde la app misma.
const MANUAL_URL = "/manual-usuario-la-amassadera.pdf";

export default function Layout({ children }) {
  const { session, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex h-screen app-shell">
      <aside className="w-60 bg-navy text-white flex flex-col py-5 flex-shrink-0 no-print">
        <div className="px-5 pb-4 border-b border-white/10 mb-2">
          <div className="font-bold">La Amassadera</div>
          <div className="text-xs text-slate-300 mt-0.5">
            {session?.nombre} · {session?.rol}
          </div>
        </div>
        {NAV_ITEMS.filter((item) => !item.soloAdmin || session?.rol === "administrador").map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `px-5 py-3 text-sm flex items-center gap-3 ${
                isActive
                  ? "bg-white/10 border-l-[3px] border-orange font-semibold"
                  : "border-l-[3px] border-transparent text-slate-200 hover:bg-white/5"
              }`
            }
          >
            <Icono nombre={item.icono} />
            {item.label}
          </NavLink>
        ))}
        <div className="mt-auto">
          <a
            href={MANUAL_URL}
            target="_blank"
            rel="noreferrer"
            className="px-5 py-3 text-sm flex items-center gap-3 text-slate-200 hover:bg-white/5 border-l-[3px] border-transparent"
          >
            <Icono nombre="ayuda" />
            Manual de usuario
          </a>
          <button
            onClick={handleLogout}
            className="w-full text-left px-5 py-3 text-sm text-slate-300 hover:text-white"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
