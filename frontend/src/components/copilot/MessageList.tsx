import ChatMessage from "./ChatMessage";

import { Source } from "@/types/copilot";

interface Message {

    role: "user" | "assistant";

    content: string;

    sources?: Source[];
    relatedSources?: Source[];
    grounding?: unknown;

}

interface Props {

    messages: Message[];

}

export default function MessageList({

    messages,

}: Props) {

    return (

        <div className="mx-auto max-w-5xl space-y-10">

            {

                messages.map(

                    (

                        message,

                        index,

                    ) => (

                        <ChatMessage

                            key={index}

                            role={message.role}

                            content={message.content}

                            sources={message.sources}

                            relatedSources={message.relatedSources}
                            grounding={message.grounding}

                        />

                    ),

                )

            }

        </div>

    );

}