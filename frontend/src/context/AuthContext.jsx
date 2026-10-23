import { useState } from "react";
import { api } from "../api/client";
import { AuthContext } from "./sessionContext";

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => {
    const raw = sessionStorage.getItem("amassadera_session");
    return raw ? JSON.parse(raw) : null;
  });

  async function login(correo, contrasena) {
    const data = await api.login(correo, contrasena);
    const nueva = { token: data.access_token, nombre: data.nombre, rol: data.rol };
    sessionStorage.setItem("amassadera_session", JSON.stringify(nueva));
    setSession(nueva);
    return nueva;
  }

  function logout() {
    sessionStorage.removeItem("amassadera_session");
    setSession(null);
  }

  return (
    <AuthContext.Provider value={{ session, login, logout }}>{children}</AuthContext.Provider>
  );
}
