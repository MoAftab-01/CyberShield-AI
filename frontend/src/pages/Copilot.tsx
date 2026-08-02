import { useState } from "react";

import ChatInput from "@/components/copilot/ChatInput";
import ConversationSidebar from "@/components/copilot/ConversationSidebar";
import MessageList from "@/components/copilot/MessageList";
import TypingIndicator from "@/components/copilot/TypingIndicator";

import { toast } from "sonner";

import { askCopilot } from "@/services/copilotService";
import {
  ConversationItem,
  getConversation,
  getConversations,
  deleteConversation,
} from "@/services/conversationService";

import { useEffect } from "react";


import { Source } from "@/types/copilot";

import UploadButton from "@/components/upload/UploadButton";

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
    <div className="flex h-full overflow-hidden bg-slate-100">
      <ConversationSidebar
  conversations={filteredConversations}
  loading={false}
  search={search}
  activeConversationId={conversationId ?? null}
  onSearch={setSearch}

  onSelectConversation={async (id) => {
  try {
    setConversationId(id);

    const conversation = await getConversation(id);

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
      prev.filter((conversation) => conversation.id !== id)
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

      <div className="flex flex-1 flex-col min-h-0">
        {/* Header */}

        <header className="bg-white border-b px-8 py-5 shadow-sm flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-cyan-600 flex items-center justify-center text-2xl text-white shadow-lg">
              🛡️
            </div>

            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                CyberGPT
              </h1>

              <p className="text-slate-500">
                Enterprise AI Security Assistant
              </p>
            </div>
          </div>
        </header>
        

        {/* Scrollable Chat */}

        <div className="flex-1 overflow-y-auto px-8 py-8">
          {messages.length === 0 ? (
            <div className="max-w-4xl mx-auto mt-12">
              <h2 className="text-4xl font-bold text-slate-800 mb-4">
                Welcome to CyberGPT 👋
              </h2>

              <p className="text-slate-500 text-lg mb-10">
                Your enterprise AI assistant for cybersecurity.
              </p>

              <div className="grid grid-cols-2 gap-5">
                <button
                  onClick={() =>
                    handleSend("Analyze CVE-2024-4577")
                  }
                  className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
                >
                  🛡 Analyze CVE-2024-4577
                </button>

                <button
                  onClick={() =>
                    handleSend("Explain SQL Injection")
                  }
                  className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
                >
                  🔐 Explain SQL Injection
                </button>

                <button
                  onClick={() =>
                    handleSend("Explain OWASP Top 10")
                  }
                  className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
                >
                  📚 Explain OWASP Top 10
                </button>

                <button
                  onClick={() =>
                    handleSend("Explain MITRE ATT&CK")
                  }
                  className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
                >
                  🎯 Explain MITRE ATT&CK
                </button>
              </div>
            </div>
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

        <footer className="bg-white border-t p-5 flex-shrink-0">

  <div className="max-w-5xl mx-auto">

    {uploadedFiles.length > 0 && (

      <div className="flex flex-wrap gap-2 mb-3">

        {uploadedFiles.map((file) => (

          <div
            key={file.filename}
            className="
              flex
              items-center
              gap-2
              bg-slate-100
              border
              rounded-full
              px-3
              py-1
              text-sm
            "
          >

            📄

            <span className="max-w-[220px] truncate">
              {file.filename}
            </span>

            <button
              onClick={() =>
                handleDeleteDocument(
                  file.filename,
                )
              }
              className="
                text-red-500
                hover:text-red-700
              "
            >
              ✕
            </button>

          </div>

        ))}

      </div>

    )}

    <div className="flex items-center gap-3">

      <UploadButton
        onUpload={handleUpload}
      />

      <div className="flex-1">

        <ChatInput
          loading={loading}
          onSend={handleSend}
        />

      </div>

    </div>

  </div>

</footer>
      </div>
    </div>
  );
}