import { ArrowRight, type LucideIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface QuickActionCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  route: string;
}

export default function QuickActionCard({
  title,
  description,
  icon: Icon,
  route,
}: QuickActionCardProps) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(route)}
      className="group w-full rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-cyan-500 hover:shadow-lg"
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-100">
        <Icon className="text-cyan-600" size={24} />
      </div>

      <h3 className="text-lg font-semibold text-slate-800">
        {title}
      </h3>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>

      <div className="mt-5 flex items-center gap-2 text-cyan-600">
        <span className="text-sm font-medium">
          Open
        </span>

        <ArrowRight
          size={18}
          className="transition-transform group-hover:translate-x-1"
        />
      </div>
    </button>
  );
}