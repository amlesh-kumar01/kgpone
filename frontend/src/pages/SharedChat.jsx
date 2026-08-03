import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Bot, User, Network, Database, Sparkles, Sigma, Table2, FileText, ImageIcon, ChevronLeft } from "lucide-react";
import api from '../lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

const remarkPlugins = [remarkGfm, remarkMath];
const rehypePlugins = [rehypeKatex];

const CHUNK_TYPE_CONFIG = {
  equation: { icon: Sigma, label: 'EQ', color: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300', border: 'border-violet-200 dark:border-violet-800' },
  figure: { icon: ImageIcon, label: 'FIG', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300', border: 'border-emerald-200 dark:border-emerald-800' },
  table_row: { icon: Table2, label: 'TBL', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300', border: 'border-amber-200 dark:border-amber-800' },
  text: { icon: FileText, label: 'TXT', color: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400', border: 'border-slate-200 dark:border-slate-700' },
};
const getChunkConfig = (chunk_type) => CHUNK_TYPE_CONFIG[chunk_type] || CHUNK_TYPE_CONFIG.text;

const ChatMessage = React.memo(({ msg, handleCitationClick, renderBackendBadge }) => {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end pr-2 group kgp-msg-enter">
        <div className="max-w-[75%] px-5 py-3.5 rounded-3xl rounded-tr-sm bg-slate-900 text-slate-50 dark:bg-slate-100 dark:text-slate-900 shadow-sm">
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-4 kgp-msg-enter">
      <div className="shrink-0 mt-1 flex flex-col items-center">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-primary/80 text-white flex items-center justify-center shadow-md border border-primary/20">
          <Bot className="w-5 h-5" />
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="px-5 py-4 rounded-3xl bg-white border border-slate-200/60 dark:bg-slate-900 dark:border-slate-800 rounded-tl-sm shadow-sm prose prose-slate dark:prose-invert max-w-none text-[15px] leading-relaxed prose-p:my-1.5 prose-headings:font-semibold prose-a:text-primary prose-a:no-underline hover:prose-a:underline">
          <ReactMarkdown remarkPlugins={remarkPlugins} rehypePlugins={rehypePlugins} components={{
             a: ({ node, ...props }) => {
              if (props.href && props.href.startsWith('#cit-')) {
                const citId = props.href.replace('#cit-', '');
                return (
                  <sup className="inline-flex">
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        const cit = msg.metadata?.citations?.find(c => String(c.id) === citId);
                        if (cit) handleCitationClick(e, cit);
                      }}
                      className="inline-flex items-center justify-center h-4 w-4 ml-0.5 rounded-full bg-primary/10 text-primary text-[9px] font-bold hover:bg-primary hover:text-white transition-colors cursor-pointer select-none"
                    >
                      {citId}
                    </button>
                  </sup>
                );
              }
              return <a {...props} className="text-primary hover:underline font-medium" target="_blank" rel="noopener noreferrer" />;
            }
          }}>
            {msg.content}
          </ReactMarkdown>
        </div>

        {msg.metadata?.citations?.length > 0 && (
          <div className="mt-3 ml-2 flex flex-wrap gap-2 animate-in fade-in slide-in-from-top-2 duration-500">
            {msg.metadata.citations.map((cit, i) => {
              const cfg = getChunkConfig(cit.chunk_type);
              const Icon = cfg.icon;
              return (
                <button
                  key={i}
                  onClick={(e) => handleCitationClick(e, cit)}
                  className={`group relative flex items-center max-w-[200px] h-7 bg-white dark:bg-slate-900 rounded-lg border shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md ${cfg.border} pr-2 overflow-hidden cursor-pointer`}
                >
                  <div className={`flex items-center justify-center h-full px-2 ${cfg.color} border-r ${cfg.border} transition-colors`}>
                    <span className="text-[10px] font-bold mr-1.5">{cit.id}</span>
                    <Icon className="w-3 h-3" />
                  </div>
                  <div className="flex-1 min-w-0 px-2 py-1 flex items-center justify-between gap-2">
                    <span className="text-[10px] font-medium text-slate-600 dark:text-slate-300 truncate group-hover:text-slate-900 dark:group-hover:text-slate-100 transition-colors">
                      {cit.title || cit.source_name || 'Document'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
});

const SharedChat = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchChat = async () => {
      try {
        const res = await api.get(`/api/v1/chat/shared/${id}`);
        if (res.data.messages) {
          const loadedMsgs = res.data.messages.map(m => ({
            role: m.role,
            content: m.content,
            metadata: m.metadata_payload
          }));
          setMessages(loadedMsgs);
        }
      } catch (err) {
        setError("This chat is either private or does not exist.");
      } finally {
        setLoading(false);
      }
    };
    fetchChat();
  }, [id]);

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

  if (loading) return <div className="flex items-center justify-center h-screen">Loading shared chat...</div>;
  if (error) return <div className="flex items-center justify-center h-screen text-red-500">{error}</div>;

  return (
    <div className="flex flex-col h-screen w-full bg-slate-50/50 dark:bg-slate-950 p-4 gap-6">
      <div className="w-full flex items-center gap-4 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md rounded-2xl border shadow-sm p-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/')} className="h-8 w-8 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800">
          <ChevronLeft className="w-5 h-5 text-slate-600 dark:text-slate-300" />
        </Button>
        <div className="p-2 bg-gradient-to-br from-primary/20 to-primary/5 rounded-lg text-primary shadow-sm border border-primary/10">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-sm font-bold leading-none mb-1 text-slate-800 dark:text-slate-100">KnowledgeOS</h1>
          <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Shared Public Conversation</p>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col min-h-0 bg-transparent rounded-2xl max-w-5xl mx-auto w-full overflow-y-auto px-2 py-4 space-y-8 no-scrollbar scroll-smooth">
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} msg={msg} handleCitationClick={handleCitationClick} />
        ))}
      </div>
    </div>
  );
};

export default SharedChat;
