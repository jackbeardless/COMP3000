import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../lib/useAuth";
import { ShieldCheck, FolderOpen, LogOut } from "lucide-react";

export function Layout({ children }) {
  const { user, signOut } = useAuth();
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/cases" className="flex items-center gap-2 font-semibold text-gray-900">
            <ShieldCheck size={20} className="text-brand-600" />
            Vantage
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/cases"
              className={`flex items-center gap-1.5 text-sm transition-colors ${
                pathname.startsWith("/cases") ? "text-brand-600 font-medium" : "text-gray-500 hover:text-gray-900"
              }`}>
              <FolderOpen size={15} /> Cases
            </Link>
            <button onClick={signOut}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors">
              <LogOut size={15} /> Sign out
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto">{children}</main>
    </div>
  );
}
