import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Bot, User, Send, Network, Database, Loader2, Sparkles, BookOpen, Filter } from "lucide-react";
import api from '../lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useAcademic } from '../context/AcademicContext';

const ChatMessage = React.memo(({ msg, handleCitationClick, renderBackendBadge }) => {
  return (
    <div className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        msg.role === 'user' 
          ? 'bg-primary text-primary-foreground' 
          : msg.isError 
            ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' 
            : 'bg-accent text-accent-foreground border shadow-sm'
      }`}>
        {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>
      
      {/* Message Content */}
      <div className={`flex flex-col max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
        
        {/* Intent & Backends Badges (Only for Assistant) */}
        {msg.metadata && (
          <div className="flex flex-wrap gap-2 mb-2 items-center">
            {msg.metadata.intent && (
              <span className="inline-flex items-center px-2 py-1 rounded text-[10px] font-medium bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300 uppercase tracking-wider">
                INTENT: {msg.metadata.intent}
              </span>
            )}
            {msg.metadata.backends_used?.map(b => renderBackendBadge(b))}
          </div>
        )}

        {/* Bubble */}
        <div className={`px-4 py-3 rounded-2xl shadow-sm text-sm ${
          msg.role === 'user'
            ? 'bg-primary text-primary-foreground rounded-tr-sm'
            : msg.isError
              ? 'bg-red-50 text-red-900 border border-red-200 dark:bg-red-950/50 dark:text-red-200 dark:border-red-900 rounded-tl-sm'
              : 'bg-white border text-slate-800 dark:bg-slate-950 dark:border-slate-800 dark:text-slate-200 rounded-tl-sm'
        }`}>
          {msg.role === 'user' ? (
            <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  a: ({node, href, children, ...props}) => {
                    if (href && href.startsWith('#CIT-')) {
                      return (
                        <a href={href} className="text-primary font-medium hover:underline cursor-pointer" onClick={(e) => {
                          e.preventDefault();
                          document.getElementById(href.substring(1))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }}>
                          {children}
                        </a>
                      );
                    }
                    return <a href={href} className="text-primary hover:underline" target="_blank" rel="noreferrer" {...props}>{children}</a>;
                  }
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Citations/Sources block */}
        {msg.metadata?.citations && msg.metadata.citations.length > 0 && (
          <div className="mt-2 w-full flex flex-col gap-1.5">
            <p className="text-xs font-semibold text-muted-foreground ml-1">Sources Reference:</p>
            <div className="flex flex-wrap gap-2">
              {msg.metadata.citations.map((cit, cidx) => {
                const isClickable = (cit.document_id && cit.document_id !== 'GRAPH') || cit.source_url;
                const BadgeWrapper = isClickable ? 'a' : 'div';
                return (
                  <div key={cidx} className="relative group">
                    <BadgeWrapper 
                      id={cit.citation_id} 
                      href={isClickable ? '#' : undefined} 
                      onClick={isClickable ? (e) => handleCitationClick(e, cit) : undefined}
                      className={`flex items-center gap-1.5 bg-white dark:bg-slate-900 border rounded-md px-2 py-1 shadow-sm text-xs transition-all hover:shadow-md ${isClickable ? 'cursor-pointer hover:border-primary' : 'cursor-default'}`}
                    >
                      <BookOpen className={`w-3 h-3 ${isClickable ? 'text-muted-foreground group-hover:text-primary transition-colors' : 'text-slate-400'}`} />
                      <span className={`font-mono text-[10px] ${isClickable ? 'text-muted-foreground group-hover:text-primary' : 'text-slate-400'}`}>{cit.citation_id}</span>
                      <span className={`font-medium max-w-[150px] truncate ${isClickable ? 'text-slate-700 dark:text-slate-300 group-hover:text-primary' : 'text-slate-500'}`} title={cit.source_title}>
                        {cit.source_title}
                      </span>
                    </BadgeWrapper>
                    
                    {/* Snippet Tooltip */}
                    <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-72 p-3 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-lg shadow-xl border border-slate-700 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                      <div className="font-semibold mb-1 text-primary-400">
                        {cit.section ? `Topic: ${cit.section}` : `Source: ${cit.source_title}`}
                        {cit.page_number && cit.page_number > 0 && <span className="text-slate-400 font-normal"> (Pg. {cit.page_number})</span>}
                      </div>
                      <div className="italic text-slate-300 break-words line-clamp-6 leading-relaxed">"{cit.text_snippet}"</div>
                      <div className="absolute top-full left-4 -mt-[1px] border-4 border-transparent border-t-slate-900 dark:border-t-slate-800"></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

const Chat = () => {
  const { departments, courses: allCourses } = useAcademic();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am the KnowledgeOS Assistant. You can ask me questions about your curriculum, prerequisites, or to explain concepts from your course materials. How can I help you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [useCitations, setUseCitations] = useState(true);
  
  // Cascading Selection State (Persistent)
  const [selectedDeptId, setSelectedDeptId] = useState(() => localStorage.getItem('kgpone_chat_dept_id') || '');
  const [selectedCourseId, setSelectedCourseId] = useState(() => localStorage.getItem('kgpone_chat_course_id') || '');
  const [selectedOfferingId, setSelectedOfferingId] = useState(() => localStorage.getItem('kgpone_chat_offering_id') || '');
  
  // Persist selections to localStorage
  useEffect(() => {
    localStorage.setItem('kgpone_chat_dept_id', selectedDeptId);
  }, [selectedDeptId]);

  useEffect(() => {
    localStorage.setItem('kgpone_chat_course_id', selectedCourseId);
  }, [selectedCourseId]);

  useEffect(() => {
    localStorage.setItem('kgpone_chat_offering_id', selectedOfferingId);
  }, [selectedOfferingId]);
  
  const [filteredCourses, setFilteredCourses] = useState([]);
  const [offerings, setOfferings] = useState([]);

  const { toast } = useToast();
  const scrollRef = useRef(null);

  // Filter courses when department changes
  useEffect(() => {
    if (selectedDeptId) {
      setFilteredCourses(allCourses.filter(c => String(c.department_id) === String(selectedDeptId)));
    } else {
      setFilteredCourses([]);
    }
  }, [selectedDeptId, allCourses]);

  // Fetch offerings when course changes
  useEffect(() => {
    if (selectedCourseId) {
      api.get(`/api/v1/academic/${selectedCourseId}/offerings`)
        .then(res => setOfferings(res.data.data || []))
        .catch(err => console.error("Failed to fetch offerings", err));
    } else {
      setOfferings([]);
    }
  }, [selectedCourseId]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message and empty assistant placeholder
    setMessages(prev => [
      ...prev, 
      { role: 'user', content: userMessage },
      { role: 'assistant', content: '', metadata: null }
    ]);
    setIsLoading(true);

    try {
      let courseCode = null;
      if (selectedCourseId) {
        const selectedCourse = allCourses.find(c => c.id === selectedCourseId);
        courseCode = selectedCourse ? selectedCourse.code : null;
      }

      const requestBody = {
        query: userMessage,
        course_code: courseCode || null,
        course_offering_id: selectedOfferingId || null,
        use_citations: useCitations
      };

      const baseURL = api.defaults.baseURL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${baseURL}/api/v1/query/ask_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error('Failed to fetch stream');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let assistantMessage = "";
      
      setIsLoading(false); // Stop loader when stream starts

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep the last (potentially incomplete) line in the buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'chunk') {
                assistantMessage += data.content;
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = {
                    ...newMessages[newMessages.length - 1],
                    content: assistantMessage
                  };
                  return newMessages;
                });
              } else if (data.type === 'metadata') {
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[newMessages.length - 1] = {
                    ...newMessages[newMessages.length - 1],
                    metadata: data
                  };
                  return newMessages;
                });
              }
            } catch (e) {
              console.error("SSE Parse Error", e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to communicate with KnowledgeOS. Please try again.",
        variant: "destructive"
      });
      setMessages(prev => {
         const newMessages = [...prev];
         newMessages[newMessages.length - 1] = {
           role: 'assistant',
           content: "I'm sorry, I encountered an error while processing your request. Please try again.",
           isError: true
         };
         return newMessages;
      });
      setIsLoading(false);
    }
  };

  const handleCitationClick = async (e, cit) => {
    e.preventDefault();
    if (cit.document_id && cit.document_id !== 'GRAPH') {
      try {
        const response = await api.get(`/api/v1/documents/${cit.document_id}/download`);
        if (response.data?.data) {
          window.open(response.data.data, '_blank');
        } else {
          toast({ title: "Error", description: "Could not generate download link", variant: "destructive" });
        }
      } catch (err) {
        console.error(err);
        toast({ title: "Error", description: "Failed to download document", variant: "destructive" });
      }
    } else if (cit.source_url) {
      window.open(cit.source_url, '_blank');
    }
  };

  const renderBackendBadge = (backend) => {
    if (backend === 'neo4j') {
      return (
        <span key="neo4j" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
          <Network className="w-3 h-3" /> Graph
        </span>
      );
    }
    if (backend === 'qdrant') {
      return (
        <span key="qdrant" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
          <Database className="w-3 h-3" /> Vector
        </span>
      );
    }
    if (backend === 'postgresql') {
      return (
        <span key="postgresql" className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
          <Database className="w-3 h-3" /> Catalog
        </span>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] w-full max-w-5xl mx-auto px-4 lg:px-0 py-4">
      {/* Compact Header & Filter */}
      <div className="flex flex-col md:flex-row items-center justify-between mb-3 gap-3 bg-card p-2.5 rounded-xl border shadow-sm">
        <div className="flex items-center gap-2 pr-3 md:border-r border-border shrink-0">
          <div className="p-1.5 bg-primary/10 rounded-md text-primary">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-bold leading-tight">KnowledgeOS</h1>
            <p className="text-[10px] text-muted-foreground">Academic Tutor</p>
          </div>
        </div>

        {/* Global Filter Bar (Compact) */}
        <div className="flex-1 flex flex-row items-center gap-2 overflow-x-auto no-scrollbar">
          <Filter size={14} className="text-muted-foreground shrink-0 hidden sm:block" />
          <div className="flex items-center gap-2 flex-1 min-w-max">
            <Select value={selectedDeptId} onValueChange={(val) => {
              setSelectedDeptId(val === 'all' ? '' : val);
              setSelectedCourseId('');
              setSelectedOfferingId('');
            }}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="1. Department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Department</SelectItem>
                {departments.map(d => <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>)}
              </SelectContent>
            </Select>

            <Select value={selectedCourseId} onValueChange={(val) => {
              setSelectedCourseId(val === 'all' ? '' : val);
              setSelectedOfferingId('');
            }} disabled={!selectedDeptId}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="2. Course" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Course</SelectItem>
                {filteredCourses.map(c => <SelectItem key={c.id} value={c.id}>{c.code}</SelectItem>)}
              </SelectContent>
            </Select>

            <Select value={selectedOfferingId} onValueChange={(val) => setSelectedOfferingId(val === 'all' ? '' : val)} disabled={!selectedCourseId || offerings.length === 0}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder={offerings.length === 0 && selectedCourseId ? "No offerings" : "3. Offering"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Offering</SelectItem>
                {offerings.map(o => <SelectItem key={o.id} value={o.id}>{o.semester} {o.year}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div className="flex items-center gap-2 pl-3 border-l border-border shrink-0">
          <label className="text-xs font-medium text-muted-foreground flex items-center cursor-pointer select-none">
            <input 
              type="checkbox" 
              checked={useCitations} 
              onChange={(e) => setUseCitations(e.target.checked)}
              className="mr-1.5 h-3.5 w-3.5 rounded border-slate-300 text-primary focus:ring-primary"
            />
            Citations
          </label>
        </div>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden border shadow-sm">
        {/* Chat Messages Area */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 space-y-6 bg-slate-50/50 dark:bg-slate-900/50 scroll-smooth"
        >
          {messages.map((msg, idx) => {
            if (msg.role === 'assistant' && msg.content === '' && !msg.metadata && !msg.isError) {
              return null;
            }
            return (
              <ChatMessage 
                key={idx} 
                msg={msg} 
                handleCitationClick={handleCitationClick}
                renderBackendBadge={renderBackendBadge} 
              />
            );
          })}

          {isLoading && (
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent text-accent-foreground border flex items-center justify-center shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-white border text-slate-800 dark:bg-slate-950 dark:border-slate-800 rounded-tl-sm shadow-sm flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground animate-pulse">Analyzing knowledge graph...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-3 bg-white dark:bg-slate-950 border-t">
          <form onSubmit={handleSubmit} className="flex items-end gap-2">
            <div className="relative flex-1">
              <Input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedCourseId ? "Ask about the selected course..." : "Ask about a topic, course prerequisites, or search documents..."}
                className="pr-12 py-3 h-10 text-sm bg-slate-50 dark:bg-slate-900/50 focus-visible:ring-primary/50"
                disabled={isLoading}
              />
            </div>
            <Button 
              type="submit" 
              size="icon" 
              disabled={!input.trim() || isLoading}
              className="h-10 w-10 rounded-lg shadow-sm shrink-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
          <div className="flex items-center justify-center mt-2 gap-1 text-[10px] text-muted-foreground">
            <Bot className="w-3 h-3" />
            <span>AI responses can be inaccurate. Verify important information against official course syllabus.</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Chat;
