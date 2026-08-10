import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Share2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from '../lib/api';
import { useAcademic } from '../context/AcademicContext';
import { ChatSidebar } from '../components/chat/ChatSidebar';
import { ChatSettingsSheet } from '../components/chat/ChatSettingsSheet';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatMessageList } from '../components/chat/ChatMessageList';
import { MemoryViewerDialog } from '../components/chat/MemoryViewerDialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileText, Sigma, ImageIcon, Table2, Settings, MessageSquare, Zap, Brain, Globe, Database, Network } from "lucide-react";

/* ── Inline styles injected once ──────────────────────────────────────── */
const GLOBAL_STYLES = `
@keyframes kgp-cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
@keyframes kgp-slide-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes kgp-dot-bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}
.kgp-msg-enter { animation: kgp-slide-up 0.35s cubic-bezier(0.22,1,0.36,1) both; }
.kgp-cursor { display: inline-block; width: 2px; height: 1em; background: currentColor;
  margin-left: 2px; vertical-align: text-bottom;
  animation: kgp-cursor-blink 0.8s step-start infinite; }
.kgp-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  background: currentColor; margin: 0 2px; }
.kgp-dot:nth-child(1) { animation: kgp-dot-bounce 1.2s ease-in-out infinite 0s; }
.kgp-dot:nth-child(2) { animation: kgp-dot-bounce 1.2s ease-in-out infinite 0.2s; }
.kgp-dot:nth-child(3) { animation: kgp-dot-bounce 1.2s ease-in-out infinite 0.4s; }
@keyframes kgp-byok-open {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes kgp-shimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}
.kgp-byok-open { animation: kgp-byok-open 0.28s cubic-bezier(0.22,1,0.36,1) both; }
.kgp-advanced-shimmer {
  background: linear-gradient(90deg, #7c3aed, #a855f7, #ec4899, #7c3aed);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: kgp-shimmer 3s linear infinite;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('kgp-chat-styles')) {
  const s = document.createElement('style');
  s.id = 'kgp-chat-styles';
  s.textContent = GLOBAL_STYLES;
  document.head.appendChild(s);
}

/* ── Chunk-type config ────────────────────────────────────────────────── */
const CHUNK_TYPE_CONFIG = {
  equation: {
    icon: Sigma,
    label: 'EQ',
    color: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
    border: 'border-violet-200 dark:border-violet-800',
  },
  figure: {
    icon: ImageIcon,
    label: 'FIG',
    color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  table_row: {
    icon: Table2,
    label: 'TBL',
    color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
  },
  text: {
    icon: FileText,
    label: 'TXT',
    color: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
    border: 'border-slate-200 dark:border-slate-700',
  },
};

/* ── Main Chat component ───────────────────────────────────────────────── */
const Chat = () => {
  const navigate = useNavigate();
  const { departments, courses: allCourses } = useAcademic();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am the **KnowledgeOS Assistant**. Ask me about your curriculum, prerequisites, formulas, or any concept from your course materials.',
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingIdx, setStreamingIdx] = useState(null);
  const [useCitations, setUseCitations] = useState(true);
  const [analysisMode, setAnalysisMode] = useState('basic');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const [selectedDeptId, setSelectedDeptId] = useState('');
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [selectedOfferingId, setSelectedOfferingId] = useState('');

  const [byokProvider, setByokProvider] = useState('');
  const [byokModel, setByokModel] = useState('');
  const [byokKey, setByokKey] = useState('');

  const [conversations, setConversations] = useState([]);
  const [isConversationsLoading, setIsConversationsLoading] = useState(true);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [isShared, setIsShared] = useState(false);

  const [memories, setMemories] = useState([]);
  const [memoriesOpen, setMemoriesOpen] = useState(false);

  const [isChatLoading, setIsChatLoading] = useState(false);

  const { toast } = useToast();
  const scrollRef = useRef(null);

  const filteredCourses = selectedDeptId
    ? allCourses.filter(c => c.department_id === selectedDeptId)
    : allCourses;

  const offerings = selectedCourseId
    ? allCourses.find(c => c.id === selectedCourseId)?.offerings || []
    : [];

  const fetchConversations = useCallback(async () => {
    setIsConversationsLoading(true);
    try {
      const response = await api.get('/api/v1/chat/conversations');
      setConversations(response.data.data || []);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    } finally {
      setIsConversationsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const loadConversation = async (convId) => {
    if (convId === activeConversationId || convId === 'temp') return;
    
    setIsChatLoading(true);
    setActiveConversationId(convId);
    
    try {
      const response = await api.get(`/api/v1/chat/conversations/${convId}`);
      const data = response.data.data;
      
      const formattedMessages = data.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        metadata: msg.metadata || null
      }));
      
      setMessages(formattedMessages);
      setIsShared(data.is_shared || false);
    } catch (err) {
      toast({ title: 'Error', description: 'Failed to load conversation', variant: 'destructive' });
      createNewChat();
    } finally {
      setIsChatLoading(false);
    }
  };

  const createNewChat = () => {
    setMessages([{
      role: 'assistant',
      content: 'Hello! I am the **KnowledgeOS Assistant**. Ask me about your curriculum, prerequisites, formulas, or any concept from your course materials.',
    }]);
    setActiveConversationId(null);
    setIsShared(false);
  };

  const deleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this chat?")) return;
    try {
      await api.delete(`/api/v1/chat/conversations/${convId}`);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (activeConversationId === convId) {
        createNewChat();
      }
      toast({ title: 'Success', description: 'Chat deleted' });
    } catch (err) {
      toast({ title: 'Error', description: 'Failed to delete chat', variant: 'destructive' });
    }
  };

  const clearMemories = async () => {
    if (!window.confirm("Are you sure you want to clear all learned facts about you? This action cannot be undone.")) return;
    try {
      await api.delete('/api/v1/chat/memories');
      setMemories([]);
      toast({ title: 'Success', description: 'AI memory cleared' });
      setMemoriesOpen(false);
    } catch (err) {
      toast({ title: 'Error', description: 'Failed to clear memory', variant: 'destructive' });
    }
  };

  useEffect(() => {
    if (scrollRef.current && !isChatLoading) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');

    const assistantIdx = messages.length + 1; // after user message

    if (!activeConversationId) {
      setConversations(prev => [{id: 'temp', title: 'New Conversation...'}, ...prev]);
      setActiveConversationId('temp');
    }

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: analysisMode === 'advanced' ? 'Agent is analyzing request...' : 'Assistant is thinking...', isThinking: true, metadata: null },
    ]);
    setIsLoading(true);
    setStreamingIdx(null);

    try {
      let courseCode = null;
      if (selectedCourseId) {
        const selectedCourse = allCourses.find(c => c.id === selectedCourseId);
        courseCode = selectedCourse?.code ?? null;
      }

      const baseURL = api.defaults.baseURL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('access_token');

      const response = await fetch(`${baseURL}/api/v1/query/ask_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query: userMessage,
          course_code: courseCode,
          use_citations: useCitations,
          mode: analysisMode,
          conversation_id: activeConversationId === 'temp' ? null : activeConversationId,
          ...(byokKey ? {
            byok_provider: byokProvider,
            byok_api_key: byokKey,
            byok_model: byokModel || undefined,
          } : {}),
        }),
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
                  msg.content = ''; // Clear placeholder
                }
                msg.content = assistantContent;
                next[lastIdx] = msg;
                return next;
              });
            } else if (data.type === 'metadata') {
              setStreamingIdx(null); // stop cursor
              setMessages(prev => {
                const next = [...prev];
                const lastIdx = next.length - 1;
                const msg = { ...next[lastIdx], metadata: data };
                next[lastIdx] = msg;
                return next;
              });
              if (data.conversation_id && data.conversation_id !== activeConversationId) {
                setActiveConversationId(data.conversation_id);
                fetchConversations();
              }
            }
          } catch {
            /* ignore parse errors on partial lines */
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

  const handleShareToggle = async () => {
    if (!activeConversationId) return;
    try {
      const response = await api.post(`/api/v1/chat/conversations/${activeConversationId}/share`, {
        is_shared: !isShared
      });
      setIsShared(response.data.data.is_shared);
      toast({ title: 'Success', description: response.data.data.is_shared ? 'Chat link is now public' : 'Chat is now private' });
    } catch (err) {
      toast({ title: 'Error', description: 'Failed to update share settings', variant: 'destructive' });
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
      <span key="neo4j" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
        <Network className="w-3 h-3" /> Graph
      </span>
    );
    if (backend === 'qdrant') return (
      <span key="qdrant" className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 uppercase tracking-wider border">
        <Database className="w-3 h-3" /> Vector
      </span>
    );
    if (backend === 'postgresql') return (
      <span key="postgresql" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
        <Database className="w-3 h-3" /> Catalog
      </span>
    );
    return null;
  }, []);

  return (
    <div className="flex flex-col md:flex-row h-screen w-full bg-background p-4 gap-6">

      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <ChatSidebar
        navigate={navigate}
        departments={departments}
        filteredCourses={filteredCourses}
        offerings={offerings}
        setMemoriesOpen={setMemoriesOpen}
        clearMemories={clearMemories}
        conversations={conversations}
        isConversationsLoading={isConversationsLoading}
        activeConversationId={activeConversationId}
        loadConversation={loadConversation}
        createNewChat={createNewChat}
        deleteConversation={deleteConversation}
        CHUNK_TYPE_CONFIG={CHUNK_TYPE_CONFIG}
      />

      <ChatSettingsSheet
        open={isSettingsOpen}
        onOpenChange={setIsSettingsOpen}
        departments={departments}
        filteredCourses={filteredCourses}
        offerings={offerings}
        selectedDeptId={selectedDeptId}
        setSelectedDeptId={setSelectedDeptId}
        selectedCourseId={selectedCourseId}
        setSelectedCourseId={setSelectedCourseId}
        selectedOfferingId={selectedOfferingId}
        setSelectedOfferingId={setSelectedOfferingId}
        useCitations={useCitations}
        setUseCitations={setUseCitations}
        byokProvider={byokProvider}
        setByokProvider={setByokProvider}
        byokModel={byokModel}
        setByokModel={setByokModel}
        byokKey={byokKey}
        setByokKey={setByokKey}
      />

      {/* ── Main chat area ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-0 bg-transparent rounded-2xl max-w-5xl mx-auto w-full relative">
        
        {/* Top Header / Share */}
        <div className="flex-none flex justify-between items-center px-4 py-3 bg-card/80 backdrop-blur border-b border-border rounded-t-2xl shadow-sm z-10">
          {/* Left Side: Model Selector */}
          <div className="flex items-center gap-3">
            <Select value={analysisMode} onValueChange={setAnalysisMode}>
              <SelectTrigger className="w-[180px] h-8 text-xs font-semibold bg-transparent border-none shadow-none focus:ring-0">
                <SelectValue placeholder="Select Model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="general">
                  <div className="flex items-center gap-2"><MessageSquare className="w-3.5 h-3.5 text-muted-foreground" /> General QA</div>
                </SelectItem>
                <SelectItem value="basic">
                  <div className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 text-blue-500" /> Basic Search</div>
                </SelectItem>
                <SelectItem value="advanced">
                  <div className="flex items-center gap-2"><Brain className="w-3.5 h-3.5 text-purple-500" /> Advanced Agent</div>
                </SelectItem>
                <SelectItem value="deep_research">
                  <div className="flex items-center gap-2"><Globe className="w-3.5 h-3.5 text-orange-500" /> Deep Research</div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Right Side: Share and Settings */}
          <div className="flex items-center gap-2">
            {activeConversationId && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleShareToggle}
                className={`h-8 gap-1.5 rounded-full text-[11px] font-medium border-border shadow-sm bg-muted/50 ${isShared ? 'text-primary border-primary/30' : 'text-muted-foreground hover:text-foreground'}`}
              >
                <Share2 className="w-3 h-3" />
                {isShared ? 'Shared' : 'Share'}
              </Button>
            )}
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSettingsOpen(true)}
              className="h-8 w-8 rounded-full text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 flex flex-col overflow-hidden relative border-t border-border bg-card/50">
          <ChatMessageList
          scrollRef={scrollRef}
          messages={messages}
          isChatLoading={isChatLoading}
          isLoading={isLoading}
          streamingIdx={streamingIdx}
          handleCitationClick={handleCitationClick}
          renderBackendBadge={renderBackendBadge}
        />
        </div>

        {/* Input */}
        <ChatInput
          input={input}
          setInput={setInput}
          handleSubmit={handleSubmit}
          isLoading={isLoading}
          selectedCourseId={selectedCourseId}
          analysisMode={analysisMode}
          byokKey={byokKey}
        />

      </div>
      
      {/* Memory Viewer Dialog */}
      <MemoryViewerDialog
        open={memoriesOpen}
        onOpenChange={setMemoriesOpen}
        memories={memories}
        setMemories={setMemories}
        activeConversationId={activeConversationId}
      />
    </div>
  );
};

export default Chat;
