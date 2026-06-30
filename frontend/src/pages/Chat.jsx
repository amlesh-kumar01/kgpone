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
    
    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // Find course code for the selected course
      let courseCode = null;
      if (selectedCourseId) {
        const selectedCourse = allCourses.find(c => c.id === selectedCourseId);
        courseCode = selectedCourse ? selectedCourse.code : null;
      }

      const response = await api.post('/api/v1/query/ask', {
        query: userMessage,
        course_code: courseCode || null,
        course_offering_id: selectedOfferingId || null
      });

      if (response.data.status === 'success') {
        const { answer, sources, backends_used, intent, citations } = response.data.data;
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: answer,
          metadata: {
            sources,
            backends_used,
            intent,
            citations
          }
        }]);
      } else {
        throw new Error(response.data.message || 'Failed to get answer');
      }
    } catch (error) {
      console.error('Chat error:', error);
      toast({
        title: "Error",
        description: error.response?.data?.message || "Failed to communicate with KnowledgeOS. Please try again.",
        variant: "destructive"
      });
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm sorry, I encountered an error while processing your request. Please try again.",
        isError: true
      }]);
    } finally {
      setIsLoading(false);
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
    <div className="flex flex-col h-[calc(100vh-8rem)] max-h-[800px] w-full max-w-5xl mx-auto px-4 lg:px-0">
      <div className="flex flex-col gap-4 mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-primary/10 rounded-lg text-primary">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">KnowledgeOS Assistant</h1>
            <p className="text-sm text-muted-foreground">Hybrid GraphRAG-powered academic tutor</p>
          </div>
        </div>

        {/* Global Filter Bar */}
        <Card className="rounded-lg shadow-sm border border-border bg-card">
          <CardContent className="p-4 flex flex-col md:flex-row gap-4 items-center">
            <div className="flex items-center gap-2 text-muted-foreground font-medium mr-2 whitespace-nowrap">
              <Filter size={18} /> Context Filter
            </div>
            <div className="flex-1 w-full grid grid-cols-1 md:grid-cols-3 gap-4">
              <Select value={selectedDeptId} onValueChange={(val) => {
                setSelectedDeptId(val === 'all' ? '' : val);
                setSelectedCourseId('');
                setSelectedOfferingId('');
              }}>
                <SelectTrigger>
                  <SelectValue placeholder="1. Any Department" />
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
                <SelectTrigger>
                  <SelectValue placeholder="2. Any Course" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Any Course</SelectItem>
                  {filteredCourses.map(c => <SelectItem key={c.id} value={c.id}>{c.code}</SelectItem>)}
                </SelectContent>
              </Select>

              <Select value={selectedOfferingId} onValueChange={(val) => setSelectedOfferingId(val === 'all' ? '' : val)} disabled={!selectedCourseId || offerings.length === 0}>
                <SelectTrigger>
                  <SelectValue placeholder={offerings.length === 0 && selectedCourseId ? "No offerings available" : "3. Any Offering"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Any Offering</SelectItem>
                  {offerings.map(o => <SelectItem key={o.id} value={o.id}>{o.semester} {o.year}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden border shadow-sm">
        {/* Chat Messages Area */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 space-y-6 bg-slate-50/50 dark:bg-slate-900/50 scroll-smooth"
        >
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
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
                </div>

                {/* Citations/Sources block */}
                {msg.metadata?.citations && msg.metadata.citations.length > 0 && (
                  <div className="mt-2 w-full flex flex-col gap-1.5">
                    <p className="text-xs font-semibold text-muted-foreground ml-1">Sources Reference:</p>
                    <div className="flex flex-wrap gap-2">
                      {msg.metadata.citations.map((cit, cidx) => (
                        <a 
                          id={cit.citation_id} 
                          key={cidx} 
                          href={cit.source_url || '#'} 
                          target={cit.source_url ? "_blank" : undefined}
                          rel="noreferrer"
                          className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border rounded-md px-2 py-1 shadow-sm text-xs group cursor-pointer hover:border-primary transition-all hover:shadow-md"
                        >
                          <BookOpen className="w-3 h-3 text-muted-foreground group-hover:text-primary transition-colors" />
                          <span className="font-mono text-[10px] text-muted-foreground group-hover:text-primary">{cit.citation_id}</span>
                          <span className="font-medium text-slate-700 dark:text-slate-300 max-w-[150px] truncate group-hover:text-primary" title={cit.source_title}>
                            {cit.source_title}
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

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
        <div className="p-4 bg-white dark:bg-slate-950 border-t">
          <form onSubmit={handleSubmit} className="flex items-end gap-2">
            <div className="relative flex-1">
              <Input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedCourseId ? "Ask about the selected course..." : "Ask about a topic, course prerequisites, or search documents..."}
                className="pr-12 py-6 text-sm bg-slate-50 dark:bg-slate-900/50 focus-visible:ring-primary/50"
                disabled={isLoading}
              />
            </div>
            <Button 
              type="submit" 
              size="icon" 
              disabled={!input.trim() || isLoading}
              className="h-[50px] w-[50px] rounded-xl shadow-sm"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
          <div className="flex items-center justify-center mt-3 gap-1 text-[10px] text-muted-foreground">
            <Bot className="w-3 h-3" />
            <span>AI responses can be inaccurate. Verify important information against official course syllabus.</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Chat;
