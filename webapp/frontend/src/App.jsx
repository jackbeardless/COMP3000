import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { useAuth } from "./lib/useAuth";
import { getMyOrg } from "./lib/api";
import { AuthPage } from "./pages/AuthPage";
import { CasesPage } from "./pages/CasesPage";
import { CasePage } from "./pages/CasePage";
import { ScanPage } from "./pages/ScanPage";
import { OrgPage } from "./pages/OrgPage";
import { AcceptInvitePage } from "./pages/AcceptInvitePage";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui/Spinner";

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10_000 } },
});

function OrgGate({ children }) {
  const { pathname } = useLocation();
  const { data: org, isLoading } = useQuery({ queryKey: ["org-me"], queryFn: getMyOrg });

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;

  // /org and /invite don't need an org
  if (!org && !pathname.startsWith("/org") && !pathname.startsWith("/invite")) {
    return <Navigate to="/org" replace />;
  }

  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  );

  if (!user) return (
    <Routes>
      <Route path="/invite" element={<AcceptInvitePage />} />
      <Route path="*" element={<AuthPage />} />
    </Routes>
  );

  return (
    <Layout>
      <OrgGate>
        <Routes>
          <Route path="/" element={<Navigate to="/cases" replace />} />
          <Route path="/cases" element={<CasesPage />} />
          <Route path="/cases/:caseId" element={<CasePage />} />
          <Route path="/scans/:scanId" element={<ScanPage />} />
          <Route path="/org" element={<OrgPage />} />
          <Route path="/invite" element={<AcceptInvitePage />} />
        </Routes>
      </OrgGate>
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
