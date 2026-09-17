import { useState } from "react";
import { sendMessage } from "./api";
import "./App.css";

function getDecision(text) {
  if (typeof text !== "string") {
    return null;
  }

  const normalizedText = text.toUpperCase();

  if (normalizedText.includes("HUMAN_APPROVAL")) {
    return "HUMAN_APPROVAL";
  }

  if (/\bBLOCK(?:ED)?\b/.test(normalizedText)) {
    return "BLOCK";
  }

  if (/\bALLOW\b/.test(normalizedText)) {
    return "ALLOW";
  }

  return null;
}

function getDecisionLabel(decision) {
  switch (decision) {
    case "ALLOW":
      return "Refund Approved";

    case "HUMAN_APPROVAL":
      return "Human Approval Required";

    case "BLOCK":
      return "Refund Blocked";

    default:
      return null;
  }
}

function cleanMarkdown(text) {
  return text
    .replace(/\*\*/g, "")
    .replace(/\*/g, "")
    .trim();
}

function renderAgentResponse(text) {
  if (typeof text !== "string") {
    return null;
  }

  const lines = text.split(/\r?\n/);

  return lines.map((line, index) => {
    const cleanedLine = cleanMarkdown(line);

    if (!cleanedLine) {
      return (
        <div
          key={`spacer-${index}`}
          style={{ height: "8px" }}
        />
      );
    }

    const bulletMatch = cleanedLine.match(/^-\s+(.*)$/);
    const content = bulletMatch ? bulletMatch[1] : cleanedLine;

    const labelMatch = content.match(/^([^:]+):\s*(.*)$/);

    if (labelMatch) {
      const label = labelMatch[1].trim();
      const value = labelMatch[2].trim();

      return (
        <div key={`line-${index}`}>
          {bulletMatch && "• "}
          <strong>{label}:</strong>{" "}
          {value}
        </div>
      );
    }

    return (
      <div key={`line-${index}`}>
        {bulletMatch && "• "}
        {content}
      </div>
    );
  });
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId] = useState(() => crypto.randomUUID());
  const [loading, setLoading] = useState(false);

  const extractAgentResponse = (events) => {
    if (!Array.isArray(events)) {
      return "The agent returned an unexpected response.";
    }

    const modelEvents = events.filter(
      (event) =>
        event?.content?.role === "model" &&
        Array.isArray(event.content.parts)
    );

    for (let i = modelEvents.length - 1; i >= 0; i--) {
      const textParts = modelEvents[i].content.parts
        .filter((part) => typeof part.text === "string")
        .map((part) => part.text.trim())
        .filter(Boolean);

      if (textParts.length > 0) {
        return textParts.join("\n");
      }
    }

    return "The agent completed the request but returned no text response.";
  };

  const handleSend = async (event) => {
    event.preventDefault();

    const message = input.trim();

    if (!message || loading) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        role: "user",
        text: message,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const events = await sendMessage(message, sessionId);

      const agentResponse = extractAgentResponse(events);
      const decision = getDecision(agentResponse);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: agentResponse,
          decision,
          error: false,
        },
      ]);
    } catch (error) {
      console.error("Agent request failed:", error);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: "Unable to reach the Finance Agent. Please try again.",
          decision: null,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>AgentOps Finance Assistant</h1>
        <p>Ask the Finance Agent about refund requests.</p>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>How can I help?</h2>
              <p>
                Ask about a refund request using a customer ID, order ID, and
                refund amount.
              </p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`message ${message.role}`}
              >
                <div className="message-label">
                  {message.role === "user" ? "You" : "Finance Agent"}
                </div>

                {message.role === "assistant" && message.decision && (
                  <div
                    className={`decision-card decision-${message.decision.toLowerCase()}`}
                  >
                    <div className="decision-label">
                      Decision
                    </div>

                    <div className="decision-value">
                      {message.decision}
                    </div>

                    <div className="decision-description">
                      {getDecisionLabel(message.decision)}
                    </div>
                  </div>
                )}

                <div
                  className={`message-content ${
                    message.error ? "error-message" : ""
                  }`}
                >
                  {message.error
                    ? message.text
                    : renderAgentResponse(message.text)}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="message assistant">
              <div className="message-label">
                Finance Agent
              </div>

              <div className="message-content">
                Thinking...
              </div>
            </div>
          )}
        </div>

        <form className="chat-form" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Ask about a refund..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={loading}
          />

          <button
            type="submit"
            disabled={loading || !input.trim()}
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;