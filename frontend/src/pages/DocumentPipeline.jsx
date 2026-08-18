import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2, ArrowLeft, Play, RefreshCw, CheckCircle2, AlertCircle, FileJson, Link as LinkIcon, Database, Check, ChevronRight } from "lucide-react";
import api from '../lib/api';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const PIPELINE_STAGES = [
  { group: 'Phase 1: Parse', icon: <FileJson size={14} />, stages: ['PARSE', 'AST'] },
  { group: 'Phase 2: Knowledge Extraction', icon: <LinkIcon size={14} />, stages: ['FORMULA', 'QUESTION', 'ENTITY', 'RELATION'] },
  { group: 'Phase 3: Indexing', icon: <Database size={14} />, stages: ['CHUNK', 'EMBED', 'GRAPH', 'MANIFEST'] },
];

const DocumentPipeline = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [doc, setDoc] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedStage, setSelectedStage] = useState('PARSE');
  const [outputData, setOutputData] = useState(null);
  const [outputLoading, setOutputLoading] = useState(false);

  const fetchPipeline = async () => {
    try {
      const [docRes, jobsRes] = await Promise.all([
        api.get(`/api/v1/documents/${documentId}`),
        api.get(`/api/v1/ingestion/${documentId}/jobs`)
      ]);
      setDoc(docRes.data.data);
      setJobs(jobsRes.data.data);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Failed to load pipeline",
        description: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPipeline();
    const interval = setInterval(() => {
      setJobs(currentJobs => {
        const isRunning = currentJobs.some(j => j.status === 'RUNNING' || j.status === 'PENDING');
        if (isRunning) {
          fetchPipeline();
        }
        return currentJobs;
      });
    }, 5000);
    return () => clearInterval(interval);
  }, [documentId]);

  useEffect(() => {
    const fetchOutput = async () => {
      const job = jobs.find(j => j.stage === selectedStage);
      if (!job || !job.output_url) {
        setOutputData(null);
        return;
      }
      
      setOutputLoading(true);
      try {
        const res = await fetch(job.output_url);
        const data = await res.json();
        setOutputData(data);
      } catch (err) {
        setOutputData({ error: "Failed to fetch output data" });
      } finally {
        setOutputLoading(false);
      }
    };

    fetchOutput();
  }, [selectedStage, jobs]);

  const handleTrigger = async (stage, e) => {
    e.stopPropagation();
    try {
      await api.post(`/api/v1/ingestion/${documentId}/jobs/${stage}/retry`);
      toast({ title: `Triggered ${stage}` });
      fetchPipeline();
    } catch (err) {
      toast({ variant: "destructive", title: "Failed to trigger stage", description: err.message });
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className="text-emerald-500 bg-background relative z-10" size={18} />;
      case 'FAILED': return <AlertCircle className="text-rose-500 bg-background relative z-10" size={18} />;
      case 'RUNNING':
      case 'PENDING': return <Loader2 className="text-amber-500 animate-spin bg-background relative z-10" size={18} />;
      default: return <div className="w-[18px] h-[18px] rounded-full border-2 border-muted-foreground/30 bg-background relative z-10" />;
    }
  };

  const renderASTNode = (node, depth = 0) => {
    if (!node.text_content && !node.latex && (!node.children || node.children.length === 0)) return null;
    
    const confidence = node.source?.confidence ?? 1.0;
    let bgColor = "bg-emerald-50/50 border-emerald-200/50";
    if (confidence < 0.5) bgColor = "bg-rose-50/50 border-rose-200/50";
    else if (confidence < 0.8) bgColor = "bg-amber-50/50 border-amber-200/50";

    return (
      <div key={node.id} className="mb-2 text-sm">
        {(node.text_content || node.latex) && (
          <div className={`px-4 py-3 rounded-lg border ${bgColor}`}>
            <div className="flex items-center gap-3 mb-1.5">
              <span className="text-[10px] font-bold tracking-widest uppercase bg-background/60 px-2 py-0.5 rounded text-muted-foreground">{node.type}</span>
              <span className="text-xs text-muted-foreground font-medium">Confidence: {Math.round(confidence * 100)}%</span>
            </div>
            {node.text_content && (
              <p className="text-foreground leading-relaxed whitespace-pre-wrap">{node.text_content}</p>
            )}
            {node.latex && (
              <p className="font-mono text-accent leading-relaxed mt-1 p-2 bg-background/50 rounded">{node.latex}</p>
            )}
          </div>
        )}
        {node.children && node.children.length > 0 && (
          <div className="pl-6 border-l-2 border-border/40 mt-2">
            {node.children.map(c => renderASTNode(c, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="animate-spin text-accent" size={32} /></div>;
  }

  const selectedJobObj = jobs.find(j => j.stage === selectedStage);

  return (
    <div className="w-full h-screen flex flex-col overflow-hidden bg-background">
      <div className="flex-none px-6 py-4 border-b border-border bg-card/50">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-2 text-muted-foreground h-8 -ml-3 hover:bg-muted/50">
          <ArrowLeft size={14} className="mr-2" /> Back to Documents
        </Button>
        <h1 className="text-2xl font-serif font-bold text-foreground">
          {doc?.title}
        </h1>
        <p className="text-muted-foreground font-mono mt-0.5 text-xs">Document Pipeline • {documentId}</p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Timeline Sidebar */}
        <div className="w-80 flex-none border-r border-border bg-card/30 overflow-y-auto custom-scrollbar p-6">
          <div className="relative">
            {PIPELINE_STAGES.map((phase, pIndex) => (
              <div key={pIndex} className="mb-10 last:mb-0">
                <div className="flex items-center gap-2 text-xs font-bold tracking-widest uppercase text-muted-foreground mb-5">
                  {phase.icon} {phase.group}
                </div>
                
                <div className="relative pl-1 space-y-2">
                  <div className="absolute left-[13px] top-3 bottom-0 w-px border-l-2 border-dashed border-border/60 -z-10"></div>
                  {phase.stages.map((stageName) => {
                    const job = jobs.find(j => j.stage === stageName) || { stage: stageName, status: 'PENDING' };
                    const isSelected = selectedStage === stageName;
                    
                    return (
                      <div key={stageName} className="relative flex items-start gap-4 group">
                        {/* Timeline Icon */}
                        <div className="relative z-10 bg-background rounded-full mt-2.5 p-0.5">
                          {getStatusIcon(job.status)}
                        </div>

                        {/* Clickable Card */}
                        <div 
                          onClick={() => setSelectedStage(stageName)}
                          className={`flex-1 flex flex-col py-2 px-3 rounded-lg transition-all border cursor-pointer
                            ${isSelected ? 'bg-muted shadow-sm border-border' : 'border-transparent hover:bg-muted/40'}
                          `}
                        >
                          <div className="flex items-center justify-between">
                            <span className={`font-semibold text-sm ${isSelected ? 'text-foreground' : 'text-muted-foreground group-hover:text-foreground'}`}>
                              {stageName}
                            </span>
                            
                            {/* Actions */}
                            <div className={`transition-opacity ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                              {(job.status === 'PENDING' || job.status === 'SKIPPED' || !job.started_at) ? (
                                <Button size="icon" variant="ghost" className="h-6 w-6" onClick={(e) => handleTrigger(stageName, e)}>
                                  <Play size={12} className="text-muted-foreground hover:text-foreground" />
                                </Button>
                              ) : (
                                <Button size="icon" variant="ghost" className="h-6 w-6" onClick={(e) => handleTrigger(stageName, e)} title="Retry">
                                  <RefreshCw size={12} className="text-muted-foreground hover:text-foreground" />
                                </Button>
                              )}
                            </div>
                          </div>
                          
                          <div className="text-[10px] text-muted-foreground mt-0.5">
                            {job.started_at ? new Date(job.started_at).toLocaleTimeString() : 'Pending'}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Output Area */}
        <div className="flex-1 flex flex-col bg-[#1e1e1e] overflow-hidden relative">
          <div className="flex-none p-4 border-b border-[#2d2d2d] bg-[#252526] flex items-center justify-between shadow-sm z-10">
            <div>
              <h2 className="text-gray-200 font-semibold flex items-center gap-2">
                <ChevronRight size={16} className="text-accent" />
                {selectedStage} Output
              </h2>
              {selectedJobObj?.status && (
                <p className="text-xs text-gray-400 ml-6 mt-0.5">Status: {selectedJobObj.status}</p>
              )}
            </div>
            {selectedStage === 'AST' && (
              <div className="flex gap-4 text-[10px] font-medium text-gray-400 bg-[#1e1e1e] px-3 py-1.5 rounded border border-[#2d2d2d]">
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-500"></div> &gt;80%</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-amber-500"></div> &gt;50%</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-rose-500"></div> &lt;50%</div>
              </div>
            )}
          </div>
          
          <div className="flex-1 overflow-auto custom-scrollbar">
            {!selectedJobObj?.output_url ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <FileJson className="mb-3 opacity-20" size={48} />
                <p>No output available for this stage yet.</p>
              </div>
            ) : outputLoading ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <Loader2 className="animate-spin mb-3 text-accent" size={32} />
                <p>Loading output...</p>
              </div>
            ) : selectedStage === 'AST' && outputData?.nodes ? (
              <div className="p-6 bg-background min-h-full">
                {outputData.nodes.map(n => renderASTNode(n))}
              </div>
            ) : (
              <SyntaxHighlighter
                language="json"
                style={vscDarkPlus}
                customStyle={{ margin: 0, padding: '1.5rem', background: 'transparent', fontSize: '13px' }}
                showLineNumbers={true}
                wrapLines={true}
              >
                {outputData ? JSON.stringify(outputData, null, 2) : "No data available"}
              </SyntaxHighlighter>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentPipeline;
