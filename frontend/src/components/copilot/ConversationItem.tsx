import { useState } from "react";

import {
  Check,
  Edit2,
  MessageSquare,
  Trash2,
  X,
} from "lucide-react";

import {
  ConversationItem as Conversation,
  renameConversation,
} from "../../services/conversationService";

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
  const [editing, setEditing] = useState(false);

  const [title, setTitle] = useState(
    conversation.title,
  );

  const updated = new Date(
    conversation.updated_at,
  ).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const saveRename = async () => {
    const newTitle = title.trim();

    if (!newTitle) {
      setTitle(conversation.title);
      setEditing(false);
      return;
    }

    try {
      await renameConversation(
        conversation.id,
        newTitle,
      );

      conversation.title = newTitle;

      setEditing(false);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div
      onClick={() => {
        if (!editing) {
          onSelect(conversation.id);
        }
      }}
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

          <div className="flex-1 min-w-0">

            {editing ? (
              <input
                autoFocus
                value={title}
                onChange={(e) =>
                  setTitle(e.target.value)
                }
                onClick={(e) =>
                  e.stopPropagation()
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    saveRename();
                  }

                  if (e.key === "Escape") {
                    setTitle(
                      conversation.title,
                    );
                    setEditing(false);
                  }
                }}
                className="
                  w-full
                  rounded-md
                  px-2
                  py-1
                  text-black
                  outline-none
                "
              />
            ) : (
              <h3 className="font-medium truncate">
                {conversation.title}
              </h3>
            )}

            <p
              className={`mt-1 text-xs ${
                active
                  ? "text-cyan-100"
                  : "text-slate-400"
              }`}
            >
              {updated}
            </p>

          </div>

        </div>

        <div className="flex gap-1">

          {editing ? (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  saveRename();
                }}
                className="
                  p-1
                  rounded-lg
                  hover:bg-green-500/20
                "
              >
                <Check
                  size={16}
                  className="text-green-400"
                />
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setTitle(
                    conversation.title,
                  );
                  setEditing(false);
                }}
                className="
                  p-1
                  rounded-lg
                  hover:bg-red-500/20
                "
              >
                <X
                  size={16}
                  className="text-red-400"
                />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setEditing(true);
                }}
                className="
                  opacity-0
                  group-hover:opacity-100
                  transition
                  p-1
                  rounded-lg
                  hover:bg-cyan-500/20
                "
              >
                <Edit2
                  size={16}
                  className="text-cyan-400"
                />
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(
                    conversation.id,
                  );
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
            </>
          )}

        </div>

      </div>
    </div>
  );
}