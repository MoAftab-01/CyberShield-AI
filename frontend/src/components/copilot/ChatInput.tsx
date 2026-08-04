import { useRef, useState } from "react";

import {
  Send,
  Loader2,
} from "lucide-react";

interface Props {
  loading: boolean;
  onSend: (message: string) => void;
}

export default function ChatInput({
  loading,
  onSend,
}: Props) {

  const [message, setMessage] = useState("");

  const textareaRef =
    useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {

    if (!message.trim()) return;

    onSend(message);

    setMessage("");

    if (textareaRef.current) {

      textareaRef.current.style.height = "52px";

    }

  };

  const resize = () => {

    if (!textareaRef.current) return;

    textareaRef.current.style.height = "52px";

    textareaRef.current.style.height =
      textareaRef.current.scrollHeight + "px";

  };

        return (

  <div className="relative">

    {/* Cyan Glow */}

    <div
      className="
      pointer-events-none

      absolute

      inset-0

      rounded-3xl

      bg-cyan-500/5

      blur-2xl
      "
    />

    <div
      className="
      relative

      flex

      items-end

      gap-3

      rounded-3xl

      border

      border-cyan-500/15

      bg-slate-900/60

      backdrop-blur-2xl

      p-3

      transition-all

      duration-300

      focus-within:border-cyan-400/40

      focus-within:shadow-[0_0_35px_rgba(34,211,238,0.15)]
      "
    >

      {/* Textarea */}

      <textarea

        ref={textareaRef}

        rows={1}

        value={message}

        disabled={loading}

        placeholder="Ask CyberGPT about CVEs, malware, OWASP, MITRE ATT&CK..."

        onChange={(e) => {

          setMessage(e.target.value);

          resize();

        }}

        onKeyDown={(e) => {

          if (
            e.key === "Enter" &&
            !e.shiftKey
          ) {

            e.preventDefault();

            handleSend();

          }

        }}

        className="
        max-h-[180px]

        min-h-[52px]

        flex-1

        resize-none

        overflow-y-auto

        bg-transparent

        px-3

        py-3

        text-[15px]

        leading-7

        text-white

        placeholder:text-slate-500

        outline-none
        "
      />

      {/* Send Button */}

      <button

        disabled={
          loading ||
          !message.trim()
        }

        onClick={handleSend}

        className="
        group

        flex

        h-12

        w-12

        flex-shrink-0

        items-center

        justify-center

        rounded-2xl

        bg-gradient-to-br

        from-cyan-500

        to-blue-600

        text-white

        shadow-[0_0_20px_rgba(34,211,238,0.35)]

        transition-all

        duration-300

        hover:scale-105

        hover:shadow-[0_0_30px_rgba(34,211,238,0.55)]

        disabled:cursor-not-allowed

        disabled:opacity-50
        "
      >

        {

          loading

            ? (

              <Loader2

                size={22}

                className="animate-spin"

              />

            )

            : (

              <Send

                size={20}

                className="
                transition-transform

                duration-300

                group-hover:translate-x-0.5
                "

              />

            )

        }

      </button>

    </div>

    {/* Footer Hint */}

    <div
      className="
      mt-2

      flex

      justify-between

      px-2

      text-xs

      text-slate-500
      "
    >

      <span>

        Shift + Enter for new line

      </span>

      <span>

        Enter to send

      </span>

    </div>

  </div>

);
}

