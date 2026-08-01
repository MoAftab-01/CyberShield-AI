interface ActivityCardProps {
  title: string;
  time: string;
  status: "success" | "warning" | "danger";
}

const statusColors = {
  success: "bg-green-500",
  warning: "bg-yellow-500",
  danger: "bg-red-500",
};

export default function ActivityCard({
  title,
  time,
  status,
}: ActivityCardProps) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-4">
        <div
          className={`h-3 w-3 rounded-full ${statusColors[status]}`}
        />

        <div>
          <h4 className="font-medium text-slate-800">
            {title}
          </h4>

          <p className="text-sm text-slate-500">
            {time}
          </p>
        </div>
      </div>
    </div>
  );
}