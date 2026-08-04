import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  Bot,
  User,
  Copy,
  Check,
  Sparkles,
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

  const [copied, setCopied] =
    useState(false);

  const copyMessage = async () => {

    await navigator.clipboard.writeText(content);

    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 2000);

  };

  return (

    <div
      className={`

      flex

      items-start

      gap-5

      ${
        isUser

          ? "justify-end"

          : "justify-start"

      }

      `}
    >

      {/* AI Avatar */}

      {

        !isUser && (

          <div
            className="
            relative

            flex

            h-14
            w-14

            flex-shrink-0

            items-center
            justify-center

            rounded-3xl

            bg-gradient-to-br

            from-cyan-400

            via-cyan-500

            to-blue-600

            shadow-[0_0_35px_rgba(34,211,238,0.45)]
            "
          >

            <Bot
              size={24}
              className="text-white"
            />

          </div>

        )

      }

      {/* Bubble */}

      <div
        className={`
        relative

        max-w-[850px]

        overflow-hidden

        rounded-3xl

        transition-all

        duration-300

        ${
          isUser

            ? `
            bg-gradient-to-br

            from-cyan-500

            via-cyan-500

            to-blue-600

            text-white

            shadow-[0_0_35px_rgba(34,211,238,0.18)]
            `

            : `
            border

            border-cyan-500/20

            bg-slate-900/60

            backdrop-blur-2xl

            shadow-[0_0_35px_rgba(34,211,238,0.08)]
            `
        }
        `}
      >

        {/* Ambient Glow */}

        {

          !isUser && (

            <div
              className="
              absolute

              -right-20
              -top-20

              h-52
              w-52

              rounded-full

              bg-cyan-500/10

              blur-[120px]
              "
            />

          )

        }

        {/* Copy */}

        {

          !isUser && (

            <button

              onClick={copyMessage}

              className="
              absolute

              right-5
              top-5

              z-20

              rounded-xl

              border

              border-cyan-500/10

              bg-slate-800/60

              p-2

              text-slate-500

              backdrop-blur

              transition-all

              duration-300

              hover:scale-105

              hover:border-cyan-400/30

              hover:bg-cyan-500/10

              hover:text-cyan-300
              "

            >

              {

                copied

                  ? <Check size={18} />

                  : <Copy size={18} />

              }

            </button>

          )

        }

        {/* Assistant Header */}

        {

          !isUser && (

            <div
              className="
              relative

              flex

              items-center

              justify-between

              border-b

              border-cyan-500/15

              px-6

              py-5
              "
            >

              <div className="flex items-center gap-3">

                <Sparkles
                  size={18}
                  className="text-cyan-300"
                />

                <div>

                  <h3 className="font-semibold text-white">

                    CyberGPT

                  </h3>

                  <p
                    className="
                    text-xs

                    text-slate-400
                    "
                  >

                    Enterprise AI Security Assistant

                  </p>

                </div>

              </div>

            </div>

          )

        }

        {/* Content */}

        <div className="relative px-6 py-5">

          {

            isUser

              ? (

                <p
                  className="
                  whitespace-pre-wrap

                  leading-8

                  text-white
                  "
                >

                  {content}

                </p>

              )

              : (

                <div
                  className="
prose

prose-invert

max-w-none

text-slate-200

[&_p]:text-slate-200
[&_p]:leading-8

[&_strong]:text-cyan-300

[&_em]:text-slate-100

[&_h1]:text-white
[&_h2]:text-white
[&_h3]:text-white
[&_h4]:text-white

[&_li]:text-slate-200

[&_ul]:text-slate-200
[&_ol]:text-slate-200

[&_a]:text-cyan-300

[&_blockquote]:text-slate-300
[&_blockquote]:border-cyan-500

[&_table]:text-slate-200

[&_th]:text-white
[&_td]:text-slate-300

[&_code]:text-cyan-300

[&_pre]:bg-[#081423]
[&_pre]:border
[&_pre]:border-cyan-500/20
[&_pre]:rounded-2xl
[&_pre]:p-5
"
                >

                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                  >

                    {content}

                  </ReactMarkdown>

                </div>

              )

          }

        </div>

        {/* Sources */}

        {

          !isUser &&

          sources.length > 0 && (

            <div
              className="
              border-t

              border-cyan-500/15

              px-6

              py-5
              "
            >

              <div className="mb-5 flex items-center justify-between">

                <h3
                  className="
                  text-lg

                  font-semibold

                  text-white
                  "
                >

                  📚 Knowledge Sources

                </h3>

                <span
                  className="
                  rounded-full

                  border

                  border-cyan-500/20

                  bg-cyan-500/10

                  px-3

                  py-1

                  text-xs

                  text-cyan-300
                  "
                >

                  {sources.length} Source{sources.length > 1 ? "s" : ""}

                </span>

              </div>

              <div className="space-y-3">

                {

                  sources.map(

                    (

                      source,

                      index,

                    ) => (

                      <SourceCard

                        key={index}

                        source={source}

                      />

                    ),

                  )

                }

              </div>

            </div>

          )

        }

        {/* Footer */}

        {

          !isUser && (

            <div
              className="
              flex

              items-center

              justify-between

              border-t

              border-cyan-500/10

              bg-slate-900/40

              px-6

              py-4
              "
            >

              <div
                className="
                flex

                items-center

                gap-2

                text-sm

                text-slate-500
                "
              >

                <Sparkles
                  size={15}
                  className="text-cyan-400"
                />

                AI-generated response

              </div>

              <button

                onClick={copyMessage}

                className="
                flex

                items-center

                gap-2

                rounded-xl

                border

                border-cyan-500/15

                bg-slate-800/40

                px-3

                py-2

                text-sm

                text-slate-400

                transition-all

                hover:border-cyan-400/30

                hover:bg-cyan-500/10

                hover:text-cyan-300
                "

              >

                {

                  copied

                    ? (

                      <>

                        <Check size={16} />

                        Copied

                      </>

                    )

                    : (

                      <>

                        <Copy size={16} />

                        Copy

                      </>

                    )

                }

              </button>

            </div>

          )

        }

      </div>

      {/* User Avatar */}

      {

        isUser && (

          <div
            className="
            flex

            h-14

            w-14

            flex-shrink-0

            items-center

            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-slate-700

            via-slate-800

            to-slate-900

            shadow-[0_0_25px_rgba(15,23,42,0.45)]
            "
          >

            <User
              size={24}
              className="text-white"
            />

          </div>

        )

      }

    </div>

  );

}