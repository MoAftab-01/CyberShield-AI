import {
  Shield,
  Sparkles,
  Plus,
} from "lucide-react";

import ConversationList from "./ConversationList";
import SearchConversation from "./SearchConversation";

import { ConversationItem } from "@/services/conversationService";

interface Props {
  conversations: ConversationItem[];
  loading: boolean;
  search: string;
  activeConversationId: number | null;
  onSearch: (value: string) => void;
  onSelectConversation: (id: number) => void;
  onDeleteConversation: (id: number) => void;
  onNewChat: () => void;
}

export default function ConversationSidebar({
  conversations,
  loading,
  search,
  activeConversationId,
  onSearch,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
}: Props) {
  return (
    <aside
      className="
      relative

      flex

      h-full

      w-[280px]

      flex-col

      border-r

      border-cyan-500/10

      bg-[#050C18]/95

      backdrop-blur-3xl
      "
    >
      {/* Ambient Glow */}

      <div
        className="
        pointer-events-none

        absolute

        left-0

        top-0

        h-56

        w-56

        rounded-full

        bg-cyan-500/10

        blur-[110px]
        "
      />

      {/* Header */}

      <div className="relative px-4 pt-5 pb-4">

        <div className="flex items-center gap-3">

          <div
            className="
            flex

            h-12

            w-12

            items-center

            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-cyan-400

            via-cyan-500

            to-blue-600

            shadow-[0_0_35px_rgba(34,211,238,.45)]
            "
          >

            <Shield
              size={24}
              className="text-white"
            />

          </div>

          <div>

            <h2
              className="
              text-lg

              font-bold

              tracking-tight

              text-white
              "
            >
              CyberGPT
            </h2>

            <div className="mt-1 flex items-center gap-1.5">

              <Sparkles
                size={12}
                className="text-cyan-400"
              />

              <p
                className="
                text-[11px]

                uppercase

                tracking-[0.18em]

                text-cyan-300
                "
              >
                Enterprise AI
              </p>

            </div>

          </div>

        </div>

        {/* New Chat */}

<button
  onClick={onNewChat}
  className="
  group

  relative

  mt-5

  w-full

  overflow-hidden

  rounded-2xl

  border

  border-cyan-400/20

  bg-slate-900/75

  px-4

  py-4

  text-left

  backdrop-blur-2xl

  transition-all

  duration-500

  hover:-translate-y-1

  hover:border-cyan-300/45

  hover:shadow-[0_0_35px_rgba(34,211,238,.18)]
  "
>

  {/* Glow */}

  <div
    className="
    absolute

    -right-10

    -top-10

    h-36

    w-36

    rounded-full

    bg-cyan-500/20

    blur-[80px]

    transition-all

    duration-700

    group-hover:scale-125

    group-hover:opacity-80
    "
  />

  <div className="relative flex items-center justify-between">

    <div className="flex items-center gap-3">

      {/* Icon */}

      <div
        className="
        flex

        h-10

        w-10

        items-center

        justify-center

        rounded-xl

        bg-gradient-to-br

        from-cyan-400

        via-cyan-500

        to-blue-600

        shadow-[0_0_22px_rgba(34,211,238,.35)]
        "
      >

        <Sparkles
          size={18}
          className="text-white"
        />

      </div>

      {/* Text */}

      <div>

        <h3
          className="
          text-[15px]

          font-semibold

          text-white
          "
        >
          New Chat
        </h3>

        <p
          className="
          mt-1

          text-xs

          text-slate-400
          "
        >
          Start secure AI session
        </p>

      </div>

    </div>

    {/* Plus */}

    <div
      className="
      flex

      h-8

      w-8

      items-center

      justify-center

      rounded-full

      border

      border-cyan-400/20

      bg-cyan-500/10

      text-cyan-300

      transition-all

      duration-300

      group-hover:rotate-90

      group-hover:bg-cyan-500/20

      group-hover:shadow-[0_0_16px_rgba(34,211,238,.3)]
      "
    >

      <Plus size={14} />

    </div>

  </div>

</button>

      </div>

    {/* Divider */}

          {/* Divider */}

      <div className="mx-4 border-t border-cyan-500/10" />

      {/* Search */}

      <div className="px-4 py-4">

        <SearchConversation
          value={search}
          onChange={onSearch}
        />

      </div>

      {/* History */}

      <div
        className="
        flex-1

        overflow-y-auto

        px-3

        pb-4

        scrollbar-thin

        scrollbar-thumb-slate-700

        scrollbar-track-transparent
        "
      >

        <ConversationList
          conversations={conversations}
          loading={loading}
          activeConversationId={activeConversationId}
          onSelect={onSelectConversation}
          onDelete={onDeleteConversation}
        />

      </div>

      {/* Divider */}

      <div className="mx-4 border-t border-cyan-500/10" />

      {/* Workspace */}

      <div className="p-4">

        <div
          className="
          group

          relative

          overflow-hidden

          rounded-2xl

          border

          border-cyan-500/10

          bg-slate-900/70

          px-4

          py-3

          backdrop-blur-xl

          transition-all

          duration-300

          hover:border-cyan-400/25

          hover:shadow-[0_0_20px_rgba(34,211,238,.12)]
          "
        >

          {/* Glow */}

          <div
            className="
            absolute

            -right-10

            -bottom-10

            h-24

            w-24

            rounded-full

            bg-cyan-500/10

            blur-[70px]
            "
          />

          <div className="relative flex items-center gap-3">

            <div
              className="
              h-3

              w-3

              rounded-full

              bg-emerald-400

              shadow-[0_0_10px_rgba(74,222,128,.9)]
              "
            />

            <div className="min-w-0">

              <p
                className="
                truncate

                text-sm

                font-semibold

                text-white
                "
              >
                Enterprise Workspace
              </p>

              <p
                className="
                mt-1

                truncate

                text-[11px]

                text-slate-400
                "
              >
                AI Security Assistant Connected
              </p>

            </div>

          </div>

        </div>

      </div>

    </aside>
  );
}