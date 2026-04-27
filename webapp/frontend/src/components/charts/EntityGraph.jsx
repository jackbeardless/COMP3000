import { useState, useRef, useEffect } from "react";

function platformLabel(platform, urls) {
  if (platform && platform !== "unknown") return platform;
  const url = Array.isArray(urls) ? urls[0] : urls;
  if (!url) return "unknown";
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    return host.split(".")[0];
  } catch {
    return "unknown";
  }
}

const VERDICT_COLOUR = {
  likely: { fill: "#166534", bg: "#dcfce7", border: "#16a34a" },
  maybe:  { fill: "#92400e", bg: "#fef3c7", border: "#d97706" },
  low:    { fill: "#991b1b", bg: "#fee2e2", border: "#dc2626" },
};

const NODE_W = 90;
const NODE_H = 36;
const MIN_ARC  = 104; // minimum arc-length spacing between nodes in a ring

function ringRadius(count, base) {
  if (count === 0) return base;
  return Math.max(base, (count * MIN_ARC) / (2 * Math.PI));
}

function placeRing(clusters, radius) {
  return clusters.map((c, i) => {
    const angle = (2 * Math.PI * i / clusters.length) - Math.PI / 2;
    return { cluster: c, x: radius * Math.cos(angle), y: radius * Math.sin(angle) };
  });
}

