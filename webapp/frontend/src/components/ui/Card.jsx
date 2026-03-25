export function Card({ children, className = "", onClick }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm ${className}`} onClick={onClick}>
      {children}
    </div>
  );
}

export function CardHeader({ children }) {
  return <div className="px-5 py-4 border-b border-gray-100">{children}</div>;
}

export function CardBody({ children, className = "" }) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>;
}
