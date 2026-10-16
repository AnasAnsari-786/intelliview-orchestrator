import { describe, expect, it } from "vitest";
import {
  attachClientMessageId,
  createMessageDeduplicator,
} from "../socketDeduplicator";

describe("socket deduplication helpers", () => {
  it("attaches a deterministic client message ID to outbound payloads", () => {
    expect(
      attachClientMessageId({ type: "answer_chunk", text: "hello" }, 7),
    ).toEqual({
      type: "answer_chunk",
      text: "hello",
      client_message_id: "client-7",
    });
  });

  it("buffers identified outbound messages for reconnect replay", () => {
    const deduplicator = createMessageDeduplicator();
    const message = deduplicator.prepare({
      type: "answer_chunk",
      text: "hello",
    });

    expect(message.client_message_id).toBe("client-1");
    expect(deduplicator.pending()).toEqual([message]);
  });

  it("removes acknowledged messages from the reconnect buffer", () => {
    const deduplicator = createMessageDeduplicator();
    const message = deduplicator.prepare({ type: "answer_chunk" });

    deduplicator.acknowledge(message.client_message_id);

    expect(deduplicator.pending()).toEqual([]);
  });

  it("preserves an existing client message ID", () => {
    const payload = {
      type: "answer_chunk",
      client_message_id: "answer-1",
    };

    expect(attachClientMessageId(payload, 7)).toBe(payload);
  });

  it("accepts an identified message once and rejects retransmissions", () => {
    const deduplicator = createMessageDeduplicator();

    expect(deduplicator.accept({ client_message_id: "answer-1" })).toBe(true);
    expect(deduplicator.accept({ client_message_id: "answer-1" })).toBe(false);
    expect(deduplicator.accept({ client_message_id: "answer-2" })).toBe(true);
  });

  it("accepts messages without IDs for backward compatibility", () => {
    const deduplicator = createMessageDeduplicator();

    expect(deduplicator.accept({ type: "metric" })).toBe(true);
    expect(deduplicator.accept({ type: "metric" })).toBe(true);
  });
});
