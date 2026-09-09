import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Panel principal", end: true },
  { to: "/inventario", label: "Inventario" },
  { to: "/ventas", label: "Registrar Venta" },
  { to: "/recetas", label: "Recetas" },
  { to: "/ia", label: "Recomendaciones IA" },
];

export default function Layout({ children }) {
  const { session, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex h-screen">
      <aside className="w-56 bg-navy text-white flex flex-col py-5 flex-shrink-0">
        <div className="px-5 pb-4 border-b border-white/10 mb-2">
          <div className="font-bold text-sm">La Amassadera</div>
          <div className="text-xs text-slate-300 mt-0.5">
            {session?.nombre} · {session?.rol}
          </div>
        </div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `px-5 py-3 text-sm ${
                isActive
                  ? "bg-white/10 border-l-[3px] border-orange font-semibold"
                  : "border-l-[3px] border-transparent text-slate-200 hover:bg-white/5"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
        <button
          onClick={handleLogout}
          className="mt-auto text-left px-5 py-3 text-sm text-slate-300 hover:text-white"
        >
          Cerrar sesión
        </button>
      </aside>
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
