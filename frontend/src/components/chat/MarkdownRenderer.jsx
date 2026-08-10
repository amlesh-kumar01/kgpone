import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Copy } from 'lucide-react';

const remarkPlugins = [remarkGfm, remarkMath];
const rehypePlugins = [[rehypeKatex, { throwOnError: false, strict: false }]];

const CodeBlock = ({ language, children }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-4 rounded-xl overflow-hidden border border-border shadow-sm bg-[#282c34]">
      <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b border-border">
        <span className="text-xs font-semibold font-mono text-muted-foreground uppercase tracking-wider">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors text-[11px] font-medium"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          {copied ? <span className="text-emerald-400">Copied!</span> : 'Copy'}
        </button>
      </div>
      <div className="text-[13px] font-mono leading-relaxed overflow-x-auto">
        <SyntaxHighlighter
          language={language || 'text'}
          style={oneDark}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'transparent',
          }}
          codeTagProps={{
            style: {
              fontFamily: 'inherit',
            }
          }}
        >
          {children}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

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
      <div className="rounded-xl overflow-hidden border border-border shadow-md hover:shadow-lg transition-shadow duration-200 max-w-full">
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
        <figcaption className="text-xs text-muted-foreground text-center italic">
          Figure {node?.properties?.alt || 'Image'}
        </figcaption>
      )}
    </figure>
  ),
  pre: ({ node, children, ...props }) => (
    <>{children}</>
  ),
  code: ({ node, inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : '';
    
    if (inline || !match) {
      return (
        <code className="bg-muted text-foreground px-1.5 py-0.5 rounded-md font-mono text-[13px] border border-border" {...props}>
          {children}
        </code>
      );
    }
    
    return <CodeBlock language={language}>{String(children).replace(/\n$/, '')}</CodeBlock>;
  },
  table: ({ node, children, ...props }) => (
    <div className="my-3 overflow-x-auto rounded-lg border border-border shadow-sm">
      <table className="min-w-full divide-y divide-border text-sm" {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({node, ...props}) => (
    <th className="bg-muted px-4 py-2 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider" {...props}>
      {props.children}
    </th>
  ),
  td: ({node, ...props}) => (
    <td className="px-4 py-2 text-foreground border-t border-border" {...props}>
      {props.children}
    </td>
  ),
};

export const MarkdownRenderer = React.memo(({ content, isStreaming }) => {

  return (
    <div className="prose prose-slate dark:prose-invert max-w-none break-words leading-relaxed">
      <ReactMarkdown
        remarkPlugins={remarkPlugins}
        rehypePlugins={rehypePlugins}
        components={MarkdownComponents}
      >
        {content}
      </ReactMarkdown>
      {/* Blinking streaming cursor */}
      {isStreaming && <span className="kgp-cursor" aria-hidden="true" />}
    </div>
  );
});
