import { useEffect, useRef, useState } from "react";
import ConversationSidebar from "@/components/copilot/ConversationSidebar";
import MessageList from "@/components/copilot/MessageList";
import TypingIndicator from "@/components/copilot/TypingIndicator";
import ChatFooter from "@/components/copilot/ChatFooter";
import ChatWelcome from "@/components/copilot/ChatWelcome";
import { toast } from "sonner";
import { askCopilot } from "@/services/copilotService";
import { getConversation, getConversations, deleteConversation } from "@/services/conversationService";
import type { ConversationItem } from "@/services/conversationService";
import type { Source } from "@/types/copilot";
import { uploadDocument, getUploadedDocuments, deleteUploadedDocument } from "@/services/uploadService";
import type { UploadedDocument } from "@/services/uploadService";
import "@/components/copilot/grounding.css";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  relatedSources?: Source[];
  grounding?: unknown;
  answerBasis?: "document" | "general_knowledge" | "tool" | "conversation";
}

export default function Copilot() {
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [search, setSearch] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedDocument[]>([]);
  const [error, setError] = useState("");
  const [failedQuestion, setFailedQuestion] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const lifecycle = useRef({ request: null as AbortController | null, version: 0 });
  const historyToggle = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let mounted = true;
    const state = lifecycle.current;
    Promise.all([getConversations(), getUploadedDocuments()])
      .then(([history, files]) => {
        if (mounted) { setConversations(history); setUploadedFiles(files); }
      })
      .catch(() => { if (mounted) setError("Unable to load chat history or uploaded files."); });
    return () => {
      mounted = false;
      state.request?.abort();
      state.request = null;
      state.version++;
    };
  }, []);

  function cancelRequest() {
    lifecycle.current.request?.abort();
    lifecycle.current.request = null;
    setLoading(false);
    setFailedQuestion(null);
  }

  function newChat() {
    cancelRequest();
    lifecycle.current.version++;
    setHistoryLoading(false);
    setConversationId(undefined);
    setMessages([]);
    setError("");
    setHistoryOpen(false);
  }

  async function selectConversation(id: number) {
    cancelRequest();
    const version = ++lifecycle.current.version;
    setHistoryLoading(true);
    setConversationId(id);
    setMessages([]);
    setError("");
    setHistoryOpen(false);
    try {
      const conversation = await getConversation(id);
      if (version === lifecycle.current.version) {
        // History is server-owned display text; do not fabricate persisted grounding.
        setMessages(conversation.messages.map(message => ({ role: message.role, content: message.content })));
      }
    } catch {
      if (version === lifecycle.current.version) setError("Unable to load this conversation.");
    } finally {
      if (version === lifecycle.current.version) setHistoryLoading(false);
    }
  }

  async function removeConversation(id: number) {
    const version = lifecycle.current.version;
    try {
      await deleteConversation(id);
      setConversations(prev => prev.filter(conversation => conversation.id !== id));
      if (version === lifecycle.current.version && conversationId === id) newChat();
    } catch { setError("Unable to delete this conversation."); }
  }

  async function handleSend(question: string, retry = false) {
    if (!question.trim() || lifecycle.current.request || historyLoading) return;
    const controller = new AbortController();
    lifecycle.current.request = controller;
    const version = lifecycle.current.version;
    setError("");
    setFailedQuestion(null);
    if (!retry) setMessages(prev => [...prev, { role: "user", content: question }]);
    setLoading(true);
    try {
      const response = await askCopilot({ question, conversation_id: conversationId }, controller.signal);
      if (controller.signal.aborted || lifecycle.current.request !== controller || version !== lifecycle.current.version) return;
      if (!conversationId && response.conversation_id !== null) {
        const id = response.conversation_id;
        setConversationId(id);
        setConversations(prev => prev.some(conversation => conversation.id === id) ? prev : [
          { id, title: "New conversation", updated_at: new Date().toISOString() }, ...prev,
        ]);
        // Retrieve the server's redacted title; never use a raw submitted password as a title.
        getConversations().then(items => {
          if (version === lifecycle.current.version) setConversations(items);
        }).catch(() => { /* A title refresh failure must not discard an answer. */ });
      }
      setMessages(prev => [...prev, {
        role: "assistant", content: response.grounding == null ? response.answer : "", sources: response.sources,
        relatedSources: response.related_sources, grounding: response.grounding, answerBasis: response.answer_basis,
      }]);
    } catch {
      if (!controller.signal.aborted && lifecycle.current.request === controller && version === lifecycle.current.version) {
        setError("Unable to send the message. A completed turn may already appear in history. Retry only if needed.");
        setFailedQuestion(question);
      }
    } finally {
      if (lifecycle.current.request === controller) {
        lifecycle.current.request = null;
        setLoading(false);
      }
    }
  }

  const filteredConversations = conversations.filter(conversation =>
    conversation.title.toLowerCase().includes(search.toLowerCase()));

  async function handleUpload(file: File) {
    try {
      await uploadDocument(file);
      setUploadedFiles(await getUploadedDocuments());
      toast.success("Document uploaded successfully!");
    } catch { toast.error("Upload failed."); }
  }

  async function handleDeleteDocument(filename: string) {
    try {
      await deleteUploadedDocument(filename);
      setUploadedFiles(prev => prev.filter(file => file.filename !== filename));
    } catch { setError("Unable to delete the uploaded document."); }
  }

  return (
  <div
    className="
    copilot-page
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

  <div id="copilot-conversations" className="copilot-conversations" data-open={historyOpen} onKeyDown={event => { if (event.key === "Escape") { setHistoryOpen(false); historyToggle.current?.focus(); } }}>
    <ConversationSidebar conversations={filteredConversations} loading={false} search={search}
      activeConversationId={conversationId ?? null} onSearch={setSearch}
      onSelectConversation={selectConversation} onDeleteConversation={removeConversation} onNewChat={newChat} />
  </div>



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


        

        <button type="button" ref={historyToggle} className="copilot-history-toggle" aria-controls="copilot-conversations"
          onKeyDown={event => { if (event.key === "Escape") setHistoryOpen(false); }}
          aria-expanded={historyOpen} onClick={() => setHistoryOpen(value => !value)}>Chat history</button>
        <div className="copilot-request-status" role="status" aria-live="polite">
          {historyLoading && <p>Loading conversation...</p>}
          {loading && <button type="button" onClick={() => { cancelRequest(); setError("Request cancelled. A completed turn may appear when history is reloaded."); }}>Cancel response</button>}
          {error && <p>{error}</p>}
          {failedQuestion && <button type="button" onClick={() => handleSend(failedQuestion, true)}>Retry message</button>}
        </div>
        {/* Scrollable Chat */}

        <div
  className="
  relative

  flex-1
  copilot-chat-scroll
  min-h-0

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
  loading={loading || historyLoading}
  uploadedFiles={uploadedFiles}
  onSend={handleSend}
  onUpload={handleUpload}
  onDeleteDocument={handleDeleteDocument}
/>
      </div>
    </div>
  );
}