export function EntityGraph({ clusters, target }) {
  const containerRef = useRef(null);
  const [width, setWidth]     = useState(800);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.floor(e.contentRect.width)));
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const likely = clusters.filter(c => c.verdict === "likely");
  const maybe  = clusters.filter(c => c.verdict === "maybe");
  const low    = clusters.filter(c => c.verdict === "low");

  const r1 = ringRadius(likely.length, 130);
  const r2 = ringRadius(maybe.length,  r1 + 95);
  const r3 = ringRadius(low.length,    r2 + 95);

  const outerR = (low.length ? r3 : maybe.length ? r2 : r1) + NODE_W / 2 + 12;
  const viewBox = `${-outerR} ${-outerR} ${outerR * 2} ${outerR * 2}`;
  const svgH = Math.round(width * 0.58);

  const nodes = [
    ...placeRing(likely, r1),
    ...placeRing(maybe,  r2),
    ...placeRing(low,    r3),
  ];

  const selCluster = selected !== null ? nodes[selected]?.cluster : null;

  const contCt = clusters.filter(c => (c.contradiction_flags ?? []).length > 0).length;

  return (
    <div ref={containerRef} className="border border-gray-200 rounded-xl overflow-hidden">
      <div className="relative bg-slate-950">
        <svg width={width} height={svgH} viewBox={viewBox} style={{ display: "block" }}>

          {/* Edges — drawn first so they sit under nodes */}
          {nodes.map(({ cluster, x, y }, i) => {
            const conf = cluster.final_confidence ?? cluster.heuristic_score ?? 0;
            const col  = VERDICT_COLOUR[cluster.verdict] ?? VERDICT_COLOUR.low;
            return (
              <line key={i}
                x1={0} y1={0} x2={x} y2={y}
                stroke={col.border}
                strokeWidth={1 + conf * 3}
                strokeOpacity={0.28 + conf * 0.42}
                strokeDasharray={cluster.verdict === "low" ? "6,4" : undefined}
              />
            );
          })}

          {/* Target node */}
          <circle cx={0} cy={0} r={32} fill="#1e40af" stroke="#1e3a8a" strokeWidth={2.5} />
          <text x={0} y={-8}  textAnchor="middle" fontSize={9}  fill="rgba(255,255,255,0.5)" fontFamily="sans-serif">TARGET</text>
          <text x={0} y={10}  textAnchor="middle" fontSize={13} fontWeight={700} fill="white" fontFamily="sans-serif">
            {target.length > 12 ? target.slice(0, 11) + "…" : target}
          </text>

          {/* Cluster nodes */}
          {nodes.map(({ cluster, x, y }, i) => {
            const col      = VERDICT_COLOUR[cluster.verdict] ?? VERDICT_COLOUR.low;
            const label    = platformLabel(cluster.platform, cluster.urls);
            const handle   = cluster.handle;
            const isSelected = selected === i;
            const hasContra  = (cluster.contradiction_flags ?? []).length > 0;
            const hw = NODE_W / 2, hh = NODE_H / 2;

            return (
              <g key={i} onClick={() => setSelected(p => p === i ? null : i)} style={{ cursor: "pointer" }}>
                <rect
                  x={x - hw} y={y - hh} width={NODE_W} height={NODE_H} rx={7}
                  fill={col.bg}
                  stroke={isSelected ? col.fill : col.border}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                />
                {/* Left accent stripe */}
                <rect x={x - hw} y={y - hh} width={4} height={NODE_H} rx={2} fill={col.border} />

                <text x={x + 2} y={y + (handle ? -4 : 5)}
                  textAnchor="middle" fontSize={11} fontWeight={700}
                  fill={col.fill} fontFamily="sans-serif">
                  {label.length > 11 ? label.slice(0, 10) + "…" : label}
                </text>
                {handle && (
                  <text x={x + 2} y={y + 9}
                    textAnchor="middle" fontSize={9} fill="#6b7280" fontFamily="monospace">
                    {(`@${handle}`).length > 13 ? `@${handle}`.slice(0, 12) + "…" : `@${handle}`}
                  </text>
                )}

                {/* Contradiction warning dot */}
                {hasContra && (
                  <>
                    <circle cx={x + hw - 6} cy={y - hh + 6} r={6} fill="#f59e0b" />
                    <text x={x + hw - 6} y={y - hh + 10} textAnchor="middle" fontSize={8} fontWeight={700} fill="white">!</text>
                  </>
                )}
              </g>
            );
          })}
        </svg>

        {/* Detail panel */}
        {selCluster && (
          <div className="absolute top-3 right-3 bg-white rounded-xl border border-gray-200 shadow-lg p-4 w-56 text-xs z-10">
            <p className="font-bold text-gray-900 mb-1">
              {platformLabel(selCluster.platform, selCluster.urls)}
              {selCluster.handle && (
                <span className="font-mono font-normal text-gray-500 ml-1">@{selCluster.handle}</span>
              )}
            </p>
            <p className="font-semibold mb-2" style={{ color: (VERDICT_COLOUR[selCluster.verdict] ?? VERDICT_COLOUR.low).border }}>
              {selCluster.verdict} · {Math.round((selCluster.final_confidence ?? selCluster.heuristic_score ?? 0) * 100)}%
            </p>
            {selCluster.rationale && (
              <p className="text-gray-500 leading-relaxed mb-2">
                {selCluster.rationale.slice(0, 160)}{selCluster.rationale.length > 160 ? "…" : ""}
              </p>
            )}
            {(selCluster.contradiction_flags ?? []).length > 0 && (
              <p className="text-amber-600 font-medium mb-2">
                ⚠ {selCluster.contradiction_flags.length} contradiction{selCluster.contradiction_flags.length > 1 ? "s" : ""}
              </p>
            )}
            {selCluster.urls?.[0] && (
              <a href={selCluster.urls[0]} target="_blank" rel="noopener noreferrer"
                className="block text-brand-600 hover:underline truncate mb-2">
                {selCluster.urls[0]}
              </a>
            )}
            <button className="text-gray-400 hover:text-gray-600" onClick={() => setSelected(null)}>
              Dismiss ×
            </button>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 px-4 py-2.5 bg-slate-900 text-xs flex-wrap">
        <span className="text-gray-400 font-medium">Legend:</span>
        {[
          { colour: "#16a34a", label: `Likely (${likely.length})` },
          { colour: "#d97706", label: `Maybe (${maybe.length})` },
          { colour: "#dc2626", label: `Low (${low.length})` },
        ].map(l => (
          <span key={l.label} className="flex items-center gap-1.5 text-gray-300">
            <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: l.colour }} />
            {l.label}
          </span>
        ))}
        {contCt > 0 && <span className="text-amber-400 font-medium">⚠ {contCt} with contradictions</span>}
        <span className="ml-auto text-gray-500">Click a node for detail</span>
      </div>
    </div>
  );
}
