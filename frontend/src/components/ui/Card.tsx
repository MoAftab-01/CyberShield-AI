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
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={clsx(
        "rounded-xl border border-gray-200 bg-white p-6 shadow-sm text-gray-900",
        className
      )}
    >
      {children}
    </motion.div>
  );
}