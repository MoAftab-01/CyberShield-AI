import ChatMessage from "./ChatMessage";

import { Source } from "@/types/copilot";

interface Message {

    role: "user" | "assistant";

    content: string;

    sources?: Source[];

}

interface Props {

    messages: Message[];

}

export default function MessageList({

    messages,

}: Props) {

    return (

        <div className="space-y-6">

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

                        />

                    ),

                )

            }

        </div>

    );

}