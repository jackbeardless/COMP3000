import { useEffect, useRef, useState, useCallback } from "react";
import {
  forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide,
} from "d3-force";

const VERDICT_COLOUR = {
  likely: { fill: "#166534", bg: "#dcfce7", border: "#16a34a" },
  maybe:  { fill: "#92400e", bg: "#fef3c7", border: "#d97706" },
  low:    { fill: "#991b1b", bg: "#fee2e2", border: "#dc2626" },
};
const TARGET = { fill: "#fff", bg: "#1e40af", border: "#1e3a8a" };

function ClusterLabel({ node, onHover, hovered }) {
  const c = VERDICT_COLOUR[node.verdict] ?? VERDICT_COLOUR.low;
  const isHovered = hovered === node.id;
  const pad = { x: 10, y: 6 };
  const lineH = 16;
  const lines = [node.platform, node.handle ? `@${node.handle}` : null].filter(Boolean);
  const w = Math.max(90, (Math.max(...lines.map(l => l.length)) * 7) + pad.x * 2);
  const h = lines.length * lineH + pad.y * 2;

  return (
    <g
      transform={`translate(${node.x - w / 2},${node.y - h / 2})`}
      style={{ cursor: "pointer" }}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
    >
      <rect
        x={0} y={0} width={w} height={h} rx={7} ry={7}
        fill={c.bg}
        stroke={isHovered ? c.fill : c.border}
        strokeWidth={isHovered ? 2.5 : 1.5}
        filter={isHovered ? "url(#glow)" : undefined}
      />
      {/* Verdict colour stripe on left edge */}
      <rect x={0} y={0} width={4} height={h} rx={3} ry={3} fill={c.border} />
      {lines.map((line, i) => (
        <text
          key={i}
          x={w / 2 + 2} y={pad.y + lineH * i + 11}
          textAnchor="middle"
          fontSize={i === 0 ? 11 : 9.5}
          fontWeight={i === 0 ? 700 : 400}
          fontFamily={i === 1 ? "monospace" : "sans-serif"}
          fill={i === 0 ? c.fill : "#6b7280"}
        >
          {line}
        </text>
      ))}
      {/* Confidence badge */}
      <text
        x={w - 5} y={h - 4}
        textAnchor="end"
        fontSize={9} fontWeight={700}
        fill={c.border}
      >
        {Math.round(node.confidence * 100)}%
      </text>
      {/* Contradiction dot */}
      {node.contradictions > 0 && (
        <circle cx={w - 7} cy={7} r={6} fill="#f59e0b" />
      )}
      {node.contradictions > 0 && (
        <text x={w - 7} y={11} textAnchor="middle" fontSize={8} fontWeight={700} fill="white">!</text>
      )}
    </g>
  );
}

