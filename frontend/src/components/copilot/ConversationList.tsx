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

      <div className="space-y-2">

        {

          Array.from({ length: 6 }).map((_, index) => (

            <div
              key={index}
              className="
              h-24
              rounded-2xl
              bg-slate-800/70
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
        rounded-3xl

        border

        border-slate-800

        bg-slate-900

        p-8

        text-center

        shadow-lg
        "
      >

        <div className="text-5xl mb-4">

          🤖

        </div>

        <h3
          className="
          text-lg
          font-semibold
          text-white
          "
        >

          No Conversations Yet

        </h3>

        <p
          className="
          mt-3
          text-slate-400
          leading-7
          "
        >

          Start a new CyberGPT conversation
          to begin analyzing threats,
          documents and security data.

        </p>

      </div>

    );

  }

  return (

    <div className="space-y-4">

      {

        conversations.map(

          (conversation) => (

            <ConversationItem

              key={conversation.id}

              conversation={conversation}

              active={

                activeConversationId ===

                conversation.id

              }

              onSelect={onSelect}

              onDelete={onDelete}

            />

          ),

        )

      }

    </div>

  );

}