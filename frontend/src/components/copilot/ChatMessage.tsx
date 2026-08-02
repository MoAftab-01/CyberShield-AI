import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  Bot,
  User,
  Copy,
  Check,
} from "lucide-react";

import { useState } from "react";

import SourceCard from "./SourceCard";

import { Source } from "@/types/copilot";

interface Props {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export default function ChatMessage({
  role,
  content,
  sources = [],
}: Props) {
  const isUser = role === "user";

  const [copied, setCopied] = useState(false);

  const copyMessage = async () => {
    await navigator.clipboard.writeText(content);

    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  return (
    <div
      className={`flex gap-4 ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {/* AI Avatar */}

      {!isUser && (
        <div
          className="
          w-11
          h-11
          rounded-2xl
          bg-cyan-600
          flex
          items-center
          justify-center
          text-white
          shadow-lg
          flex-shrink-0
          "
        >
          <Bot size={20} />
        </div>
      )}

      {/* Bubble */}

      <div
        className={`
          max-w-4xl
          rounded-2xl
          px-6
          py-5
          shadow-sm
          relative

          ${
            isUser
              ? "bg-cyan-600 text-white"
              : "bg-white border border-slate-200"
          }
        `}
      >
        {/* Copy Button */}

        {!isUser && (
          <button
            onClick={copyMessage}
            className="
            absolute
            top-4
            right-4
            text-slate-400
            hover:text-cyan-600
            transition
            "
          >
            {copied ? (
              <Check size={18} />
            ) : (
              <Copy size={18} />
            )}
          </button>
        )}

        {/* User */}

        {isUser ? (
          <p className="whitespace-pre-wrap leading-7">
            {content}
          </p>
        ) : (
          <div
            className="
            prose
            prose-slate
            max-w-none

            prose-headings:text-slate-800
            prose-headings:font-bold

            prose-p:leading-8

            prose-strong:text-slate-900

            prose-code:text-cyan-600
            prose-code:before:content-none
            prose-code:after:content-none

            prose-pre:bg-slate-950
            prose-pre:text-white

            prose-li:my-1

            prose-table:block
            prose-table:overflow-x-auto
            "
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
          </div>
        )}

        {/* Sources */}

        {!isUser && sources.length > 0 && (
          <div className="mt-8 border-t pt-6">
            <h3 className="font-semibold text-slate-700 mb-4">
              📚 Sources
            </h3>

            <div className="space-y-3">
              {sources.map((source, index) => (
                <SourceCard
                  key={index}
                  source={source}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* User Avatar */}

      {isUser && (
        <div
          className="
          w-11
          h-11
          rounded-2xl
          bg-slate-800
          flex
          items-center
          justify-center
          text-white
          shadow-lg
          flex-shrink-0
          "
        >
          <User size={20} />
        </div>
      )}
    </div>
  );
}