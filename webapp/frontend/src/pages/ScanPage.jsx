import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getScan, getClusters, annotateClusters } from "../lib/api";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { ConfidenceBar } from "../components/charts/ConfidenceBar";
import { VerdictPie } from "../components/charts/VerdictPie";
import { PlatformBar } from "../components/charts/PlatformBar";
import { ConfidenceHistogram } from "../components/charts/ConfidenceHistogram";
import { ChevronLeft, ExternalLink, ChevronDown, ChevronUp, CheckCircle, AlertTriangle, HelpCircle } from "lucide-react";
import { formatDistanceToNow } from "../lib/time";

// ── WebSocket progress feed ────────────────────────────────────────────────
function ProgressFeed({ scanId }) {
  const [msgs, setMsgs] = useState([]);
  const [done, setDone] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/scans/${scanId}/ws`);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      setMsgs(p => [...p, msg]);
      if (msg.done) setDone(true);
    };
    ws.onerror = () => setDone(true);
    return () => ws.close();
  }, [scanId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  if (msgs.length === 0) return (
    <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
      <Spinner size="sm" /> Waiting for pipeline to start…
    </div>
  );

  return (
    <div className="font-mono text-xs bg-gray-950 text-gray-200 rounded-lg p-4 max-h-60 overflow-y-auto">
      {msgs.map((m, i) => (
        <div key={i} className={`mb-1 ${m.status === "failed" ? "text-red-400" : m.status === "complete" ? "text-green-400" : "text-blue-300"}`}>
          [{m.step}] {m.message}
        </div>
      ))}
      {!done && <div className="flex items-center gap-1 text-gray-400"><Spinner size="sm" /> running…</div>}
      <div ref={bottomRef} />
    </div>
  );
}

// ── Cluster row ────────────────────────────────────────────────────────────
function ClusterRow({ cluster }) {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [note, setNote] = useState(cluster.analyst_note ?? "");
  const [savingNote, setSavingNote] = useState(false);

  const annotate = useMutation({
    mutationFn: (body) => annotateClusters(cluster.id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clusters"] }),
  });

  async function saveNote() {
    setSavingNote(true);
    await annotate.mutateAsync({ analyst_note: note });
    setSavingNote(false);
  }

  const VERDICT_ICON = {
    likely: <CheckCircle size={14} className="text-green-500" />,
    maybe:  <HelpCircle size={14} className="text-yellow-500" />,
    low:    <AlertTriangle size={14} className="text-red-400" />,
  };

  return (
    <div className="border border-gray-100 rounded-lg overflow-hidden">
      {/* Header row */}
      <div
        className="flex items-center gap-3 px-4 py-3 bg-white hover:bg-gray-50 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        {VERDICT_ICON[cluster.verdict]}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-gray-900 text-sm">{cluster.platform ?? "unknown"}</span>
            {cluster.handle && (
              <span className="font-mono text-xs text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">
                @{cluster.handle}
              </span>
            )}
            <Badge variant={cluster.verdict} label={cluster.verdict} />
            {cluster.analyst_verdict && (
              <Badge variant={cluster.analyst_verdict} label={cluster.analyst_verdict} />
            )}
          </div>
          <div className="mt-1 w-48">
            <ConfidenceBar value={cluster.final_confidence ?? cluster.heuristic_score} showLabel />
          </div>
        </div>
        <div className="flex items-center gap-2 ml-2 shrink-0">
          {cluster.urls[0] && (
            <a href={cluster.urls[0]} target="_blank" rel="noopener noreferrer"
              className="text-gray-400 hover:text-brand-600"
              onClick={e => e.stopPropagation()}>
              <ExternalLink size={14} />
            </a>
          )}
          {expanded ? <ChevronUp size={15} className="text-gray-400" /> : <ChevronDown size={15} className="text-gray-400" />}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100 space-y-3">
          {/* LLM rationale */}
          {cluster.rationale && (
            <div>
              <p className="text-xs font-medium text-gray-500 mt-3 mb-1">LLM Rationale</p>
              <p className="text-sm text-gray-700">{cluster.rationale}</p>
            </div>
          )}

          {/* URLs */}
          {cluster.urls.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">URLs</p>
              <div className="space-y-1">
                {cluster.urls.map((u, i) => (
                  <a key={i} href={u} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-brand-600 hover:underline break-all">
                    <ExternalLink size={10} />{u}
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Signals */}
          {cluster.signals?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">SpiderFoot Modules</p>
              <div className="flex flex-wrap gap-1">
                {cluster.signals.map(s => (
                  <span key={s} className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Scores */}
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
            <div>Heuristic score: <span className="font-mono text-gray-700">{(cluster.heuristic_score * 100).toFixed(0)}%</span></div>
            <div>Final confidence: <span className="font-mono text-gray-700">{((cluster.final_confidence ?? cluster.heuristic_score) * 100).toFixed(0)}%</span></div>
          </div>

          {/* Analyst annotation */}
          <div className="border-t border-gray-200 pt-3">
            <p className="text-xs font-medium text-gray-500 mb-2">Analyst Assessment</p>
            <div className="flex gap-1 mb-2">
              {["confirmed", "disputed", "needs_review"].map(v => (
                <button key={v}
                  className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                    cluster.analyst_verdict === v
                      ? "bg-brand-600 text-white border-brand-600"
                      : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"
                  }`}
                  onClick={() => annotate.mutate({ analyst_verdict: cluster.analyst_verdict === v ? null : v })}>
                  {v.replace("_", " ")}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <textarea value={note} onChange={e => setNote(e.target.value)} rows={2}
                placeholder="Add analyst note…"
                className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs resize-none focus:outline-none focus:ring-1 focus:ring-brand-500" />
              <Button size="sm" variant="secondary" onClick={saveNote} disabled={savingNote}>
                {savingNote ? <Spinner size="sm" /> : "Save"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main scan page ─────────────────────────────────────────────────────────
export function ScanPage() {
  const { scanId } = useParams();
  const qc = useQueryClient();
  const [verdictFilter, setVerdictFilter] = useState(null);
  const [platformFilter, setPlatformFilter] = useState("");
  const [minConf, setMinConf] = useState(0);

  const { data: scan, isLoading: loadingScan } = useQuery({
    queryKey: ["scan", scanId], queryFn: () => getScan(scanId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return (status === "running" || status === "queued") ? 3000 : false;
    },
  });

  // Invalidate clusters when scan transitions to complete
  useEffect(() => {
    if (scan?.status === "complete") {
      qc.invalidateQueries({ queryKey: ["clusters", scanId] });
    }
  }, [scan?.status, scanId, qc]);

  const { data: clusters = [], isLoading: loadingClusters } = useQuery({
    queryKey: ["clusters", scanId, verdictFilter, platformFilter, minConf],
    queryFn: () => getClusters(scanId, {
      ...(verdictFilter && { verdict: verdictFilter }),
      ...(platformFilter && { platform: platformFilter }),
      min_confidence: minConf,
    }),
    enabled: scan?.status === "complete",
  });

  const isRunning = scan?.status === "running" || scan?.status === "queued";

  if (loadingScan) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  if (!scan) return <p className="text-center py-20 text-gray-500">Scan not found.</p>;

  const platforms = [...new Set(clusters.map(c => c.platform).filter(Boolean))].sort();

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <Link to={`/cases/${scan.case_id}`}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ChevronLeft size={15} /> Back to case
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">Scan Results</h1>
            <Badge variant={scan.status} label={scan.status} />
          </div>
          <p className="text-sm text-gray-500 mt-0.5">
            Target: <span className="font-mono text-gray-700">{scan.target}</span>
            {scan.completed_at && <span className="ml-3">{formatDistanceToNow(scan.completed_at)}</span>}
          </p>
        </div>
      </div>

      {/* Live progress feed */}
      {isRunning && (
        <Card className="mb-6">
          <CardHeader><p className="font-semibold text-sm text-gray-900">Pipeline Progress</p></CardHeader>
          <CardBody><ProgressFeed scanId={scanId} /></CardBody>
        </Card>
      )}

      {/* Error state */}
      {scan.status === "failed" && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <p className="text-sm font-medium text-red-800">Scan failed</p>
          <p className="text-xs text-red-600 mt-1 font-mono">{scan.error}</p>
        </div>
      )}

      {/* Charts — only show when complete */}
      {scan.status === "complete" && clusters.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader><p className="font-semibold text-sm text-gray-900">Verdict Breakdown</p></CardHeader>
            <CardBody className="pt-0">
              <VerdictPie
                likely={scan.likely_count ?? 0}
                maybe={scan.maybe_count ?? 0}
                low={scan.low_count ?? 0}
              />
            </CardBody>
          </Card>
          <Card>
            <CardHeader><p className="font-semibold text-sm text-gray-900">Platforms Found</p></CardHeader>
            <CardBody className="pt-0"><PlatformBar clusters={clusters} /></CardBody>
          </Card>
          <Card>
            <CardHeader><p className="font-semibold text-sm text-gray-900">Confidence Distribution</p></CardHeader>
            <CardBody className="pt-0"><ConfidenceHistogram clusters={clusters} /></CardBody>
          </Card>
        </div>
      )}

      {/* Summary stats */}
      {scan.status === "complete" && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[
            { label: "Total clusters", value: scan.total_clusters ?? 0, colour: "text-gray-900" },
            { label: "Likely",  value: scan.likely_count ?? 0, colour: "text-green-600" },
            { label: "Maybe",   value: scan.maybe_count  ?? 0, colour: "text-yellow-600" },
            { label: "Low",     value: scan.low_count    ?? 0, colour: "text-red-500" },
          ].map(s => (
            <Card key={s.label}>
              <CardBody className="text-center py-3">
                <p className={`text-2xl font-bold ${s.colour}`}>{s.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Cluster list with filters */}
      {scan.status === "complete" && (
        <>
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className="text-sm font-medium text-gray-700">Filter:</span>
            {[null, "likely", "maybe", "low"].map(v => (
              <button key={v ?? "all"}
                className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                  verdictFilter === v
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"
                }`}
                onClick={() => setVerdictFilter(v)}>
                {v ?? "All"}
              </button>
            ))}
            {platforms.length > 0 && (
              <select value={platformFilter} onChange={e => setPlatformFilter(e.target.value)}
                className="text-xs px-2 py-1 border border-gray-300 rounded-full focus:outline-none">
                <option value="">All platforms</option>
                {platforms.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            )}
            <label className="text-xs text-gray-500 flex items-center gap-1">
              Min confidence:
              <input type="range" min="0" max="0.9" step="0.05" value={minConf}
                onChange={e => setMinConf(parseFloat(e.target.value))} className="w-20" />
              <span className="font-mono">{Math.round(minConf * 100)}%</span>
            </label>
          </div>

          {loadingClusters ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : clusters.length === 0 ? (
            <p className="text-center text-gray-400 text-sm py-8">No clusters match your filters.</p>
          ) : (
            <div className="space-y-2">
              {clusters.map(c => <ClusterRow key={c.id} cluster={c} />)}
            </div>
          )}
        </>
      )}
    </div>
  );
}
