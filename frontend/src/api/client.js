// Cliente HTTP centralizado: agrega el token JWT y maneja errores de forma
// consistente en toda la app (ver RNF de Manejo de fallos en la Wiki).
const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function qs(params = {}) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "" && v != null));
  const texto = q.toString();
  return texto ? `?${texto}` : "";
}

async function request(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    // El backend no respondió en absoluto (caído, sin red, etc.)
    throw new Error("No se pudo conectar con el servidor. Intenta de nuevo en un momento.");
  }

  if (!res.ok) {
    let detail = "Ocurrió un error inesperado.";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // respuesta sin cuerpo JSON
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

// Variante para subir archivos (foto de factura / Excel de receta): no se
// puede usar JSON.stringify en el body, el navegador arma el multipart solo.
async function requestFile(path, { file, token } = {}) {
  const form = new FormData();
  form.append("file", file);

  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: form,
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor. Intenta de nuevo en un momento.");
  }

  if (!res.ok) {
    let detail = "Ocurrió un error inesperado.";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // respuesta sin cuerpo JSON
    }
    throw new Error(detail);
  }

  return res.json();
}

export const api = {
  login: (correo, contrasena) =>
    request("/api/auth/login", { method: "POST", body: { correo, contrasena } }),
  getInsumos: (token) => request("/api/insumos", { token }),
  crearInsumo: (token, data) => request("/api/insumos", { method: "POST", body: data, token }),
  getRecetas: (token) => request("/api/recetas", { token }),
  crearReceta: (token, data) => request("/api/recetas", { method: "POST", body: data, token }),
  importarExcelReceta: (token, file) => requestFile("/api/recetas/importar-excel", { file, token }),
  getVentas: (token, filtros) => request(`/api/ventas${qs(filtros)}`, { token }),
  getRanking: (token, limite = 10) => request(`/api/ventas/ranking${qs({ limite })}`, { token }),
  getRentabilidad: (token) => request("/api/recetas/rentabilidad", { token }),
  getRecetasSugeridas: (token) => request("/api/ia/recetas-sugeridas", { token }),
  actualizarCantidadInsumo: (token, id, cantidad) =>
    request(`/api/insumos/${id}/cantidad`, { method: "PATCH", body: { cantidad_disponible: cantidad }, token }),
  getUsuarios: (token) => request("/api/auth/usuarios", { token }),
  crearEmpleado: (token, data) => request("/api/auth/empleados", { method: "POST", body: data, token }),
  registrarVenta: (token, data) => request("/api/ventas", { method: "POST", body: data, token }),
  registrarVentasLote: (token, data) => request("/api/ventas/lote", { method: "POST", body: data, token }),
  importarFactura: (token, file) => requestFile("/api/ventas/importar-factura", { file, token }),
  getDashboard: (token) => request("/api/dashboard", { token }),
  getRecomendaciones: (token) => request("/api/ia/recomendaciones", { token }),
};
