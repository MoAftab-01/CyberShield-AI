import { useState } from "react";
import { Send } from "lucide-react";

import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

interface Props {
    loading: boolean;
    onSend: (message: string) => void;
}

export default function ChatInput({

    loading,

    onSend,

}: Props) {

    const [message, setMessage] = useState("");

    const handleSend = () => {

        if (!message.trim()) return;

        onSend(message);

        setMessage("");
    };

    return (

        <div className="flex gap-4">

            <Input

                placeholder="Ask about CVEs, OWASP, Secure Coding..."

                value={message}

                onChange={(e) => setMessage(e.target.value)}

                onKeyDown={(e) => {

                    if (e.key === "Enter") {

                        handleSend();

                    }

                }}

            />

            <Button

                loading={loading}

                leftIcon={<Send size={18} />}

                onClick={handleSend}

            >

                Send

            </Button>

        </div>

    );

}