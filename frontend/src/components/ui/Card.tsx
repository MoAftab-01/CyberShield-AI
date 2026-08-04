import { ReactNode } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface Props {
  children: ReactNode;
  className?: string;
}

export default function Card({
  children,
  className,
}: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={clsx(
        `
        relative

        overflow-hidden

        rounded-[28px]

        border

        border-cyan-400/20

        bg-slate-900/55

        p-6

        text-white

        backdrop-blur-2xl

        shadow-[0_0_45px_rgba(34,211,238,.08)]

        transition-all

        duration-300

        hover:border-cyan-300/35

        hover:shadow-[0_0_55px_rgba(34,211,238,.16)]
        `,
        className
      )}
    >

      {/* Ambient Glow */}

      <div
        className="
        pointer-events-none

        absolute

        -right-10

        -top-10

        h-36

        w-36

        rounded-full

        bg-cyan-500/10

        blur-[90px]
        "
      />

      <div className="relative">

        {children}

      </div>

    </motion.div>
  );
}