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
  const [renameError, setRenameError] = useState(false);
  const [title, setTitle] = useState(conversation.title);

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

    setRenameError(false);
    try {

      await renameConversation(
        conversation.id,
        newTitle,
      );

      conversation.title = newTitle;

      setEditing(false);

    }

    catch {

      setRenameError(true);

    }

  };

  return (

    <div

      onClick={() => {

        if (!editing) {

          onSelect(conversation.id);

        }

      }}

      title={conversation.title}

      className={`
      group

      relative

      cursor-pointer

      overflow-hidden

      rounded-xl

      border

      transition-all

      duration-300

      ${
        active

          ? `
          border-cyan-400/50

          bg-gradient-to-r

          from-cyan-500/20

          via-cyan-500/10

          to-transparent

          shadow-[0_0_25px_rgba(34,211,238,0.22)]
          `

          : `
          border-slate-800

bg-[#081423]/70

hover:border-cyan-500/25

hover:bg-[#0B182A]

hover:shadow-[0_0_18px_rgba(34,211,238,0.08)]
          `
      }

      px-3

      py-2.5
      `}
    >

      {renameError && <p role="alert" className="text-sm text-amber-200">Unable to rename conversation.</p>}
      {active && (

        <div
          className="
          absolute

          left-0

          top-2

          bottom-2

          w-1

          rounded-r-full

          bg-cyan-400

          shadow-[0_0_12px_rgba(34,211,238,1)]
          "
        />

      )}

      <div className="flex items-center justify-between">

        <div className="flex items-center gap-3 flex-1 min-w-0">

          <div
            className={`
            flex

            h-8
            w-8

            flex-shrink-0

            items-center
            justify-center

            rounded-lg

            ${
              active

                ? "bg-cyan-500/20"

                : "bg-slate-800"
            }
            `}
          >

            <MessageSquare

              size={15}

              className={
                active

                  ? "text-cyan-300"

                  : "text-slate-400"
              }

            />

          </div>

          <div className="min-w-0 flex-1">

            {

              editing

                ? (

                  <input

                    aria-label="Conversation title"
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

                    rounded-lg

                    bg-slate-800

                    px-2

                    py-1

                    text-sm

                    text-white

                    outline-none
                    "

                  />

                )

                : (

                  <h3
                    className="
                    truncate

                    text-sm

                    font-medium

                    text-white
                    "
                  >

                    <button type="button" className="block w-full truncate text-left" aria-current={active ? "true" : undefined}
                      onClick={event => { event.stopPropagation(); onSelect(conversation.id); }}>{conversation.title}</button>

                  </h3>

                )

            }

            <p
              className={`
              mt-0.5

              text-[11px]

              ${
                active

                  ? "text-cyan-300"

                  : "text-slate-500"
              }
              `}
            >

              {updated}

            </p>

          </div>

        </div>

        <div
          className="
          ml-2

          flex

          items-center

          gap-1

          opacity-0

          transition-opacity

          group-hover:opacity-100
          group-focus-within:opacity-100
          "
        >

          {

            editing

              ? (

                <>

                  <button
                  aria-label="Save conversation title"

                    onClick={(e) => {

                      e.stopPropagation();

                      saveRename();

                    }}

                    className="
                    rounded-lg

                    p-1.5

                    hover:bg-emerald-500/20
                    "

                  >

                    <Check
                      size={14}
                      className="text-emerald-400"
                    />

                  </button>

                  <button
                  aria-label="Cancel rename"

                    onClick={(e) => {

                      e.stopPropagation();

                      setTitle(conversation.title);

                      setEditing(false);

                    }}

                    className="
                    rounded-lg

                    p-1.5

                    hover:bg-red-500/20
                    "

                  >

                    <X
                      size={14}
                      className="text-red-400"
                    />

                  </button>

                </>

              )

              : (

                <>

                  <button
                  aria-label="Rename conversation"

                    onClick={(e) => {

                      e.stopPropagation();

                      setEditing(true);

                    }}

                    className="
                    rounded-lg

                    p-1.5

                    hover:bg-cyan-500/20
                    "

                  >

                    <Edit2
                      size={14}
                      className="text-cyan-400"
                    />

                  </button>

                  <button
                  aria-label="Delete conversation"

                    onClick={(e) => {

                      e.stopPropagation();

                      onDelete(conversation.id);

                    }}

                    className="
                    rounded-lg

                    p-1.5

                    hover:bg-red-500/20
                    "

                  >

                    <Trash2
                      size={14}
                      className="text-red-400"
                    />

                  </button>

                </>

              )

          }

        </div>

      </div>
      
{
  !active && (
    <div
      className="
      absolute

      bottom-0

      left-4

      right-4

      h-px

      bg-gradient-to-r

      from-transparent

      via-slate-700/70

      to-transparent
      "
    />
  )
}
    </div>

  );

}