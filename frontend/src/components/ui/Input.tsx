import { forwardRef, InputHTMLAttributes } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="w-full space-y-3">

        {label && (
          <label
            className="
            block

            text-sm

            font-semibold

            tracking-wide

            text-slate-300
            "
          >
            {label}
          </label>
        )}

        <input
          ref={ref}
          className={clsx(
            `
            w-full

            rounded-2xl

            border

            border-cyan-400/20

            bg-slate-900/60

            px-5

            py-3.5

            text-white

            placeholder:text-slate-500

            backdrop-blur-xl

            outline-none

            transition-all

            duration-300

            shadow-[0_0_20px_rgba(34,211,238,0.04)]

            hover:border-cyan-300/35

            hover:shadow-[0_0_30px_rgba(34,211,238,0.08)]

            focus:border-cyan-300

            focus:bg-slate-900/70

            focus:ring-2

            focus:ring-cyan-400/20

            focus:shadow-[0_0_40px_rgba(34,211,238,0.18)]
            `,
            error &&
              `
              border-red-500/50

              focus:border-red-400

              focus:ring-red-500/20

              focus:shadow-[0_0_35px_rgba(239,68,68,0.18)]
              `,
            className
          )}
          {...props}
        />

        {error && (
          <p
            className="
            text-sm

            font-medium

            text-red-400
            "
          >
            {error}
          </p>
        )}

      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;