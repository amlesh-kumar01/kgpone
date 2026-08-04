import React from 'react';
import { Bot, User, Sparkles, FileText, Download } from 'lucide-react';
import { CitationCard } from './CitationCard';
import { MarkdownRenderer } from './MarkdownRenderer';

export const ChatMessage = React.memo(({ msg, index, isStreaming, handleCitationClick, renderBackendBadge }) => {
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
            : 'bg-card border text-muted-foreground'
      }`}>
        {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
      </div>

      {/* Content */}
      <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>

        {/* Intent & Backend badges */}
        {msg.metadata && (
          <div className="flex flex-wrap gap-2 mb-2 items-center">
            {msg.metadata.intent && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-muted text-muted-foreground uppercase tracking-wider border">
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
              : 'bg-card border border-border/60 text-foreground rounded-tl-sm'
        }`}>
          {msg.role === 'user' ? (
            <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
          ) : msg.isThinking ? (
            <div className="animate-pulse text-muted-foreground italic whitespace-pre-wrap leading-relaxed flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" /> {msg.content}
            </div>
          ) : (
            <MarkdownRenderer content={msg.content} isStreaming={isStreaming} />
          )}
        </div>

        {/* Citations */}
        {msg.metadata?.citations?.length > 0 && (
          <div className="mt-3 w-full flex flex-col gap-2">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider ml-1">Sources</p>
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
          // Deduplicate by normalized source_title to prevent duplicates of the same PDF
          const uniqueDocsMap = new Map();
          docsWithUrls.forEach(c => {
            const key = (c.source_title || '').toLowerCase().trim() || c.document_id;
            if (key && !uniqueDocsMap.has(key)) {
              uniqueDocsMap.set(key, c);
            }
          });
          const uniqueDocs = Array.from(uniqueDocsMap.values());
          if (uniqueDocs.length === 0) return null;
          return (
            <div className="mt-4 w-full flex flex-col gap-2 border-t border-border pt-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider ml-1">Related Documents</p>
              <div className="flex flex-col gap-2">
                {uniqueDocs.map(doc => (
                  <a
                    key={doc.document_id}
                    href={doc.document_download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between bg-muted/50 hover:bg-muted px-4 py-2.5 rounded-lg border border-border transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-primary" />
                      <span className="text-sm font-medium text-foreground">
                        {doc.source_title || 'Document'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Download className="w-4 h-4 text-muted-foreground" />
                    </div>
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
