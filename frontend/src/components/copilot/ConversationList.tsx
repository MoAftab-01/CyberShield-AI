import ConversationItem from "./ConversationItem";

import { ConversationItem as Conversation } from "../../services/conversationService";

interface Props {

  conversations: Conversation[];

  loading: boolean;

  activeConversationId: number | null;

  onSelect: (id: number) => void;

  onDelete: (id: number) => void;

}

export default function ConversationList({

  conversations,

  loading,

  activeConversationId,

  onSelect,

  onDelete,

}: Props) {

  if (loading) {

    return (

      <div className="space-y-3">

        {

          Array.from({ length: 6 }).map((_, index) => (

            <div
              key={index}
              className="
                h-20
                rounded-xl
                bg-slate-800
                animate-pulse
              "
            />

          ))

        }

      </div>

    );

  }

  if (conversations.length === 0) {

    return (

      <div
        className="
          rounded-xl
          border
          border-slate-700
          bg-slate-900
          p-6
          text-center
        "
      >

        <p className="text-slate-400">

          No conversations yet.

        </p>

        <p className="text-slate-500 text-sm mt-2">

          Start a new CyberGPT conversation.

        </p>

      </div>

    );

  }

  return (

    <div className="space-y-3">

      {

        conversations.map(

          (conversation) => (

            <ConversationItem

              key={conversation.id}

              conversation={conversation}

              active={activeConversationId === conversation.id}

              onSelect={onSelect}

              onDelete={onDelete}

            />

          ),

        )

      }

    </div>

  );

}