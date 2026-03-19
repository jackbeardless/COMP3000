import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export function ConfidenceHistogram({ clusters = [] }) {
  // Bucket into 10% bands
  const buckets = Array.from({ length: 10 }, (_, i) => ({
    range: `${i * 10}–${i * 10 + 10}%`,
    count: 0,
  }));

  for (const c of clusters) {
    const pct = Math.min(Math.floor((c.final_confidence ?? 0) * 10), 9);
    buckets[pct].count++;
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={buckets} margin={{ top: 0, right: 0, left: -20, bottom: 20 }}>
        <XAxis dataKey="range" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" fill="#6366f1" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
