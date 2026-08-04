import { FileText, FolderOpen, File } from "lucide-react";

import { Source } from "@/types/copilot";

interface Props {
  source: Source;
}

export default function SourceCard({
  source,
}: Props) {
  return (
    <div
      className="
      group

      rounded-2xl

      border
      border-cyan-500/15

      bg-slate-900/40

      backdrop-blur-xl

      p-5

      transition-all
      duration-300

      hover:border-cyan-400/30

      hover:shadow-[0_0_25px_rgba(34,211,238,0.12)]
      "
    >

      {/* File Name */}

      <div className="flex items-center gap-3">

        <div
          className="
          flex

          h-10
          w-10

          items-center
          justify-center

          rounded-xl

          bg-cyan-500/10

          border

          border-cyan-500/20
          "
        >

          <FileText
            size={18}
            className="text-cyan-300"
          />

        </div>

        <div className="min-w-0">

          <h4
            className="
            truncate

            font-semibold

            text-white
            "
          >
            {source.filename}
          </h4>

          <p
            className="
            text-xs

            text-slate-400
            "
          >
            PDF Reference
          </p>

        </div>

      </div>

      {/* Metadata */}

      <div className="mt-4 space-y-2">

        <div className="flex items-center gap-2">

          <FolderOpen
            size={15}
            className="text-cyan-400"
          />

          <span
            className="
            text-sm

            text-slate-300
            "
          >
            {source.folder}
          </span>

        </div>

        <div className="flex items-center gap-2">

          <File
            size={15}
            className="text-cyan-400"
          />

          <span
            className="
            text-sm

            text-slate-300
            "
          >
            Page {source.page}
          </span>

        </div>

      </div>

    </div>
  );
}