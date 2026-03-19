/**
 * A coloured horizontal bar showing a confidence score 0–1.
 * Green ≥ 0.75 | Yellow ≥ 0.55 | Red < 0.55
 */
export function ConfidenceBar({ value, showLabel = true }) {
  const pct = Math.round((value ?? 0) * 100);
  const colour =
    pct >= 75 ? "bg-green-500" :
    pct >= 55 ? "bg-yellow-400" :
                "bg-red-400";

  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div className={`h-2 rounded-full transition-all ${colour}`} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && (
        <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
      )}
    </div>
  );
}
