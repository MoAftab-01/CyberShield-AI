interface Props {
  severity: string;
}

export default function SeverityBadge({ severity }: Props) {
  const colors: Record<string, string> = {
    CRITICAL: "bg-red-600",
    HIGH: "bg-orange-500",
    MEDIUM: "bg-yellow-500",
    LOW: "bg-green-600",
  };

  return (
    <span
      className={`px-3 py-1 rounded-full text-white text-sm font-semibold ${
        colors[severity] || "bg-gray-500"
      }`}
    >
      {severity}
    </span>
  );
}