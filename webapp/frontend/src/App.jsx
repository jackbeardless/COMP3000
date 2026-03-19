import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuth } from "./lib/useAuth";
import { AuthPage } from "./pages/AuthPage";
import { CasesPage } from "./pages/CasesPage";
import { CasePage } from "./pages/CasePage";
import { ScanPage } from "./pages/ScanPage";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui/Spinner";

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10_000 } },
});

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  );

  if (!user) return <AuthPage />;

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/cases" replace />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/cases/:caseId" element={<CasePage />} />
        <Route path="/scans/:scanId" element={<ScanPage />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
