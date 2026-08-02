import {
  Trash2,
  MessageSquare,
} from "lucide-react";

import { ConversationItem as Conversation } from "../../services/conversationService";

interface Props {

  conversation: Conversation;

  active: boolean;

  onSelect: (id: number) => void;

  onDelete: (id: number) => void;

}

export default function ConversationItem({

  conversation,

  active,

  onSelect,

  onDelete,

}: Props) {

  const updated = new Date(
    conversation.updated_at,
  ).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (

    <div
      onClick={() => onSelect(conversation.id)}
      className={`
        group
        cursor-pointer
        rounded-xl
        p-4
        transition-all
        duration-200
        border

        ${
          active

            ? "bg-cyan-600 border-cyan-500 text-white"

            : "bg-slate-900 border-slate-800 hover:bg-slate-800 text-slate-200"

        }
      `}
    >

      <div className="flex items-start justify-between">

        <div className="flex gap-3 flex-1 min-w-0">

          <MessageSquare
            size={18}
            className={
              active
                ? "text-white mt-1"
                : "text-cyan-400 mt-1"
            }
          />

          <div className="min-w-0 flex-1">

            <h3
              className="
                font-medium
                truncate
              "
            >

              {conversation.title}

            </h3>

            <p
              className={`
                mt-1
                text-xs

                ${
                  active

                    ? "text-cyan-100"

                    : "text-slate-400"

                }
              `}
            >

              {updated}

            </p>

          </div>

        </div>

        <button

          onClick={(e) => {

            e.stopPropagation();

            onDelete(conversation.id);

          }}

          className="
            opacity-0
            group-hover:opacity-100
            transition
            p-1
            rounded-lg
            hover:bg-red-500/20
          "

        >

          <Trash2
            size={16}
            className="text-red-400"
          />

        </button>

      </div>

    </div>

  );

}