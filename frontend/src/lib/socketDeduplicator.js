export function attachClientMessageId(payload, sequence) {
  if (
    !payload ||
    typeof payload !== "object" ||
    payload.type === "auth" ||
    payload.client_message_id
  ) {
    return payload;
  }

  return {
    ...payload,
    client_message_id: `client-${sequence}`,
  };
}

export function createMessageDeduplicator() {
  const seenMessageIds = new Set();
  let sequence = 0;
  const pendingMessages = new Map();

  return {
    prepare(payload) {
      if (
        !payload ||
        typeof payload !== "object" ||
        payload.type === "auth"
      ) {
        return payload;
      }

      const message = payload.client_message_id
        ? payload
        : attachClientMessageId(payload, ++sequence);

      pendingMessages.set(message.client_message_id, message);
      return message;
    },
    pending() {
      return [...pendingMessages.values()];
    },
    acknowledge(messageId) {
      if (messageId) pendingMessages.delete(messageId);
    },
    accept(message) {
      const messageId = message?.client_message_id;

      if (!messageId) return true;
      if (seenMessageIds.has(messageId)) return false;

      seenMessageIds.add(messageId);
      return true;
    },
    clear() {
      seenMessageIds.clear();
      pendingMessages.clear();
    },
  };
}
