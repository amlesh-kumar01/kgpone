import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import {
  Bot, User, Send, Network, Database, Sparkles, BookOpen, Download,
  Filter, ChevronLeft, ImageIcon, Sigma, Table2, FileText
} from "lucide-react";
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

const getChunkConfig = (chunk_type) =>
  CHUNK_TYPE_CONFIG[chunk_type] || CHUNK_TYPE_CONFIG.text;

/* ── Markdown components ───────────────────────────────────────────────── */
const MarkdownComponents = {
  a: ({ node, href, children, ...props }) => {
    if (href && href.startsWith('#CIT-')) {
      return (
        <a
          href={href}
          className="text-primary font-semibold hover:underline cursor-pointer bg-primary/10 px-1 rounded-sm mx-0.5"
          onClick={(e) => {
            e.preventDefault();
            document.getElementById(href.substring(1))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }}
        >
          {children}
        </a>
      );
    }
    return (
      <a href={href} className="text-primary font-medium hover:underline" target="_blank" rel="noreferrer" {...props}>
        {children}
      </a>
    );
  },
  img: ({ node, src, alt, ...props }) => (
    <figure className="my-4 flex flex-col items-center gap-2">
      <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-md hover:shadow-lg transition-shadow duration-200 max-w-full">
        <img
          src={src}
          alt={alt || 'Figure'}
          className="max-w-full h-auto object-contain transition-transform duration-300 hover:scale-105"
          style={{ maxHeight: '480px' }}
          onError={(e) => { e.target.style.display = 'none'; }}
          {...props}
        />
      </div>
      {alt && alt !== 'Figure' && (
        <figcaption className="text-xs text-slate-500 dark:text-slate-400 text-center italic">
          {alt}
        </figcaption>
      )}
    </figure>
  ),
  code: ({ node, inline, className, children, ...props }) => {
    if (inline) {
      return (
        <code className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 px-1.5 py-0.5 rounded text-[13px] font-mono" {...props}>
          {children}
        </code>
      );
    }
    return (
      <div className="my-3 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700">
        <div className="bg-slate-100 dark:bg-slate-800 px-4 py-2 text-xs font-mono text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
          {className?.replace('language-', '') || 'code'}
        </div>
        <pre className="bg-slate-50 dark:bg-slate-900 px-4 py-3 overflow-x-auto text-[13px] font-mono leading-relaxed">
          <code className={className} {...props}>{children}</code>
        </pre>
      </div>
    );
  },
  table: ({ node, children, ...props }) => (
    <div className="my-3 overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700 text-sm" {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ node, children, ...props }) => (
    <th className="bg-slate-50 dark:bg-slate-800 px-4 py-2 text-left text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider" {...props}>
      {children}
    </th>
  ),
  td: ({ node, children, ...props }) => (
    <td className="px-4 py-2 text-slate-700 dark:text-slate-300 border-t border-slate-100 dark:border-slate-800" {...props}>
      {children}
    </td>
  ),
};

