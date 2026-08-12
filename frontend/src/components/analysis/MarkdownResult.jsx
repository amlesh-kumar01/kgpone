import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

const MarkdownResult = ({ content, downloadUrl, downloadLabel = 'Download .md' }) => {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {downloadUrl && (
        <div className="flex justify-end px-5 py-3 border-b border-border bg-muted/30">
          <Button variant="outline" size="sm" asChild>
            <a href={downloadUrl} target="_blank" rel="noopener noreferrer" download>
              <Download className="w-4 h-4 mr-2" /> {downloadLabel}
            </a>
          </Button>
        </div>
      )}
      <div className="p-6 overflow-y-auto max-h-[65vh] prose prose-sm dark:prose-invert max-w-none
        prose-headings:font-serif prose-headings:text-foreground prose-headings:font-bold
        prose-p:text-muted-foreground prose-p:leading-relaxed
        prose-strong:text-foreground
        prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-code:text-xs
        prose-pre:bg-muted prose-pre:rounded-lg
        prose-table:w-full prose-th:text-left prose-th:font-semibold
        prose-li:text-muted-foreground
        prose-hr:border-border
        prose-blockquote:border-l-accent prose-blockquote:bg-accent/5 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:rounded-r-lg">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default MarkdownResult;
