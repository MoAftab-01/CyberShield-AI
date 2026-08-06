import { useEffect, useState } from "react";
// import {
//   PanelLeftClose,
//   PanelLeftOpen,
// } from "lucide-react";

// import ChatInput from "@/components/copilot/ChatInput";
import ConversationSidebar from "@/components/copilot/ConversationSidebar";
import MessageList from "@/components/copilot/MessageList";
import TypingIndicator from "@/components/copilot/TypingIndicator";

import ChatFooter from "@/components/copilot/ChatFooter";
import ChatWelcome from "@/components/copilot/ChatWelcome";

import { toast } from "sonner";

import { askCopilot } from "@/services/copilotService";
import {
  ConversationItem,
  getConversation,
  getConversations,
  deleteConversation,
} from "@/services/conversationService";


import { Source } from "@/types/copilot";

// import UploadButton from "@/components/upload/UploadButton";

import {
  uploadDocument,
  getUploadedDocuments,
  deleteUploadedDocument,
  UploadedDocument,
} from "@/services/uploadService";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}



export default function Copilot() {
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [conversations, setConversations] =useState<ConversationItem[]>([]);
    const [search, setSearch] = useState("");
    const [uploadedFiles, setUploadedFiles] = useState<UploadedDocument[]>([]);

  useEffect(() => {
  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
      const files =
        await getUploadedDocuments();

    setUploadedFiles(files);
    } catch (error) {
      console.error(error);
    }
  };

  loadConversations();
}, []);  

  const handleSend = async (question: string) => {
    if (!question.trim()) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: question,
      },
    ]);

    setLoading(true);

    try {
      const response = await askCopilot({
        question,
        conversation_id: conversationId,
      });

      if (!conversationId) {
        setConversationId(response.conversation_id);

        setConversations((prev) => {
  const exists = prev.some(
    (conversation) =>
      conversation.id === response.conversation_id
  );

  if (exists) return prev;

  return [
    {
      id: response.conversation_id,
      title: question,
      updated_at: new Date().toISOString(),
    },
    ...prev,
  ];
});
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };
    const filteredConversations = conversations.filter((conversation) =>
  conversation.title
    .toLowerCase()
    .includes(search.toLowerCase())
    );

const handleUpload = async (
  file: File,
) => {
  try {
    await uploadDocument(file);

    const files =
      await getUploadedDocuments();

    setUploadedFiles(files);

    toast.success(
      "Document uploaded successfully!"
    );

  } catch (error) {

    console.error(error);

    toast.error(
      "Upload failed."
    );
  }
};

const handleDeleteDocument = async (
  filename: string,
) => {

  try {

    await deleteUploadedDocument(
      filename,
    );

    setUploadedFiles((prev) =>
      prev.filter(
        (file) =>
          file.filename !== filename,
      ),
    );

  }

  catch (error) {

    console.error(error);

  }

};


  return (
  <div
    className="
    relative

    flex

    h-full

    overflow-hidden

    rounded-3xl

    border
    border-cyan-500/15

    bg-slate-900/20

    backdrop-blur-2xl

    shadow-[0_0_50px_rgba(34,211,238,0.08)]
    "
  >
      {/* Galaxy Glow */}

<div
  className="
  absolute
  inset-0

  overflow-hidden

  pointer-events-none
  "
>

  <div
    className="
    absolute

    top-[-150px]
    right-[20%]

    h-[520px]
    w-[520px]

    rounded-full

    bg-cyan-500/8

    blur-[190px]
    "
  />

  <div
    className="
    absolute

    bottom-[-180px]
    left-[-100px]

    h-[450px]
    w-[450px]

    rounded-full

    bg-blue-500/10

    blur-[180px]
    "
  />

</div>

  <ConversationSidebar
    conversations={filteredConversations}
    loading={false}
    search={search}
    activeConversationId={conversationId ?? null}
    onSearch={setSearch}

    onSelectConversation={async (id) => {
      try {
        setConversationId(id);

        const conversation =
          await getConversation(id);

        setMessages(
          conversation.messages.map((message) => ({
            role: message.role,
            content: message.content,
          }))
        );
      } catch (error) {
        console.error(error);
      }
    }}

    onDeleteConversation={async (id) => {
      try {
        await deleteConversation(id);

        setConversations((prev) =>
          prev.filter(
            (conversation) =>
              conversation.id !== id
          )
        );

        if (conversationId === id) {
          setConversationId(undefined);
          setMessages([]);
        }
      } catch (error) {
        console.error(error);
      }
    }}

    onNewChat={() => {
      setConversationId(undefined);
      setMessages([]);
    }}
  />



      <div
  className="
  relative

  z-10

  flex

  min-w-0

  flex-1

  flex-col

  overflow-hidden
  "
>
        {/* Header */}


        

        {/* Scrollable Chat */}

        <div
  className="
  relative

  flex-1

  overflow-y-auto

  px-6

  py-4

  bg-transparent
  "
>
          {messages.length === 0 ? (
            <ChatWelcome
  onSuggestion={handleSend}
/>
          ) : (
            <>
              <MessageList messages={messages} />

              {loading && (
                <div className="mt-6">
                  <TypingIndicator />
                </div>
              )}
            </>
          )}
        </div>

        {/* Fixed Footer */}

        <ChatFooter
  loading={loading}
  uploadedFiles={uploadedFiles}
  onSend={handleSend}
  onUpload={handleUpload}
  onDeleteDocument={handleDeleteDocument}
/>
      </div>
    </div>
  );
}