import { Shield, Settings } from "lucide-react";

import ConversationList from "./ConversationList";
import SearchConversation from "./SearchConversation";
import NewChatButton from "./NewChatButton";

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
        w-80
        h-full
        bg-slate-950
        border-r
        border-slate-800
        flex
        flex-col
      "
    >
      {/* Header */}

      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center gap-3 mb-6">
          <div
            className="
              w-12
              h-12
              rounded-xl
              bg-cyan-600
              flex
              items-center
              justify-center
            "
          >
            <Shield
              className="text-white"
              size={24}
            />
          </div>

          <div>
            <h2 className="text-white font-bold text-xl">
              CyberGPT
            </h2>

            <p className="text-slate-400 text-sm">
              Enterprise AI Security Assistant
            </p>
          </div>
        </div>

        <NewChatButton
          onClick={onNewChat}
        />
      </div>

      {/* Search */}

      <div className="p-4">
        <SearchConversation
          value={search}
          onChange={onSearch}
        />
      </div>

      {/* Conversation List */}

      <div
        className="
          flex-1
          overflow-y-auto
          px-4
          pb-4
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

      {/* Footer */}

      <div
        className="
          border-t
          border-slate-800
          p-5
        "
      >
        <button
          className="
            w-full
            flex
            items-center
            gap-3
            rounded-xl
            px-4
            py-3
            text-slate-300
            hover:bg-slate-900
            transition
          "
        >
          <Settings size={20} />

          Settings
        </button>
      </div>
    </aside>
  );
}