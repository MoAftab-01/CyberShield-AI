import { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

export default function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed",

        {
          "w-full": fullWidth,

          "px-3 py-2 text-sm": size === "sm",
          "px-5 py-2.5": size === "md",
          "px-6 py-3 text-lg": size === "lg",

          "bg-blue-600 hover:bg-blue-700 text-white shadow-lg":
            variant === "primary",

          "bg-slate-700 hover:bg-slate-600 text-white":
            variant === "secondary",

          "border border-slate-700 hover:bg-slate-800":
            variant === "outline",

          "bg-red-600 hover:bg-red-700 text-white":
            variant === "danger",

          "hover:bg-slate-800":
            variant === "ghost",
        },

        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 size={18} className="animate-spin" />
      ) : (
        leftIcon
      )}

      {children}

      {!loading && rightIcon}
    </button>
  );
}