/* ── Citation card ─────────────────────────────────────────────────────── */
const CitationCard = React.memo(({ cit, onCitationClick }) => {
  const isClickable = (cit.document_id && cit.document_id !== 'GRAPH') || cit.source_url;

  return (
    <div className="relative group">
      <div
        id={cit.citation_id}
        onClick={isClickable ? (e) => onCitationClick(e, cit) : undefined}
        className={`flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 shadow-sm text-xs transition-all duration-200 hover:shadow-md select-none
          ${isClickable ? 'cursor-pointer hover:border-primary/50 hover:bg-primary/5' : 'cursor-default'}`}
      >
        <span className={`font-mono text-[10px] font-bold ${isClickable ? 'text-primary' : 'text-slate-400'}`}>
          [{cit.citation_id}]
        </span>
        <span
          className={`font-medium max-w-[160px] truncate ${isClickable ? 'text-slate-700 dark:text-slate-300' : 'text-slate-500'}`}
          title={cit.source_title}
        >
          {cit.source_title}
        </span>
        {cit.page_number && (
          <span className="text-slate-400 font-normal text-[10px]">p.{cit.page_number}</span>
        )}
      </div>

      {/* Rich hover tooltip */}
      <div className="absolute bottom-full left-0 mb-2 hidden group-hover:flex flex-col z-50 w-80 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-2xl shadow-2xl border border-slate-700 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none overflow-hidden">
        {/* Tooltip header */}
        <div className="px-3 pt-3 pb-2 border-b border-slate-700/60">
          <div className="font-semibold text-slate-100 truncate">{cit.source_title}</div>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            {cit.section && (
              <span className="text-primary-400 text-[10px] italic truncate max-w-[200px]" title={cit.section}>
                {cit.section}
              </span>
            )}
            {cit.page_number && (
              <span className="text-slate-400 text-[10px]">· Page {cit.page_number}</span>
            )}
          </div>
        </div>

        {/* Equation block */}
        {cit.chunk_type === 'equation' && cit.raw_latex && (
          <div className="px-3 py-2 border-b border-slate-700/60">
            <div className="text-[10px] text-violet-400 font-semibold mb-1 flex items-center gap-1">
              <Sigma className="w-3 h-3" />
              {cit.equation_label ? `Equation (${cit.equation_label})` : 'Equation'}
            </div>
            <code className="block bg-slate-950 rounded-lg px-2 py-1.5 font-mono text-violet-300 text-[11px] break-all leading-relaxed">
              {cit.raw_latex}
            </code>
          </div>
        )}

        {/* Figure image preview */}
        {cit.chunk_type === 'figure' && cit.image_url && (
          <div className="px-3 py-2 border-b border-slate-700/60">
            <div className="text-[10px] text-emerald-400 font-semibold mb-1.5 flex items-center gap-1">
              <ImageIcon className="w-3 h-3" /> Figure Preview
            </div>
            <img
              src={cit.image_url}
              alt="Figure from document"
              className="w-full rounded-lg object-contain max-h-36 bg-slate-950"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          </div>
        )}

        {/* Text snippet */}
        <div className="px-3 py-2">
          <p className="italic text-slate-300 break-words line-clamp-5 leading-relaxed text-[11px]">
            "{cit.text_snippet}"
          </p>
        </div>

        {/* Confidence */}
        <div className="px-3 pb-2.5 flex items-center justify-between">
          <span className="text-[9px] text-slate-500 uppercase tracking-wider">{cit.confidence}</span>
          <span className="text-[9px] font-mono text-slate-500">{(cit.score * 100).toFixed(0)}% match</span>
        </div>

        {/* Tooltip arrow */}
        <div className="absolute top-full left-6 -mt-px border-4 border-transparent border-t-slate-900 dark:border-t-slate-800" />
      </div>
    </div>
  );
});

