import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const COLOURS = { likely: "#22c55e", maybe: "#facc15", low: "#f87171" };

export function VerdictPie({ likely = 0, maybe = 0, low = 0 }) {
  const data = [
    { name: "Likely",  value: likely, key: "likely" },
    { name: "Maybe",   value: maybe,  key: "maybe" },
    { name: "Low",     value: low,    key: "low" },
  ].filter(d => d.value > 0);

  if (data.length === 0) return <p className="text-sm text-gray-400 text-center py-8">No data</p>;

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%"
          innerRadius={55} outerRadius={85} paddingAngle={3} label={false}>
          {data.map(d => <Cell key={d.key} fill={COLOURS[d.key]} />)}
        </Pie>
        <Tooltip formatter={(v) => [`${v} clusters`]} />
        <Legend iconType="circle" iconSize={10} />
      </PieChart>
    </ResponsiveContainer>
  );
}
