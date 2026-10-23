import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { api } from "../api/client";

// HU-02 Crear cuenta de empleado. Solo el administrador (el backend lo valida).
export default function Usuarios() {
  const { session } = useAuth();
  const [usuarios, setUsuarios] = useState([]);
  const [form, setForm] = useState({ nombre: "", correo: "", contrasena: "" });
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  function cargar() {
    api.getUsuarios(session.token).then(setUsuarios).catch((err) => setError(err.message));
  }
  useEffect(cargar, [session.token]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setOk("");
    if (!form.nombre.trim() || !form.correo.trim() || form.contrasena.length < 8) {
      setError("Completa nombre y correo, y usa una contraseña de al menos 8 caracteres.");
      return;
    }
    try {
      await api.crearEmpleado(session.token, form);
      setOk(`Cuenta creada para ${form.nombre}.`);
      setForm({ nombre: "", correo: "", contrasena: "" });
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-1">Usuarios</h2>
      <p className="text-slate-500 text-sm mb-6">Crea cuentas para tu personal de producción</p>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-5 mb-6 grid grid-cols-3 gap-3 max-w-3xl">
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={(e) => setForm({ ...form, nombre: e.target.value })}
          className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
        />
        <input
          type="email"
          placeholder="Correo"
          value={form.correo}
          onChange={(e) => setForm({ ...form, correo: e.target.value })}
          className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
        />
        <input
          type="password"
          placeholder="Contraseña (mín. 8)"
          value={form.contrasena}
          onChange={(e) => setForm({ ...form, contrasena: e.target.value })}
          className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
        />
        {error && <p className="text-red-600 text-xs col-span-3">{error}</p>}
        {ok && <p className="text-green-700 text-xs col-span-3">{ok}</p>}
        <button type="submit" className="bg-navy text-white text-sm font-semibold rounded-lg py-2 col-span-3">
          Crear cuenta de empleado
        </button>
      </form>

      <div className="bg-white border border-slate-200 rounded-xl p-5 max-w-3xl">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-100">
              <th className="py-2">Nombre</th>
              <th>Correo</th>
              <th>Rol</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id} className="border-b border-slate-50">
                <td className="py-2">{u.nombre}</td>
                <td>{u.correo}</td>
                <td>{u.rol}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
