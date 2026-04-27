import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCase, getScans, createScan, getCaseProfile, updateCase } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { ConfidenceBar } from "../components/charts/ConfidenceBar";
import { formatDistanceToNow } from "../lib/time";
import { Play, ChevronLeft, Settings, CheckCircle, Clock, XCircle, Loader, User, MapPin, Tag, FileText, ExternalLink, Pencil, Check, X } from "lucide-react";

const PLATFORM_COLOURS = {
  github: "bg-gray-900 text-white",
  reddit: "bg-orange-500 text-white",
  twitter: "bg-sky-500 text-white",
  instagram: "bg-pink-500 text-white",
  twitch: "bg-purple-600 text-white",
  youtube: "bg-red-600 text-white",
  linkedin: "bg-blue-700 text-white",
  steam: "bg-slate-700 text-white",
};

function SubjectProfile({ caseId, profile, isLoading }) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});

  const ki = profile?.known_info ?? {};
  const accounts = profile?.confirmed_accounts ?? [];

  function startEdit() {
    setForm({
      known_name: ki.known_name ?? "",
      known_aliases: ki.known_aliases ?? "",
      known_location: ki.known_location ?? "",
      known_notes: ki.known_notes ?? "",
    });
    setEditing(true);
  }

  const save = useMutation({
    mutationFn: () => updateCase(caseId, { known_info: form }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", caseId] });
      qc.invalidateQueries({ queryKey: ["profile", caseId] });
      setEditing(false);
    },
  });

  return (
    <div>
      <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <User size={16} /> Subject Profile
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* Known Information */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-900">Known Information</span>
              {!editing ? (
                <button onClick={startEdit} className="text-gray-400 hover:text-brand-600 p-1 rounded">
                  <Pencil size={13} />
                </button>
              ) : (
                <div className="flex gap-1">
                  <button onClick={() => save.mutate()} className="text-green-600 hover:text-green-700 p-1 rounded" title="Save">
                    {save.isPending ? <Spinner size="sm" /> : <Check size={14} />}
                  </button>
                  <button onClick={() => setEditing(false)} className="text-gray-400 hover:text-gray-600 p-1 rounded" title="Cancel">
                    <X size={14} />
                  </button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardBody>
            {editing ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <User size={13} className="text-gray-400 shrink-0" />
                  <input value={form.known_name} onChange={e => setForm(p => ({...p, known_name: e.target.value}))}
                    placeholder="Full name"
                    className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div className="flex items-center gap-2">
                  <Tag size={13} className="text-gray-400 shrink-0" />
                  <input value={form.known_aliases} onChange={e => setForm(p => ({...p, known_aliases: e.target.value}))}
                    placeholder="Known aliases (comma-separated)"
                    className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div className="flex items-center gap-2">
                  <MapPin size={13} className="text-gray-400 shrink-0" />
                  <input value={form.known_location} onChange={e => setForm(p => ({...p, known_location: e.target.value}))}
                    placeholder="Location"
                    className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div className="flex items-start gap-2">
                  <FileText size={13} className="text-gray-400 shrink-0 mt-1.5" />
                  <textarea value={form.known_notes} onChange={e => setForm(p => ({...p, known_notes: e.target.value}))}
                    placeholder="Additional notes (employer, bio keywords…)"
                    rows={2}
                    className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
              </div>
            ) : isLoading ? (
              <div className="flex justify-center py-4"><Spinner /></div>
            ) : (
              <div className="space-y-2 text-sm">
                {ki.known_name ? (
                  <div className="flex items-center gap-2">
                    <User size={13} className="text-gray-400 shrink-0" />
                    <span className="font-medium text-gray-900">{ki.known_name}</span>
                  </div>
                ) : null}
                {ki.known_aliases ? (
                  <div className="flex items-start gap-2">
                    <Tag size={13} className="text-gray-400 shrink-0 mt-0.5" />
                    <div className="flex flex-wrap gap-1">
                      {ki.known_aliases.split(",").map(a => (
                        <span key={a} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{a.trim()}</span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {ki.known_location ? (
                  <div className="flex items-center gap-2">
                    <MapPin size={13} className="text-gray-400 shrink-0" />
                    <span className="text-gray-700">{ki.known_location}</span>
                  </div>
                ) : null}
                {ki.known_notes ? (
                  <div className="flex items-start gap-2">
                    <FileText size={13} className="text-gray-400 shrink-0 mt-0.5" />
                    <span className="text-gray-600 text-xs">{ki.known_notes}</span>
                  </div>
                ) : null}
                {!ki.known_name && !ki.known_aliases && !ki.known_location && !ki.known_notes && (
                  <p className="text-gray-400 text-xs text-center py-2">No known information yet. Click the pencil to add details.</p>
                )}
              </div>
            )}
          </CardBody>
        </Card>

        {/* Confirmed Accounts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-900">Confirmed Accounts</span>
              <span className="text-xs text-gray-400">{accounts.length} confirmed</span>
            </div>
          </CardHeader>
          <CardBody>
            {isLoading ? (
              <div className="flex justify-center py-4"><Spinner /></div>
            ) : accounts.length === 0 ? (
              <p className="text-gray-400 text-xs text-center py-2">
                No confirmed accounts yet. Open a scan and click the <CheckCircle size={11} className="inline" /> on results to confirm them.
              </p>
            ) : (
              <div className="space-y-2">
                {accounts.map(acc => (
                  <div key={acc.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded capitalize ${PLATFORM_COLOURS[acc.platform] ?? "bg-gray-200 text-gray-700"}`}>
                      {acc.platform ?? "unknown"}
                    </span>
                    <div className="flex-1 min-w-0">
                      {acc.handle && (
                        <span className="text-xs font-mono text-gray-800">@{acc.handle}</span>
                      )}
                      <div className="w-24 mt-0.5">
                        <ConfidenceBar value={acc.final_confidence ?? acc.heuristic_score} showLabel={false} />
                      </div>
                    </div>
                    {acc.urls?.[0] && (
                      <a href={acc.urls[0]} target="_blank" rel="noopener noreferrer"
                        className="text-gray-400 hover:text-brand-600 shrink-0">
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>

      </div>
    </div>
  );
}

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
  const [scanTarget, setScanTarget] = useState("");
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
  const { data: profile, isLoading: loadingProfile } = useQuery({
    queryKey: ["profile", caseId], queryFn: () => getCaseProfile(caseId),
    enabled: !!caseData,
  });

  const start = useMutation({
    mutationFn: () => createScan(caseId, {
      config,
      scan_target: scanTarget.trim() || undefined,
    }),
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
          {caseData.target && (
            <p className="text-gray-500 text-sm mt-1">
              Target: <span className="font-mono text-gray-700">{caseData.target}</span>
            </p>
          )}
          {caseData.known_info?.known_name && (
            <p className="text-sm text-gray-500 mt-0.5">Known as: <span className="font-medium text-gray-700">{caseData.known_info.known_name}</span></p>
          )}
          {(caseData.known_info?.known_aliases || caseData.known_info?.known_location || caseData.known_info?.known_notes) && (
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {caseData.known_info.known_aliases && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                  {caseData.known_info.known_aliases}
                </span>
              )}
              {caseData.known_info.known_location && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                  {caseData.known_info.known_location}
                </span>
              )}
              {caseData.known_info.known_notes && (
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                  {caseData.known_info.known_notes}
                </span>
              )}
            </div>
          )}
          {caseData.description && (
            <p className="text-gray-400 text-sm mt-1">{caseData.description}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex gap-2 items-center">
            <input
              value={scanTarget}
              onChange={e => setScanTarget(e.target.value)}
              placeholder="Username to scan *"
              className="w-56 px-2 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setShowConfig(!showConfig)}>
              <Settings size={14} /> Config
            </Button>
            <Button size="sm" onClick={() => start.mutate()} disabled={start.isPending || !scanTarget.trim()}>
              {start.isPending ? <Spinner size="sm" /> : <><Play size={14} /> Run Scan</>}
            </Button>
          </div>
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

      {/* Subject Profile */}
      <SubjectProfile caseId={caseId} profile={profile} isLoading={loadingProfile} />

      {/* Scans list */}
      <h2 className="font-semibold text-gray-900 mb-3 mt-8">Scan History</h2>
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
                        <span className="text-xs text-gray-400 font-mono">{s.target}</span>
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
