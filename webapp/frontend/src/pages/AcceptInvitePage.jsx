import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../lib/useAuth";
import { acceptInvite } from "../lib/api";
import { Card, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { ShieldCheck, CheckCircle } from "lucide-react";

export function AcceptInvitePage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { user } = useAuth();

  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [error, setError] = useState("");

  async function handleAccept() {
    setStatus("loading");
    try {
      await acceptInvite({ token });
      qc.invalidateQueries({ queryKey: ["org-me"] });
      setStatus("success");
      setTimeout(() => navigate("/cases"), 2000);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to accept invite. The link may have expired.");
      setStatus("error");
    }
  }

  // Auto-accept if user is already logged in and there's a token
  useEffect(() => {
    if (user && token && status === "idle") {
      handleAccept();
    }
  }, [user, token]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <ShieldCheck size={36} className="mx-auto text-brand-600 mb-2" />
          <h1 className="text-xl font-bold text-gray-900">Vantage OSINT</h1>
          <p className="text-gray-500 text-sm">Organisation Invite</p>
        </div>

        <Card>
          <CardBody>
            {!token ? (
              <p className="text-sm text-red-600 text-center">
                Invalid invite link — no token found.
              </p>
            ) : !user ? (
              <div className="text-center space-y-3">
                <p className="text-sm text-gray-600">
                  Please sign in to your Vantage account first, then open this invite link again.
                </p>
                <Button onClick={() => navigate("/")}>Go to sign in</Button>
              </div>
            ) : status === "loading" ? (
              <div className="flex justify-center py-4"><Spinner /></div>
            ) : status === "success" ? (
              <div className="text-center space-y-2">
                <CheckCircle size={32} className="mx-auto text-green-500" />
                <p className="text-sm font-medium text-gray-900">You've joined the organisation!</p>
                <p className="text-xs text-gray-500">Redirecting to Cases…</p>
              </div>
            ) : status === "error" ? (
              <div className="space-y-3 text-center">
                <p className="text-sm text-red-600">{error}</p>
                <Button variant="secondary" onClick={() => navigate("/org")}>Go to Organisation page</Button>
              </div>
            ) : null}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
