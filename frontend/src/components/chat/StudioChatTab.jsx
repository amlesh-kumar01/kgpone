import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useToast } from "@/hooks/use-toast";
import { ChatInput } from './ChatInput';
import { ChatMessageList } from './ChatMessageList';
import api from '@/lib/api';
import { APP_CONFIG } from '@/config/appConfig';
import { Network, Database } from "lucide-react";

export const StudioChatTab = ({ studyUnitCode, studyUnitId, documentId }) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I am the **${APP_CONFIG.APP_NAME} Assistant**. How can I help you study this material?`,
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingIdx, setStreamingIdx] = useState(null);
  
  const { toast } = useToast();
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');

    const assistantIdx = messages.length + 1;

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: 'Assistant is thinking...', isThinking: true, metadata: null },
    ]);
    setIsLoading(true);
    setStreamingIdx(null);

    try {
      const baseURL = api.defaults.baseURL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('access_token');

      const body = {
        query: userMessage,
        use_citations: true,
        mode: "basic"
      };
      
      if (studyUnitCode) body.study_unit_code = studyUnitCode;
      if (studyUnitId) body.study_unit_id = studyUnitId;
      // Note: If documentId is present, we could potentially pass it, but ask_stream currently filters by study_unit.
      // So we rely on studyUnitId being passed down from the studio.

      const response = await fetch(`${baseURL}/api/v1/query/ask_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) throw new Error('Stream request failed');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let assistantContent = '';
      let buffer = '';

      setIsLoading(false);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.substring(6));
            if (data.type === 'chunk') {
              assistantContent += data.content;
              setStreamingIdx(assistantIdx);
              setMessages(prev => {
                const next = [...prev];
                const lastIdx = next.length - 1;
                const msg = { ...next[lastIdx] };
                if (msg.isThinking) {
                  msg.isThinking = false;
                  msg.content = '';
                }
                msg.content = assistantContent;
                next[lastIdx] = msg;
                return next;
              });
            } else if (data.type === 'metadata') {
              setStreamingIdx(null);
              setMessages(prev => {
                const next = [...prev];
                const lastIdx = next.length - 1;
                const msg = { ...next[lastIdx], metadata: data };
                next[lastIdx] = msg;
                return next;
              });
            }
          } catch {
            /* ignore parse errors */
          }
        }
      }
      setStreamingIdx(null);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        if (last.role === 'assistant' && last.content === '') {
          newMsgs[newMsgs.length - 1] = {
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            isError: true,
          };
        }
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
      setStreamingIdx(null);
    }
  };

  const handleCitationClick = useCallback(async (e, cit) => {
    e.preventDefault();
    if (cit.document_id && cit.document_id !== 'GRAPH') {
      try {
        const response = await api.get(`/api/v1/documents/${cit.document_id}/download`);
        if (response.data?.data) {
          window.open(response.data.data, '_blank');
        } else {
          toast({ title: 'Error', description: 'Could not generate download link', variant: 'destructive' });
        }
      } catch (err) {
        toast({ title: 'Error', description: 'Failed to download document', variant: 'destructive' });
      }
    } else if (cit.source_url) {
      window.open(cit.source_url, '_blank');
    }
  }, [toast]);

  const renderBackendBadge = useCallback((backend) => {
    if (backend === 'neo4j') return (
      <span key="neo4j" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-muted text-foreground border border-border">
        <Network className="w-3 h-3" /> Graph
      </span>
    );
    if (backend === 'qdrant') return (
      <span key="qdrant" className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-secondary/10 text-secondary border border-secondary/20 uppercase tracking-wider">
        <Database className="w-3 h-3" /> Vector
      </span>
    );
    return null;
  }, []);

  return (
    <div className="flex flex-col h-[600px] border border-border rounded-xl bg-card overflow-hidden">
      <div className="flex-1 overflow-hidden relative">
        <ChatMessageList
          scrollRef={scrollRef}
          messages={messages}
          isChatLoading={false}
          isLoading={isLoading}
          streamingIdx={streamingIdx}
          handleCitationClick={handleCitationClick}
          renderBackendBadge={renderBackendBadge}
        />
      </div>
      <div className="px-4 border-t border-border bg-card/50">
        <ChatInput
          input={input}
          setInput={setInput}
          handleSubmit={handleSubmit}
          isLoading={isLoading}
          selectedStudyUnitId={studyUnitId}
          analysisMode="basic"
        />
      </div>
    </div>
  );
};
