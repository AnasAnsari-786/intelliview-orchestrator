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

  return {
    accept(message) {
      const messageId = message?.client_message_id;

      if (!messageId) return true;
      if (seenMessageIds.has(messageId)) return false;

      seenMessageIds.add(messageId);
      return true;
    },
    clear() {
      seenMessageIds.clear();
    },
  };
}
