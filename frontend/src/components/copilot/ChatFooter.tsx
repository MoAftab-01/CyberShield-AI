import ChatInput from "./ChatInput";
import UploadButton from "../upload/UploadButton";

import { UploadedDocument } from "@/services/uploadService";

import {
  Sparkles,
  FileText,
  X,
} from "lucide-react";

interface Props {
  loading: boolean;
  uploadedFiles: UploadedDocument[];
  onSend: (message: string) => void;
  onUpload: (file: File) => void;
  onDeleteDocument: (filename: string) => void;
}

export default function ChatFooter({
  loading,
  uploadedFiles,
  onSend,
  onUpload,
  onDeleteDocument,
}: Props) {
  return (

  <footer
    className="
    flex-shrink-0

    px-6

    pb-6

    pt-4
    "
  >

    <div className="mx-auto max-w-5xl">

      {/* Floating Composer */}

      <div
        className="
        group

        relative

        overflow-hidden

        rounded-[32px]

        border

        border-cyan-400/25

        bg-slate-900/75

        backdrop-blur-3xl

        transition-all

        duration-500

        hover:border-cyan-300/45

        hover:shadow-[0_0_80px_rgba(34,211,238,.18),0_20px_60px_rgba(0,0,0,.55)]
        "
      >

        {/* Ambient Glow */}

        <div
          className="
          pointer-events-none

          absolute

          left-1/2

          top-0

          h-52

          w-[520px]

          -translate-x-1/2

          rounded-full

          bg-cyan-500/15

          blur-[120px]
          "
        />

        {/* Uploaded Files */}

        {uploadedFiles.length > 0 && (

          <div
            className="
            relative

            flex

            flex-wrap

            gap-3

            p-5

            pb-4
            "
          >

            {uploadedFiles.map((file) => (

              <div

                key={file.filename}

                className="
                flex

                items-center

                gap-3

                rounded-full

                border

                border-cyan-500/20

                bg-slate-800/70

                px-4

                py-2

                text-sm

                transition-all

                duration-300

                hover:border-cyan-400/40

                hover:bg-slate-800

                hover:shadow-[0_0_25px_rgba(34,211,238,.15)]
                "

              >

                <FileText
                  size={16}
                  className="text-cyan-400"
                />

                <span
                  className="
                  max-w-[220px]

                  truncate

                  text-slate-200
                  "
                >

                  {file.filename}

                </span>

                <button

                  onClick={() =>
                    onDeleteDocument(
                      file.filename,
                    )
                  }

                  className="
                  rounded-full

                  p-1

                  text-slate-400

                  transition-all

                  hover:bg-red-500/20

                  hover:text-red-400
                  "

                >

                  <X size={14} />

                </button>

              </div>

            ))}

          </div>

        )}

        {/* Divider */}

        {uploadedFiles.length > 0 && (

          <div
            className="
            mx-5

            border-t

            border-cyan-500/10
            "
          />

        )}

        {/* Composer */}

        <div
          className="
          relative

          flex

          items-center

          gap-4

          p-5
          "
        >

          {/* Upload */}

          <div
            className="
            flex-shrink-0
            "
          >

            <UploadButton
              onUpload={onUpload}
            />

          </div>

          {/* Chat */}

          <div className="flex-1">

            <ChatInput
              loading={loading}
              onSend={onSend}
            />

          </div>

        </div>

      </div>

      {/* Bottom Hint */}

      <div
        className="
        mt-3

        flex

        items-center

        justify-between

        px-2

        text-xs

        text-slate-500
        "
      >

        <div
          className="
          flex

          items-center

          gap-2
          "
        >

          <Sparkles
            size={13}
            className="text-cyan-400"
          />

          <span>

            Powered by
            <span className="ml-1 font-medium text-cyan-400">
              CyberGPT
            </span>

          </span>

        </div>

        <span>

          Press

          <kbd
            className="
            mx-1

            rounded-md

            border

            border-slate-700

            bg-slate-900

            px-2

            py-0.5

            text-slate-300
            "
          >

            Enter

          </kbd>

          to send

        </span>

      </div>

    </div>

  </footer>

);
}