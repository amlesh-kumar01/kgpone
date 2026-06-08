import { useState } from 'react';

export const useChatStream = () => {
  const [messages] = useState([]);
  
  const startStream = () => {
    // Implementation for SSE stream
  };

  return { messages, startStream };
};