/* ── Chat message ──────────────────────────────────────────────────────── */
const ChatMessage = React.memo(({ msg, index, isStreaming, handleCitationClick, renderBackendBadge }) => {
  return (
    <div
      className={`flex gap-4 kgp-msg-enter ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
      style={{ animationDelay: `${Math.min(index * 30, 150)}ms` }}
    >
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

      {/* Content */}
      <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>

        {/* Intent & Backend badges */}
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
              {/* Blinking streaming cursor */}
              {isStreaming && <span className="kgp-cursor" aria-hidden="true" />}
            </div>
          )}
        </div>

        {/* Citations */}
        {msg.metadata?.citations?.length > 0 && (
          <div className="mt-3 w-full flex flex-col gap-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider ml-1">Sources</p>
            <div className="flex flex-wrap gap-2">
              {msg.metadata.citations.map((cit, cidx) => (
                <CitationCard
                  key={cidx}
                  cit={cit}
                  onCitationClick={handleCitationClick}
                />
              ))}
            </div>
          </div>
        )}

        {/* Related Documents (Download Links) */}
        {(() => {
          const docsWithUrls = msg.metadata?.citations?.filter(c => c.document_download_url) || [];
          // Deduplicate by document_id
          const uniqueDocs = Array.from(new Map(docsWithUrls.map(c => [c.document_id, c])).values());
          if (uniqueDocs.length === 0) return null;
          return (
            <div className="mt-4 w-full flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800 pt-3">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider ml-1">Related Documents</p>
              <div className="flex flex-col gap-2">
                {uniqueDocs.map(doc => (
                  <a
                    key={doc.document_id}
                    href={doc.document_download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/50 dark:hover:bg-slate-800 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-primary" />
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {doc.source_title}
                      </span>
                    </div>
                    <span className="flex items-center gap-1.5 text-xs font-medium bg-primary text-white px-3 py-1.5 rounded-md shadow-sm hover:bg-primary/90 transition-colors">
                      <Download className="w-3.5 h-3.5" />
                      Download
                    </span>
                  </a>
                ))}
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
});

/* ── Loading dots ─────────────────────────────────────────────────────── */
const LoadingDots = () => (
  <div className="flex gap-4 kgp-msg-enter">
    <div className="flex-shrink-0 w-9 h-9 rounded-full bg-white dark:bg-slate-800 border text-slate-600 dark:text-slate-300 flex items-center justify-center shadow-sm">
      <Bot className="w-5 h-5" />
    </div>
    <div className="px-5 py-4 rounded-3xl bg-white border border-slate-200/60 dark:bg-slate-900 dark:border-slate-800 rounded-tl-sm shadow-sm flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
      <span className="kgp-dot" />
      <span className="kgp-dot" />
      <span className="kgp-dot" />
    </div>
  </div>
);

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
  const [streamingIdx, setStreamingIdx] = useState(null); // index of the message being streamed
  const [useCitations, setUseCitations] = useState(true);

  // Cascading selection (persisted)
  const [selectedDeptId, setSelectedDeptId] = useState(() => localStorage.getItem('kgpone_chat_dept_id') || '');
  const [selectedCourseId, setSelectedCourseId] = useState(() => localStorage.getItem('kgpone_chat_course_id') || '');
  const [selectedOfferingId, setSelectedOfferingId] = useState(() => localStorage.getItem('kgpone_chat_offering_id') || '');

  useEffect(() => { localStorage.setItem('kgpone_chat_dept_id', selectedDeptId); }, [selectedDeptId]);
  useEffect(() => { localStorage.setItem('kgpone_chat_course_id', selectedCourseId); }, [selectedCourseId]);
  useEffect(() => { localStorage.setItem('kgpone_chat_offering_id', selectedOfferingId); }, [selectedOfferingId]);

  const [filteredCourses, setFilteredCourses] = useState([]);
  const [offerings, setOfferings] = useState([]);
  const { toast } = useToast();
  const scrollRef = useRef(null);

  useEffect(() => {
    if (selectedDeptId) {
      setFilteredCourses(allCourses.filter(c => String(c.department_id) === String(selectedDeptId)));
    } else {
      setFilteredCourses([]);
    }
  }, [selectedDeptId, allCourses]);

  useEffect(() => {
    if (selectedCourseId) {
      api.get(`/api/v1/academic/${selectedCourseId}/offerings`)
        .then(res => setOfferings(res.data.data || []))
        .catch(err => console.error("Failed to fetch offerings", err));
    } else {
      setOfferings([]);
    }
  }, [selectedCourseId]);

  // Smooth scroll to bottom
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

    const assistantIdx = messages.length + 1; // after user message

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: '', metadata: null },
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
          course_code: courseCode || null,
          course_offering_id: selectedOfferingId || null,
          use_citations: useCitations,
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
                next[next.length - 1] = { ...next[next.length - 1], content: assistantContent };
                return next;
              });
            } else if (data.type === 'metadata') {
              setStreamingIdx(null); // stop cursor
              setMessages(prev => {
                const next = [...prev];
                next[next.length - 1] = { ...next[next.length - 1], metadata: data };
                return next;
              });
            }
          } catch {
            /* ignore parse errors on partial lines */
          }
        }
      }
      setStreamingIdx(null);
    } catch (error) {
      console.error('Chat error:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to communicate with KnowledgeOS.',
        variant: 'destructive',
      });
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'assistant',
          content: "I'm sorry, I encountered an error. Please try again.",
          isError: true,
        };
        return next;
      });
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
    <div className="flex flex-col md:flex-row h-screen w-full bg-slate-50/50 dark:bg-slate-950 p-4 gap-6">

      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <div className="w-full md:w-72 shrink-0 flex flex-col bg-white/80 dark:bg-slate-900/80 backdrop-blur-md rounded-2xl border shadow-sm p-4 overflow-y-auto no-scrollbar">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <Button
            variant="ghost" size="icon"
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

          <Select
            value={selectedOfferingId}
            onValueChange={(val) => setSelectedOfferingId(val === 'all' ? '' : val)}
            disabled={!selectedCourseId || offerings.length === 0}
          >
            <SelectTrigger className="h-10 text-[13px] rounded-xl bg-slate-50/50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 shadow-sm transition-all focus:ring-2 focus:ring-primary/20">
              <SelectValue placeholder={offerings.length === 0 && selectedCourseId ? 'No offerings' : '3. Offering'} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any Offering</SelectItem>
              {offerings.map(o => <SelectItem key={o.id} value={o.id}>{o.semester} {o.year}</SelectItem>)}
            </SelectContent>
          </Select>

          <div className="pt-2">
            <label className="text-[13px] font-medium text-slate-700 dark:text-slate-300 flex items-center cursor-pointer select-none hover:text-slate-900 transition-colors">
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

        {/* Legend */}
        <div className="flex flex-col gap-2 pt-4 border-t border-slate-100 dark:border-slate-800">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Source Types</h2>
          {Object.entries(CHUNK_TYPE_CONFIG).map(([type, cfg]) => {
            const Icon = cfg.icon;
            return (
              <div key={type} className="flex items-center gap-2">
                <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[9px] font-bold ${cfg.color}`}>
                  <Icon className="w-2.5 h-2.5" /> {cfg.label}
                </span>
                <span className="text-[11px] text-slate-500 capitalize">{type.replace('_', ' ')}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Main chat area ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-0 bg-transparent rounded-2xl max-w-5xl mx-auto w-full">

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-2 py-4 space-y-8 no-scrollbar scroll-smooth">
          {messages.map((msg, idx) => {
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
          })}
          {isLoading && <LoadingDots />}
        </div>

        {/* Input */}
        <div className="pt-4 pb-2 shrink-0">
          <form onSubmit={handleSubmit} className="flex items-end gap-3 max-w-4xl mx-auto">
            <div className="relative flex-1 bg-white dark:bg-slate-900 rounded-3xl shadow-sm border border-slate-200/80 dark:border-slate-800 focus-within:ring-4 focus-within:ring-primary/10 focus-within:border-primary/30 transition-all duration-300">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedCourseId ? 'Ask about the selected course...' : 'Ask about a topic, prerequisites, formulas, or figures...'}
                className="py-4 px-6 h-auto min-h-[60px] text-[15px] bg-transparent border-none shadow-none focus-visible:ring-0 resize-none rounded-3xl"
                disabled={isLoading}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); }
                }}
              />
            </div>
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isLoading}
              className="h-[60px] w-[60px] rounded-3xl shadow-md shrink-0 bg-primary hover:bg-primary/90 transition-all duration-200 hover:scale-[1.04] active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
            >
              <Send className="w-5 h-5 ml-0.5" />
            </Button>
          </form>
          <div className="flex items-center justify-center mt-3 gap-1.5 text-[11px] text-slate-400 font-medium uppercase tracking-wide">
            <Bot className="w-3.5 h-3.5" />
            <span>AI responses may be inaccurate. Verify against official course materials.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
