import {
    MessageSquare,
    Plus,
} from "lucide-react";

import Button from "@/components/ui/Button";

interface Conversation {

    id: number;

    title: string;

}

interface Props {

    conversations: Conversation[];

    selectedConversation?: number;

    onSelect: (id: number) => void;

    onNewChat: () => void;

}

export default function ConversationSidebar({

    conversations,

    selectedConversation,

    onSelect,

    onNewChat,

}: Props) {

    return (

        <div
            className="
            w-80
            h-full
            bg-white
            border-r
            border-slate-200
            flex
            flex-col
            "
        >

            <div className="p-5 border-b border-slate-200">

                <Button

                    className="w-full"

                    leftIcon={<Plus size={18}/>}

                    onClick={onNewChat}

                >

                    New Conversation

                </Button>

            </div>

            <div className="flex-1 overflow-y-auto">

                {

                    conversations.length === 0 ? (

                        <div className="p-6 text-center text-slate-500">

                            No conversations yet.

                        </div>

                    ) : (

                        conversations.map(

                            (

                                conversation,

                            ) => (

                                <button

                                    key={conversation.id}

                                    onClick={() =>

                                        onSelect(

                                            conversation.id,

                                        )

                                    }

                                    className={`

                                        w-full

                                        flex

                                        items-center

                                        gap-3

                                        px-5

                                        py-4

                                        text-left

                                        transition

                                        hover:bg-slate-100

                                        ${
                                            selectedConversation === conversation.id

                                                ? "bg-blue-50"

                                                : ""

                                        }

                                    `}

                                >

                                    <MessageSquare

                                        size={18}

                                    />

                                    <span
                                        className="truncate"
                                    >

                                        {

                                            conversation.title

                                        }

                                    </span>

                                </button>

                            ),

                        )

                    )

                }

            </div>

        </div>

    );

}