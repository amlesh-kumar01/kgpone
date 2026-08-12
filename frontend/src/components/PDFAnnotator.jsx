import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, ChevronLeft, ChevronRight, Save, X, Edit3 } from "lucide-react";
import api from '../lib/api';
import { useToast } from "@/hooks/use-toast";

const PDFAnnotator = ({ documentId, canonicalAst }) => {
  const [pagesManifest, setPagesManifest] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [edits, setEdits] = useState({});
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const fetchManifest = async () => {
      try {
        const res = await api.get(`/api/v1/inspect/${documentId}/pages_manifest`);
        if (res.data.data && Object.keys(res.data.data).length > 0) {
          setPagesManifest(res.data.data);
        } else {
          setPagesManifest({});
        }
      } catch (err) {
        console.error("Failed to load pages manifest", err);
        setPagesManifest({});
      } finally {
        setLoading(false);
      }
    };
    fetchManifest();
  }, [documentId]);

  const totalPages = pagesManifest ? Object.keys(pagesManifest).length : 0;
  
  const nodesOnCurrentPage = useMemo(() => {
    if (!canonicalAst || !canonicalAst.nodes) return [];
    
    // Flatten all nodes (tree to flat list)
    const flat = [];
    const traverse = (node) => {
      flat.push(node);
      if (node.children) node.children.forEach(traverse);
    };
    canonicalAst.nodes.forEach(traverse);
    
    return flat.filter(n => n.source && n.source.page_start === currentPage && n.source.bbox);
  }, [canonicalAst, currentPage]);

  const handleApplyEdits = async () => {
    if (Object.keys(edits).length === 0) return;
    
    setSaving(true);
    try {
      await api.post(`/api/v1/ingestion/${documentId}/apply-node-edits`, edits);
      toast({ title: "Successfully applied fixes and retriggered pipeline!" });
      setEdits({});
      setSelectedNode(null);
    } catch (err) {
      toast({ variant: "destructive", title: "Failed to apply edits", description: err.message });
    } finally {
      setSaving(false);
    }
  };

  const saveLocalEdit = (nodeId, text, latex) => {
    setEdits(prev => ({
      ...prev,
      [nodeId]: { text_content: text, latex: latex }
    }));
    setSelectedNode(null);
  };

  if (loading) return <div className="flex h-64 items-center justify-center"><Loader2 className="animate-spin text-muted-foreground" /></div>;
  if (!pagesManifest || totalPages === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <p>No page images found for this document.</p>
        <p className="text-xs opacity-50 mt-2">Make sure Docling was configured to generate page images.</p>
      </div>
    );
  }

  const currentDims = pagesManifest[currentPage.toString()] || { width: 595, height: 842 };

  return (
    <div className="flex flex-col h-full bg-zinc-950 text-zinc-100 rounded-lg overflow-hidden border border-zinc-800">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-zinc-800 bg-zinc-900">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>
            <ChevronLeft size={18} />
          </Button>
          <span className="text-sm font-medium">Page {currentPage} of {totalPages}</span>
          <Button variant="ghost" size="icon" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>
            <ChevronRight size={18} />
          </Button>
        </div>
        
        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-emerald-500/50 border border-emerald-500"></div> High</div>
          <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-amber-500/50 border border-amber-500"></div> Med</div>
          <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-rose-500/50 border border-rose-500"></div> Low</div>
        </div>
        
        <Button 
          size="sm" 
          onClick={handleApplyEdits} 
          disabled={Object.keys(edits).length === 0 || saving}
          className="bg-emerald-600 hover:bg-emerald-700 text-white"
        >
          {saving ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <Save className="mr-2 h-4 w-4" />}
          Apply {Object.keys(edits).length} Fixes
        </Button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* PDF Viewer */}
        <div className="flex-1 overflow-auto p-8 flex justify-center bg-zinc-950 relative">
          <div className="relative shadow-2xl" style={{ 
            width: '100%', 
            maxWidth: '800px', 
            aspectRatio: `${currentDims.width} / ${currentDims.height}` 
          }}>
            <img 
              src={`/api/v1/inspect/${documentId}/pages/${currentPage}`} 
              alt={`Page ${currentPage}`}
              className="w-full h-full object-contain rounded-md"
              style={{ display: 'block' }}
            />
            
            {/* Overlays */}
            {nodesOnCurrentPage.map((node) => {
              const bbox = node.source.bbox; // [l, t, r, b]
              const conf = node.source.confidence !== undefined ? node.source.confidence : 1.0;
              
              const left = (bbox[0] / currentDims.width) * 100;
              const top = (bbox[1] / currentDims.height) * 100;
              const width = ((bbox[2] - bbox[0]) / currentDims.width) * 100;
              const height = ((bbox[3] - bbox[1]) / currentDims.height) * 100;
              
              let colorClass = "border-emerald-500 bg-emerald-500/10 hover:bg-emerald-500/30";
              if (conf < 0.5) colorClass = "border-rose-500 bg-rose-500/20 hover:bg-rose-500/40";
              else if (conf < 0.8) colorClass = "border-amber-500 bg-amber-500/20 hover:bg-amber-500/40";
              
              const isEdited = !!edits[node.id];
              if (isEdited) colorClass = "border-blue-500 bg-blue-500/20";
              
              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`absolute border-[1.5px] cursor-pointer transition-colors rounded-sm backdrop-blur-[1px] ${colorClass}`}
                  style={{
                    left: `${left}%`,
                    top: `${top}%`,
                    width: `${width}%`,
                    height: `${height}%`,
                  }}
                  title={`Type: ${node.type} | Conf: ${conf}`}
                >
                  {isEdited && <div className="absolute -top-2 -right-2 w-4 h-4 bg-blue-500 rounded-full"></div>}
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Editor Sidebar */}
        {selectedNode && (
          <div className="w-80 border-l border-zinc-800 bg-zinc-900 p-4 flex flex-col shadow-xl z-10 animate-in slide-in-from-right-8 duration-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm flex items-center gap-2"><Edit3 size={16}/> Edit Node</h3>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setSelectedNode(null)}>
                <X size={14} />
              </Button>
            </div>
            
            <div className="text-xs space-y-1 mb-4 text-zinc-400">
              <p>Type: <span className="font-mono text-zinc-200">{selectedNode.type}</span></p>
              <p>Conf: <span className="font-mono text-zinc-200">{selectedNode.source?.confidence?.toFixed(2) || 1.0}</span></p>
            </div>
            
            <div className="flex-1 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-300">Text Content</label>
                <textarea 
                  className="w-full h-32 bg-zinc-950 border border-zinc-800 rounded p-2 text-sm font-mono focus:ring-1 focus:ring-blue-500 outline-none resize-none"
                  defaultValue={edits[selectedNode.id]?.text_content ?? selectedNode.text_content}
                  id="edit-text"
                />
              </div>
              
              {['EQUATION', 'FORMULA'].includes(selectedNode.type) && (
                <div className="space-y-2">
                  <label className="text-xs font-medium text-zinc-300">LaTeX</label>
                  <textarea 
                    className="w-full h-24 bg-zinc-950 border border-zinc-800 rounded p-2 text-sm font-mono focus:ring-1 focus:ring-blue-500 outline-none resize-none text-emerald-400"
                    defaultValue={edits[selectedNode.id]?.latex ?? selectedNode.latex ?? ""}
                    id="edit-latex"
                  />
                </div>
              )}
            </div>
            
            <div className="pt-4 mt-auto">
              <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white" onClick={() => {
                const text = document.getElementById('edit-text').value;
                const latex = document.getElementById('edit-latex')?.value;
                saveLocalEdit(selectedNode.id, text, latex);
              }}>
                Confirm Change
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFAnnotator;
