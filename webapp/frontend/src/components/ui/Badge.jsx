const STYLES = {
  likely:       "bg-green-100 text-green-800 border border-green-200",
  maybe:        "bg-yellow-100 text-yellow-800 border border-yellow-200",
  low:          "bg-red-100 text-red-800 border border-red-200",
  confirmed:    "bg-green-100 text-green-800 border border-green-200",
  disputed:     "bg-red-100 text-red-800 border border-red-200",
  needs_review: "bg-orange-100 text-orange-800 border border-orange-200",
  running:      "bg-blue-100 text-blue-800 border border-blue-200",
  complete:     "bg-green-100 text-green-800 border border-green-200",
  failed:       "bg-red-100 text-red-800 border border-red-200",
  queued:       "bg-gray-100 text-gray-600 border border-gray-200",
  active:       "bg-brand-100 text-brand-700 border border-brand-200",
  archived:     "bg-gray-100 text-gray-500 border border-gray-200",
};

export function Badge({ label, variant }) {
  const cls = STYLES[variant] ?? "bg-gray-100 text-gray-600 border border-gray-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {label ?? variant}
    </span>
  );
}
