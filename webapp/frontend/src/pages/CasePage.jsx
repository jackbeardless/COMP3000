import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCase, getScans, createScan } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { formatDistanceToNow } from "../lib/time";
import { Play, ChevronLeft, Settings, CheckCircle, Clock, XCircle, Loader } from "lucide-react";

const STATUS_ICON = {
  complete: <CheckCircle size={15} className="text-green-500" />,
  running:  <Loader size={15} className="text-blue-500 animate-spin" />,
  failed:   <XCircle size={15} className="text-red-500" />,
  queued:   <Clock size={15} className="text-gray-400" />,
};

export function CasePage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState({
    run_spiderfoot: true,
    dry_run: false,
    skip_llm: false,
    threshold: 0.75,
    batch_size: 20,
    model: "gemini-2.5-flash",
    skip_noise: true,
  });

  const { data: caseData, isLoading: loadingCase } = useQuery({
    queryKey: ["case", caseId], queryFn: () => getCase(caseId),
  });
  const { data: scans = [], isLoading: loadingScans } = useQuery({
    queryKey: ["scans", caseId], queryFn: () => getScans(caseId),
    refetchInterval: (query) => query.state.data?.some(s => s.status === "running" || s.status === "queued") ? 3000 : false,
  });

  const start = useMutation({
    mutationFn: () => createScan(caseId, { config }),
    onSuccess: (scan) => {
      qc.invalidateQueries({ queryKey: ["scans", caseId] });
      navigate(`/scans/${scan.id}`);
    },
  });

  if (loadingCase) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  if (!caseData) return <p className="text-center py-20 text-gray-500">Case not found.</p>;

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <Link to="/cases" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ChevronLeft size={15} /> All cases
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">{caseData.name}</h1>
            <Badge variant={caseData.status} />
          </div>
          <p className="text-gray-500 text-sm mt-1">
            Target: <span className="font-mono text-gray-700">{caseData.target}</span>
          </p>
          {caseData.description && (
            <p className="text-gray-400 text-sm mt-1">{caseData.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => setShowConfig(!showConfig)}>
            <Settings size={14} /> Config
          </Button>
          <Button size="sm" onClick={() => start.mutate()} disabled={start.isPending}>
            {start.isPending ? <Spinner size="sm" /> : <><Play size={14} /> Run Scan</>}
          </Button>
        </div>
      </div>

      {/* Scan config panel */}
      {showConfig && (
        <Card className="mb-5 border-brand-200">
          <CardHeader><p className="font-semibold text-gray-900 text-sm">Scan Configuration</p></CardHeader>
          <CardBody>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={config.run_spiderfoot}
                  onChange={e => setConfig(p => ({ ...p, run_spiderfoot: e.target.checked }))} />
                Run SpiderFoot scan
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={config.skip_llm}
                  onChange={e => setConfig(p => ({ ...p, skip_llm: e.target.checked }))} />
                Skip LLM step
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={config.dry_run}
                  onChange={e => setConfig(p => ({ ...p, dry_run: e.target.checked }))} />
                Dry run (heuristics only)
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={config.skip_noise}
                  onChange={e => setConfig(p => ({ ...p, skip_noise: e.target.checked }))} />
                Auto-filter obvious noise
              </label>
              <div>
                <p className="text-gray-500 mb-1">Confidence threshold</p>
                <input type="number" min="0" max="1" step="0.05" value={config.threshold}
                  onChange={e => setConfig(p => ({ ...p, threshold: parseFloat(e.target.value) }))}
                  className="w-full px-2 py-1 border rounded text-sm" />
              </div>
              <div>
                <p className="text-gray-500 mb-1">LLM model</p>
                <select value={config.model} onChange={e => setConfig(p => ({ ...p, model: e.target.value }))}
                  className="w-full px-2 py-1 border rounded text-sm">
                  <option>gemini-2.5-flash</option>
                  <option>gemini-2.5-pro</option>
                </select>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Scans list */}
      <h2 className="font-semibold text-gray-900 mb-3">Scan History</h2>
      {loadingScans ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : scans.length === 0 ? (
        <Card>
          <CardBody>
            <p className="text-center text-gray-400 text-sm py-6">No scans yet. Hit "Run Scan" to start.</p>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-2">
          {scans.map(s => (
            <Card key={s.scan_id} className="hover:border-brand-300 transition-colors cursor-pointer"
              onClick={() => navigate(`/scans/${s.scan_id}`)}>
              <CardBody>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {STATUS_ICON[s.status] ?? STATUS_ICON.queued}
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant={s.status} label={s.status} />
                        <span className="text-xs text-gray-400">{formatDistanceToNow(s.created_at)}</span>
                      </div>
                      {s.status === "complete" && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          {s.likely_count ?? 0} likely · {s.maybe_count ?? 0} maybe · {s.low_count ?? 0} low
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 font-mono">{s.scan_id?.slice(0, 8)}</span>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
