import { useState } from 'react';

export const useChatStream = () => {
  const [messages, setMessages] = useState([]);
  
  const startStream = (workspaceId) => {
    // Implementation for SSE stream
  };

  return { messages, startStream };
};
