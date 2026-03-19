import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export function PlatformBar({ clusters = [] }) {
  const counts = {};
  for (const c of clusters) {
    const p = c.platform || "unknown";
    counts[p] = (counts[p] || 0) + 1;
  }
  const data = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(([platform, count]) => ({ platform, count }));

  if (data.length === 0) return <p className="text-sm text-gray-400 text-center py-8">No data</p>;

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 40 }}>
        <XAxis dataKey="platform" tick={{ fontSize: 11 }} angle={-40} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={`hsl(${240 + i * 15}, 70%, 60%)`} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
