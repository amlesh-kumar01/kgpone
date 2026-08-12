import React, { useState, useEffect } from 'react';
import { Download, ChevronDown, ChevronUp, Loader2, AlertCircle, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import api from '@/lib/api';

const formatBytes = (bytes) => {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const JsonNode = ({ data, depth = 0 }) => {
  const [collapsed, setCollapsed] = useState(depth > 1);

  if (data === null) return <span className="text-slate-400">null</span>;
  if (typeof data === 'boolean') return <span className="text-purple-500">{data.toString()}</span>;
  if (typeof data === 'number') return <span className="text-blue-500">{data}</span>;
  if (typeof data === 'string') return <span className="text-emerald-600 dark:text-emerald-400">"{data}"</span>;

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-muted-foreground">[]</span>;
    return (
      <span>
        <button onClick={() => setCollapsed(!collapsed)} className="text-accent hover:opacity-70 text-xs font-bold">
          {collapsed ? <ChevronDown className="inline w-3 h-3" /> : <ChevronUp className="inline w-3 h-3" />}
          {' '}[{data.length}]
        </button>
        {!collapsed && (
          <div className="ml-4 border-l border-border/50 pl-3 mt-1 space-y-1">
            {data.map((item, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-muted-foreground text-xs">{i}:</span>
                <JsonNode data={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }

  if (typeof data === 'object') {
    const keys = Object.keys(data);
    if (keys.length === 0) return <span className="text-muted-foreground">{'{}'}</span>;
    return (
      <span>
        <button onClick={() => setCollapsed(!collapsed)} className="text-accent hover:opacity-70 text-xs font-bold">
          {collapsed ? <ChevronDown className="inline w-3 h-3" /> : <ChevronUp className="inline w-3 h-3" />}
          {' '}{'{'}…{'}'}
        </button>
        {!collapsed && (
          <div className="ml-4 border-l border-border/50 pl-3 mt-1 space-y-1">
            {keys.map((key) => (
              <div key={key} className="flex gap-2">
                <span className="text-rose-500 dark:text-rose-400 text-xs font-mono shrink-0">"{key}":</span>
                <JsonNode data={data[key]} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }

  return <span>{String(data)}</span>;
};

/**
 * ArtifactViewer – fetches and renders a document's extracted JSON artifact from S3.
 * Props:
 *   documentId  – string UUID
 *   artifactKey – 'entities' | 'formulas' | 'questions' | 'chunks'
 *   label       – display label
 *   countLabel  – what to call each item e.g. "entities"
 */
const ArtifactViewer = ({ documentId, artifactKey, label, countLabel = 'items' }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  const fetchArtifact = async () => {
    if (data) { setExpanded(!expanded); return; }
    setLoading(true);
    setError(null);
    try {
      // Get presigned download URL for the artifact
      const res = await api.get(`/api/v1/documents/${documentId}/artifacts/${artifactKey}`);
      const url = res.data.data?.url;
      if (!url) throw new Error('No URL returned');
      const response = await fetch(url);
      const json = await response.json();
      setData(json);
      setExpanded(true);
    } catch (err) {
      setError(err.message);
      setExpanded(true);
    } finally {
      setLoading(false);
    }
  };

  const count = Array.isArray(data) ? data.length : (data ? Object.keys(data).length : null);

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <button
        onClick={fetchArtifact}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
            <Database className="w-4 h-4 text-accent" />
          </div>
          <div className="text-left">
            <p className="font-semibold text-foreground text-sm">{label}</p>
            <p className="text-xs text-muted-foreground">
              {loading ? 'Loading…' : count !== null ? `${count} ${countLabel} found` : `Click to view`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {count !== null && (
            <span className="bg-accent/15 text-accent font-bold text-xs px-2.5 py-1 rounded-full">
              {count}
            </span>
          )}
          {loading ? <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" /> :
            expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> :
            <ChevronDown className="w-4 h-4 text-muted-foreground" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border">
          {error ? (
            <div className="p-5 flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="w-4 h-4" /> {error}
            </div>
          ) : data ? (
            <div className="p-4 font-mono text-xs overflow-auto max-h-72 bg-muted/20">
              <JsonNode data={data} depth={0} />
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default ArtifactViewer;
