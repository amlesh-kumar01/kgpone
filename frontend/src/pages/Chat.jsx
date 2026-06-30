import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Bot, User, Send, Network, Database, Loader2, Sparkles, BookOpen, Filter, ChevronLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from '../lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useAcademic } from '../context/AcademicContext';

const remarkPlugins = [remarkGfm, remarkMath];
const rehypePlugins = [rehypeKatex];

const MarkdownComponents = {
  a: ({node, href, children, ...props}) => {
    if (href && href.startsWith('#CIT-')) {
      return (
        <a href={href} className="text-primary font-semibold hover:underline cursor-pointer bg-primary/10 px-1 rounded-sm mx-0.5" onClick={(e) => {
          e.preventDefault();
          document.getElementById(href.substring(1))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }}>
          {children}
        </a>
      );
    }
    return <a href={href} className="text-primary font-medium hover:underline" target="_blank" rel="noreferrer" {...props}>{children}</a>;
  }
};

const ChatMessage = React.memo(({ msg, handleCitationClick, renderBackendBadge }) => {
  return (
    <div className={`flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center shadow-sm ${
        msg.role === 'user' 
          ? 'bg-primary text-primary-foreground' 
          : msg.isError 
            ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' 
            : 'bg-white dark:bg-slate-800 border text-slate-600 dark:text-slate-300'
      }`}>
        {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
      </div>
      
      {/* Message Content */}
      <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
        
        {/* Intent & Backends Badges (Only for Assistant) */}
        {msg.metadata && (
          <div className="flex flex-wrap gap-2 mb-2 items-center">
            {msg.metadata.intent && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 uppercase tracking-wider border">
                {msg.metadata.intent.replace('_', ' ')}
              </span>
            )}
            {msg.metadata.backends_used?.map(b => renderBackendBadge(b))}
          </div>
        )}

        {/* Bubble */}
        <div className={`px-5 py-4 rounded-3xl shadow-sm text-[15px] ${
          msg.role === 'user'
            ? 'bg-primary text-primary-foreground rounded-tr-sm'
            : msg.isError
              ? 'bg-red-50 text-red-900 border border-red-200 dark:bg-red-950/50 dark:text-red-200 dark:border-red-900 rounded-tl-sm'
              : 'bg-white border border-slate-200/60 text-slate-800 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200 rounded-tl-sm'
        }`}>
          {msg.role === 'user' ? (
            <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
          ) : (
            <div className="prose prose-slate dark:prose-invert max-w-none break-words leading-relaxed">
              <ReactMarkdown 
                remarkPlugins={remarkPlugins}
                rehypePlugins={rehypePlugins}
                components={MarkdownComponents}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Citations/Sources block */}
        {msg.metadata?.citations && msg.metadata.citations.length > 0 && (
          <div className="mt-3 w-full flex flex-col gap-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider ml-1">Sources Reference</p>
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
                      className={`flex items-center gap-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-2.5 py-1.5 shadow-sm text-xs transition-all hover:shadow-md ${isClickable ? 'cursor-pointer hover:border-primary/50 hover:bg-primary/5' : 'cursor-default'}`}
                    >
                      <BookOpen className={`w-3.5 h-3.5 ${isClickable ? 'text-primary' : 'text-slate-400'}`} />
                      <span className={`font-mono text-[10px] font-semibold ${isClickable ? 'text-primary' : 'text-slate-400'}`}>{cit.citation_id}</span>
                      <span className={`font-medium max-w-[180px] truncate ${isClickable ? 'text-slate-700 dark:text-slate-300' : 'text-slate-500'}`} title={cit.source_title}>
                        {cit.source_title}
                      </span>
                    </BadgeWrapper>
                    
                    {/* Snippet Tooltip */}
                    <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-80 p-3 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-xl shadow-xl border border-slate-700 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                      <div className="font-semibold mb-1 text-primary-400">
                        {cit.section ? `Topic: ${cit.section}` : `Source: ${cit.source_title}`}
                        {cit.page_number && cit.page_number > 0 && <span className="text-slate-400 font-normal"> (Pg. {cit.page_number})</span>}
                      </div>
                      <div className="italic text-slate-300 break-words line-clamp-6 leading-relaxed">"{cit.text_snippet}"</div>
                      <div className="absolute top-full left-6 -mt-[1px] border-4 border-transparent border-t-slate-900 dark:border-t-slate-800"></div>
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
  const navigate = useNavigate();
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
        <span key="qdrant" className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 uppercase tracking-wider border">
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
    <div className="flex flex-col md:flex-row h-screen w-full bg-slate-50/50 dark:bg-slate-950 p-4 gap-6">
      {/* Sidebar (Left) */}
      <div className="w-full md:w-72 shrink-0 flex flex-col bg-white/80 dark:bg-slate-900/80 backdrop-blur-md rounded-2xl border shadow-sm p-4 overflow-y-auto no-scrollbar">
        {/* Header / Logo */}
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => navigate(-1)}
            className="h-8 w-8 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 shrink-0"
          >
            <ChevronLeft className="w-5 h-5 text-slate-600 dark:text-slate-300" />
          </Button>
          <div className="p-2 bg-gradient-to-br from-primary/20 to-primary/5 rounded-lg text-primary shadow-sm border border-primary/10">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-bold leading-none mb-1 text-slate-800 dark:text-slate-100">KnowledgeOS</h1>
            <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Academic Tutor</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-4 mb-6 shrink-0">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <Filter size={14} className="text-slate-400" /> Filters
          </h2>
          
          <Select value={selectedDeptId} onValueChange={(val) => {
            setSelectedDeptId(val === 'all' ? '' : val);
            setSelectedCourseId('');
            setSelectedOfferingId('');
          }}>
            <SelectTrigger className="h-10 text-[13px] rounded-xl bg-slate-50/50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 shadow-sm transition-all focus:ring-2 focus:ring-primary/20">
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
            <SelectTrigger className="h-10 text-[13px] rounded-xl bg-slate-50/50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 shadow-sm transition-all focus:ring-2 focus:ring-primary/20">
              <SelectValue placeholder="2. Course" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any Course</SelectItem>
              {filteredCourses.map(c => <SelectItem key={c.id} value={c.id}>{c.code}</SelectItem>)}
            </SelectContent>
          </Select>

          <Select value={selectedOfferingId} onValueChange={(val) => setSelectedOfferingId(val === 'all' ? '' : val)} disabled={!selectedCourseId || offerings.length === 0}>
            <SelectTrigger className="h-10 text-[13px] rounded-xl bg-slate-50/50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 shadow-sm transition-all focus:ring-2 focus:ring-primary/20">
              <SelectValue placeholder={offerings.length === 0 && selectedCourseId ? "No offerings" : "3. Offering"} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any Offering</SelectItem>
              {offerings.map(o => <SelectItem key={o.id} value={o.id}>{o.semester} {o.year}</SelectItem>)}
            </SelectContent>
          </Select>
          
          <div className="pt-2">
            <label className="text-[13px] font-medium text-slate-700 dark:text-slate-300 flex items-center cursor-pointer select-none transition-colors hover:text-slate-900">
              <input 
                type="checkbox" 
                checked={useCitations} 
                onChange={(e) => setUseCitations(e.target.checked)}
                className="mr-3 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary transition-all shadow-sm"
              />
              Enable Inline Citations
            </label>
          </div>
        </div>

        {/* History Placeholder */}
        <div className="flex-1 flex flex-col min-h-0 pt-4 border-t border-slate-100 dark:border-slate-800">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Chat History</h2>
          <div className="flex-1 flex items-center justify-center bg-slate-50/50 dark:bg-slate-900/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-700 p-4">
            <p className="text-[11px] text-slate-400 font-medium text-center italic">
              History will appear here in a future update
            </p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-transparent rounded-2xl max-w-5xl mx-auto w-full">
        {/* Chat Messages Area */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-2 py-4 space-y-8 no-scrollbar scroll-smooth"
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
            <div className="flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="flex-shrink-0 w-9 h-9 rounded-full bg-white dark:bg-slate-800 border text-slate-600 dark:text-slate-300 flex items-center justify-center shadow-sm">
                <Bot className="w-5 h-5" />
              </div>
              <div className="px-5 py-4 rounded-3xl bg-white border border-slate-200/60 dark:bg-slate-900 dark:border-slate-800 rounded-tl-sm shadow-sm flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-[15px] text-slate-500 font-medium animate-pulse">Analyzing knowledge graph & vector space...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="pt-4 pb-2 shrink-0">
          <form onSubmit={handleSubmit} className="flex items-end gap-3 max-w-4xl mx-auto relative">
            <div className="relative flex-1 bg-white dark:bg-slate-900 rounded-3xl shadow-sm border border-slate-200/80 dark:border-slate-800 focus-within:ring-4 focus-within:ring-primary/10 focus-within:border-primary/30 transition-all duration-300">
              <Input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedCourseId ? "Ask about the selected course..." : "Ask about a topic, course prerequisites, or search documents..."}
                className="py-4 px-6 h-auto min-h-[60px] text-[15px] bg-transparent border-none shadow-none focus-visible:ring-0 resize-none rounded-3xl"
                disabled={isLoading}
              />
            </div>
            <Button 
              type="submit" 
              size="icon" 
              disabled={!input.trim() || isLoading}
              className="h-[60px] w-[60px] rounded-3xl shadow-md shrink-0 bg-primary hover:bg-primary/90 transition-all duration-300 hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
            >
              <Send className="w-5 h-5 ml-1" />
            </Button>
          </form>
          <div className="flex items-center justify-center mt-4 gap-1.5 text-[11px] text-slate-400 font-medium uppercase tracking-wide">
            <Bot className="w-3.5 h-3.5" />
            <span>AI responses can be inaccurate. Verify important information against official course syllabus.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