export function EntityGraph({ clusters, target }) {
  const svgRef = useRef(null);
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [hovered, setHovered] = useState(null);
  const [selected, setSelected] = useState(null);
  const [dims, setDims] = useState({ w: 800, h: 520 });
  const simRef = useRef(null);

  // Measure container width
  useEffect(() => {
    const el = svgRef.current?.parentElement;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      setDims({ w, h: Math.min(560, Math.max(420, w * 0.6)) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Build and run force simulation
  useEffect(() => {
    if (!clusters.length) return;
    const { w, h } = dims;

    const simNodes = [
      { id: "target", type: "target", x: w / 2, y: h / 2, fx: w / 2, fy: h / 2 },
      ...clusters.map((c, i) => ({
        id: `c-${i}`,
        type: "cluster",
        platform: c.platform ?? "unknown",
        handle: c.handle ?? "",
        verdict: c.verdict ?? "low",
        confidence: c.final_confidence ?? c.heuristic_score ?? 0,
        contradictions: (c.contradiction_flags ?? []).length,
        clusterIdx: i,
        x: w / 2 + (Math.random() - 0.5) * 200,
        y: h / 2 + (Math.random() - 0.5) * 200,
      })),
    ];

    const simLinks = clusters.map((_, i) => ({
      source: "target",
      target: `c-${i}`,
      verdict: clusters[i].verdict ?? "low",
      confidence: clusters[i].final_confidence ?? clusters[i].heuristic_score ?? 0,
    }));

    if (simRef.current) simRef.current.stop();

    const sim = forceSimulation(simNodes)
      .force("link", forceLink(simLinks).id(d => d.id).distance(d => {
        // Likely clusters sit closer to the target
        if (d.verdict === "likely") return 140;
        if (d.verdict === "maybe")  return 180;
        return 220;
      }).strength(0.8))
      .force("charge", forceManyBody().strength(-400))
      .force("center", forceCenter(w / 2, h / 2))
      .force("collide", forceCollide(70))
      .on("tick", () => {
        setNodes([...sim.nodes()]);
        setLinks([...simLinks]);
      })
      .on("end", () => {
        setNodes([...sim.nodes()]);
        setLinks([...simLinks]);
      });

    simRef.current = sim;
    return () => sim.stop();
  }, [clusters, dims]);

  const targetNode = nodes.find(n => n.id === "target");
  const clusterNodes = nodes.filter(n => n.type === "cluster");

  const linkStroke = verdict =>
    verdict === "likely" ? "#16a34a"
    : verdict === "maybe" ? "#d97706"
    : "#dc2626";

  const selCluster = selected?.startsWith("c-")
    ? clusters[parseInt(selected.replace("c-", ""))]
    : null;

  const likelyCt = clusters.filter(c => c.verdict === "likely").length;
  const maybeCt  = clusters.filter(c => c.verdict === "maybe").length;
  const lowCt    = clusters.filter(c => c.verdict === "low").length;
  const contCt   = clusters.filter(c => (c.contradiction_flags ?? []).length > 0).length;

  const handleNodeClick = useCallback((id) => {
    setSelected(prev => prev === id ? null : id);
  }, []);

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <div className="relative bg-slate-950" style={{ minHeight: dims.h }}>
        <svg
          ref={svgRef}
          width={dims.w}
          height={dims.h}
          style={{ display: "block" }}
        >
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            {/* Arrow markers per verdict */}
            {Object.entries(VERDICT_COLOUR).map(([v, c]) => (
              <marker key={v} id={`arrow-${v}`} markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                <path d="M0,0 L0,6 L6,3 z" fill={c.border} opacity={0.7} />
              </marker>
            ))}
          </defs>

          {/* Edges */}
          {clusterNodes.map((cn, i) => {
            const lk = links[i];
            if (!lk || !targetNode) return null;
            const conf = cn.confidence ?? 0;
            const verdict = cn.verdict ?? "low";
            return (
              <line
                key={cn.id}
                x1={targetNode.x} y1={targetNode.y}
                x2={cn.x} y2={cn.y}
                stroke={linkStroke(verdict)}
                strokeWidth={1 + conf * 3.5}
                strokeOpacity={0.4 + conf * 0.35}
                strokeDasharray={verdict === "low" ? "5,4" : undefined}
                markerEnd={`url(#arrow-${verdict})`}
              />
            );
          })}

          {/* Target node */}
          {targetNode && (
            <g style={{ cursor: "default" }}>
              <circle
                cx={targetNode.x} cy={targetNode.y} r={34}
                fill={TARGET.bg} stroke={TARGET.border} strokeWidth={2.5}
                filter="url(#glow)"
              />
              <text x={targetNode.x} y={targetNode.y - 7} textAnchor="middle" fontSize={9} fill="rgba(255,255,255,0.6)" fontFamily="sans-serif">
                TARGET
              </text>
              <text x={targetNode.x} y={targetNode.y + 8} textAnchor="middle" fontSize={12} fontWeight={700} fill="white" fontFamily="sans-serif">
                {target.length > 12 ? target.slice(0, 11) + "…" : target}
              </text>
            </g>
          )}

          {/* Cluster nodes */}
          {clusterNodes.map(n => (
            <g key={n.id} onClick={() => handleNodeClick(n.id)}>
              <ClusterLabel
                node={n}
                onHover={setHovered}
                hovered={hovered}
              />
            </g>
          ))}
        </svg>

        {/* Selected detail panel */}
        {selCluster && (
          <div className="absolute top-3 right-3 bg-white rounded-xl border border-gray-200 shadow-lg p-4 w-56 text-xs z-10">
            <p className="font-bold text-gray-900 mb-1">
              {selCluster.platform}
              {selCluster.handle && (
                <span className="font-normal text-gray-500 font-mono ml-1">@{selCluster.handle}</span>
              )}
            </p>
            <p style={{ color: VERDICT_COLOUR[selCluster.verdict]?.border }} className="font-semibold mb-2">
              {selCluster.verdict} · {Math.round((selCluster.final_confidence ?? selCluster.heuristic_score ?? 0) * 100)}%
            </p>
            {selCluster.rationale && (
              <p className="text-gray-500 leading-relaxed">
                {selCluster.rationale.slice(0, 160)}{selCluster.rationale.length > 160 ? "…" : ""}
              </p>
            )}
            {(selCluster.contradiction_flags ?? []).length > 0 && (
              <p className="text-amber-600 mt-2 font-medium">
                ⚠ {selCluster.contradiction_flags.length} contradiction{selCluster.contradiction_flags.length > 1 ? "s" : ""}
              </p>
            )}
            <button className="mt-3 text-gray-400 hover:text-gray-600 text-xs" onClick={() => setSelected(null)}>
              Dismiss ×
            </button>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 px-4 py-2.5 bg-slate-900 text-xs flex-wrap">
        <span className="text-gray-400 font-medium">Legend:</span>
        {[
          { colour: "#16a34a", label: `Likely (${likelyCt})` },
          { colour: "#d97706", label: `Maybe (${maybeCt})` },
          { colour: "#dc2626", label: `Low (${lowCt})` },
        ].map(l => (
          <span key={l.label} className="flex items-center gap-1.5 text-gray-300">
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: l.colour, display: "inline-block" }} />
            {l.label}
          </span>
        ))}
        {contCt > 0 && <span className="text-amber-400 font-medium">⚠ {contCt} with contradictions</span>}
        <span className="ml-auto text-gray-500">Click a node for detail · Solid edges = likely · Dashed = low</span>
      </div>
    </div>
  );
}
