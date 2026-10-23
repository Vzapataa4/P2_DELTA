import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./context/useAuth";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Inventario from "./pages/Inventario";
import Ventas from "./pages/Ventas";
import Recetas from "./pages/Recetas";
import IA from "./pages/IA";
import Historial from "./pages/Historial";
import Analisis from "./pages/Analisis";
import Usuarios from "./pages/Usuarios";

function RutaPrivada({ children, soloAdmin = false }) {
  const { session } = useAuth();
  if (!session) return <Navigate to="/login" replace />;
  // El empleado solo puede consultar el inventario (HU-08).
  if (soloAdmin && session.rol !== "administrador") return <Navigate to="/inventario" replace />;
  return <Layout>{children}</Layout>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<RutaPrivada soloAdmin><Dashboard /></RutaPrivada>} />
      <Route path="/inventario" element={<RutaPrivada><Inventario /></RutaPrivada>} />
      <Route path="/ventas" element={<RutaPrivada soloAdmin><Ventas /></RutaPrivada>} />
      <Route path="/recetas" element={<RutaPrivada soloAdmin><Recetas /></RutaPrivada>} />
      <Route path="/ia" element={<RutaPrivada soloAdmin><IA /></RutaPrivada>} />
      <Route path="/historial" element={<RutaPrivada soloAdmin><Historial /></RutaPrivada>} />
      <Route path="/analisis" element={<RutaPrivada soloAdmin><Analisis /></RutaPrivada>} />
      <Route path="/usuarios" element={<RutaPrivada soloAdmin><Usuarios /></RutaPrivada>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
