import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Inventario from "./pages/Inventario";
import Ventas from "./pages/Ventas";
import Recetas from "./pages/Recetas";
import IA from "./pages/IA";

function RutaPrivada({ children }) {
  const { session } = useAuth();
  if (!session) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<RutaPrivada><Dashboard /></RutaPrivada>} />
      <Route path="/inventario" element={<RutaPrivada><Inventario /></RutaPrivada>} />
      <Route path="/ventas" element={<RutaPrivada><Ventas /></RutaPrivada>} />
      <Route path="/recetas" element={<RutaPrivada><Recetas /></RutaPrivada>} />
      <Route path="/ia" element={<RutaPrivada><IA /></RutaPrivada>} />
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
