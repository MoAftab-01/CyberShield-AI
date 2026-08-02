import { useEffect, useState } from "react";

import {
  ConversationItem,
  getConversations,
  deleteConversation,
} from "../services/conversationService";

export function useConversations() {

  const [conversations, setConversations] =
    useState<ConversationItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  async function refresh() {

    try {

      setLoading(true);

      const data =
        await getConversations();

      setConversations(data);

      setError("");

    }

    catch {

      setError(
        "Unable to load conversations."
      );

    }

    finally {

      setLoading(false);

    }

  }

  async function removeConversation(
    id: number,
  ) {

    try {

      await deleteConversation(id);

      setConversations(

        conversations.filter(

          conversation => conversation.id !== id,

        ),

      );

    }

    catch {

      alert(
        "Unable to delete conversation.",
      );

    }

  }

  useEffect(() => {

    refresh();

  }, []);

  return {

    conversations,

    loading,

    error,

    refresh,

    removeConversation,

  };

}