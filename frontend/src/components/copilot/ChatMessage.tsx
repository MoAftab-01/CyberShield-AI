import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Bot, User } from "lucide-react";

import SourceCard from "./SourceCard";

import { Source } from "@/types/copilot";

interface Props {

    role: "user" | "assistant";

    content: string;

    sources?: Source[];

}

export default function ChatMessage({

    role,

    content,

    sources = [],

}: Props) {

    const isUser = role === "user";

    return (

        <div
            className={`flex gap-4 ${
                isUser ? "justify-end" : "justify-start"
            }`}
        >

            {!isUser && (

                <div
                    className="
                    w-10
                    h-10
                    rounded-full
                    bg-blue-600
                    flex
                    items-center
                    justify-center
                    text-white
                    "
                >

                    <Bot size={20}/>

                </div>

            )}

            <div
                className={`
                    max-w-3xl
                    rounded-xl
                    px-5
                    py-4
                    shadow-sm

                    ${
                        isUser
                            ? "bg-blue-600 text-white"
                            : "bg-white border border-slate-200"
                    }
                `}
            >

                {isUser ? (

                    <p className="whitespace-pre-wrap">

                        {content}

                    </p>

                ) : (

                    <div
                        className="
                        prose
                        prose-slate
                        max-w-none
                        prose-headings:mb-3
                        prose-p:leading-7
                        prose-code:text-blue-600
                        "
                    >

                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                        >

                            {content}

                        </ReactMarkdown>

                    </div>

                )}

                {

                    !isUser &&

                    sources.length > 0 && (

                        <div className="mt-6">

                            <h3 className="font-semibold mb-3">

                                Sources

                            </h3>

                            <div className="space-y-3">

                                {

                                    sources.map(

                                        (

                                            source,

                                            index,

                                        ) => (

                                            <SourceCard

                                                key={index}

                                                source={source}

                                            />

                                        ),

                                    )

                                }

                            </div>

                        </div>

                    )

                }

            </div>

            {

                isUser && (

                    <div
                        className="
                        w-10
                        h-10
                        rounded-full
                        bg-slate-700
                        flex
                        items-center
                        justify-center
                        text-white
                        "
                    >

                        <User size={20}/>

                    </div>

                )

            }

        </div>

    );

}