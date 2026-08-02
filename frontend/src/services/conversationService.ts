import api from "./api";

export interface ConversationItem {

  id: number;

  title: string;

  updated_at: string;

}

export interface ChatMessage {

  id: number;

  role: "user" | "assistant";

  content: string;

  created_at: string;

}

export interface ConversationResponse {

  id: number;

  title: string;

  messages: ChatMessage[];

}

export async function getConversations(): Promise<ConversationItem[]> {

  const response = await api.get("/conversations");

  return response.data;

}

export async function getConversation(
  conversationId: number,
): Promise<ConversationResponse> {

  const response = await api.get(
    `/conversations/${conversationId}`,
  );

  return response.data;

}

export async function deleteConversation(
  conversationId: number,
): Promise<void> {

  await api.delete(
    `/conversations/${conversationId}`,
  );

}