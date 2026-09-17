const ADK_API = "http://127.0.0.1:8001";

export const sendMessage = async (message, sessionId) => {
  const response = await fetch(`${ADK_API}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      appName: "finance_agent",
      userId: "user-1",
      sessionId,
      newMessage: {
        role: "user",
        parts: [
          {
            text: message,
          },
        ],
      },
      streaming: false,
    }),
  });

  if (!response.ok) {
    throw new Error(`ADK request failed: ${response.status}`);
  }

  return response.json();
};