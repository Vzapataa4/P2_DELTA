import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export default function Login() {
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setCargando(true);
    try {
      const sesion = await login(correo, contrasena);
      navigate(sesion.rol === "administrador" ? "/" : "/inventario");
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="h-screen flex items-center justify-center bg-gradient-to-br from-navy to-slate-700">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-2xl p-9 w-[340px]"
      >
        <h1 className="text-navy text-xl font-bold mb-1">La Amassadera Inteligente</h1>
        <p className="text-slate-500 text-sm mb-6">Inicia sesión para gestionar tu panadería</p>

        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Correo</label>
        <input
          type="email"
          value={correo}
          onChange={(e) => setCorreo(e.target.value)}
          placeholder="mauricio@laamassadera.com"
          className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm mb-4"
          required
        />

        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Contraseña</label>
        <input
          type="password"
          value={contrasena}
          onChange={(e) => setContrasena(e.target.value)}
          placeholder="••••••••"
          className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm mb-4"
          required
        />

        {error && <p className="text-red-600 text-xs mb-3">{error}</p>}

        <button
          type="submit"
          disabled={cargando}
          className="w-full bg-orange text-white font-semibold rounded-lg py-2.5 text-sm disabled:opacity-60"
        >
          {cargando ? "Ingresando..." : "Iniciar sesión"}
        </button>
      </form>
    </div>
  );
}
