import React from 'react';
import { ChatMessage } from './ChatMessage';

export const ChatMessageList = ({
  scrollRef,
  messages,
  isChatLoading,
  isLoading,
  streamingIdx,
  handleCitationClick,
  renderBackendBadge
}) => {
  return (
    <div ref={scrollRef} className="h-full overflow-y-auto px-2 py-4 space-y-8 no-scrollbar scroll-smooth">
      {isChatLoading ? (
        <div className="flex flex-col gap-6 animate-pulse p-4">
          <div className="w-2/3 h-20 bg-muted rounded-2xl" />
          <div className="w-1/2 h-32 bg-muted rounded-2xl self-end" />
          <div className="w-3/4 h-40 bg-muted rounded-2xl" />
        </div>
      ) : (
        messages.map((msg, idx) => {
          if (msg.role === 'assistant' && msg.content === '' && !msg.metadata && !msg.isError) return null;
          return (
            <ChatMessage
              key={idx}
              index={idx}
              msg={msg}
              isStreaming={streamingIdx === idx}
              handleCitationClick={handleCitationClick}
              renderBackendBadge={renderBackendBadge}
            />
          );
        })
      )}
    </div>
  );
};
