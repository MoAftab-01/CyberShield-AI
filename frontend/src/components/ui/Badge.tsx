import clsx from "clsx";

interface Props {
  severity: string;
}

export default function Badge({ severity }: Props) {
  const color = {
    CRITICAL: "bg-red-600",
    HIGH: "bg-orange-500",
    MEDIUM: "bg-yellow-500 text-black",
    LOW: "bg-green-600",
  }[severity.toUpperCase()] ?? "bg-slate-600";

  return (
    <span
      className={clsx(
        "rounded-full px-3 py-1 text-xs font-semibold",
        color
      )}
    >
      {severity}
    </span>
  );
}