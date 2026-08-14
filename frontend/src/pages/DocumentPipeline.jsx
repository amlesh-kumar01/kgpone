import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2, ArrowLeft, Play, RefreshCw, CheckCircle2, AlertCircle, FileJson, Link as LinkIcon, Database, Check } from "lucide-react";
import api from '../lib/api';

const DocumentPipeline = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [doc, setDoc] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // AST state
  const [astData, setAstData] = useState(null);
  const [astLoading, setAstLoading] = useState(false);
  const [edits, setEdits] = useState({});
  const [applyingEdits, setApplyingEdits] = useState(false);

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
    // Poll every 5s if anything is running
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
    const astJob = jobs.find(j => j.stage === 'AST');
    if (astJob && astJob.status === 'COMPLETED' && astJob.output_url && !astData && !astLoading) {
      setAstLoading(true);
      fetch(astJob.output_url)
        .then(res => res.json())
        .then(data => setAstData(data))
        .catch(err => console.error("Failed to load AST", err))
        .finally(() => setAstLoading(false));
    }
  }, [jobs]);

  const handleTrigger = async (stage) => {
    try {
      await api.post(`/api/v1/ingestion/${documentId}/jobs/${stage}/retry`);
      toast({ title: `Triggered ${stage}` });
      fetchPipeline();
    } catch (err) {
      toast({ variant: "destructive", title: "Failed to trigger stage", description: err.message });
    }
  };

  const handleApplyEdits = async () => {
    if (Object.keys(edits).length === 0) return;
    setApplyingEdits(true);
    try {
      await api.post(`/api/v1/ingestion/${documentId}/apply-node-edits`, edits);
      toast({ title: "Edits applied successfully. Pipeline continuing..." });
      setEdits({});
      fetchPipeline();
    } catch (err) {
      toast({ variant: "destructive", title: "Failed to apply edits", description: err.message });
    } finally {
      setApplyingEdits(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className="text-green-500" size={20} />;
      case 'FAILED': return <AlertCircle className="text-red-500" size={20} />;
      case 'RUNNING':
      case 'PENDING': return <Loader2 className="text-amber-500 animate-spin" size={20} />;
      default: return <div className="w-5 h-5 rounded-full border-2 border-muted-foreground/30" />;
    }
  };

  const renderJobCard = (job) => {
    if (!job) return null;
    return (
      <Card key={job.stage} className="border-border shadow-sm mb-4 relative overflow-hidden group">
        <div className={`absolute top-0 left-0 w-1 h-full ${job.status === 'COMPLETED' ? 'bg-green-500' : job.status === 'FAILED' ? 'bg-red-500' : job.status === 'RUNNING' ? 'bg-amber-500' : 'bg-muted-foreground/20'}`} />
        <CardContent className="p-4 pl-5">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2 mb-1">
                {getStatusIcon(job.status)}
                <h3 className="font-semibold text-lg">{job.stage}</h3>
              </div>
              <p className="text-xs text-muted-foreground">
                {job.started_at ? new Date(job.started_at).toLocaleTimeString() : 'Not started'} 
                {job.completed_at && ` - ${new Date(job.completed_at).toLocaleTimeString()}`}
              </p>
              {job.error_message && (
                <div className="mt-2 p-2 bg-red-50 text-red-700 text-xs rounded border border-red-100 max-w-sm break-words">
                  {job.error_message}
                </div>
              )}
            </div>
            <div className="flex flex-col gap-2 items-end">
              {(job.status === 'PENDING' || job.status === 'SKIPPED' || job.status === undefined) ? (
                <Button size="sm" variant="outline" onClick={() => handleTrigger(job.stage)}>
                  <Play size={14} className="mr-1" /> Trigger
                </Button>
              ) : (
                <Button size="sm" variant="outline" onClick={() => handleTrigger(job.stage)} title="Retry (will clear downstream data)">
                  <RefreshCw size={14} className="mr-1" /> Retry
                </Button>
              )}
              {job.output_url && (
                <a href={job.output_url} target="_blank" rel="noreferrer" className="text-xs text-accent hover:underline flex items-center gap-1">
                  <FileJson size={12} /> View Output
                </a>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const getJob = (stage) => jobs.find(j => j.stage === stage);

  const renderASTNode = (node, depth = 0) => {
    // We only care about rendering blocks of text/equations for review
    if (!node.text_content && !node.latex && (!node.children || node.children.length === 0)) return null;
    
    const confidence = node.source?.confidence ?? 1.0;
    let bgColor = "bg-green-50/50 border-green-200";
    if (confidence < 0.5) bgColor = "bg-red-50 border-red-200";
    else if (confidence < 0.8) bgColor = "bg-amber-50 border-amber-200";

    const isEdited = edits[node.id] !== undefined;
    const currentText = isEdited && edits[node.id].text_content !== undefined ? edits[node.id].text_content : node.text_content;
    const currentLatex = isEdited && edits[node.id].latex !== undefined ? edits[node.id].latex : node.latex;

    return (
      <div key={node.id} className="mb-2">
        {(node.text_content || node.latex) && (
          <div className={`p-3 rounded-md border ${bgColor} relative group transition-all`}>
            <div className="flex justify-between items-start gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono bg-background/50 px-1.5 py-0.5 rounded text-muted-foreground">{node.type}</span>
                  <span className="text-xs text-muted-foreground">Confidence: {Math.round(confidence * 100)}%</span>
                  {isEdited && <span className="text-xs text-accent font-medium flex items-center gap-1"><Check size={12}/> Edited</span>}
                </div>
                {node.text_content && (
                  <textarea 
                    className="w-full text-sm bg-transparent border-b border-transparent hover:border-border focus:border-accent focus:outline-none focus:bg-background resize-y"
                    value={currentText || ""}
                    onChange={(e) => setEdits(prev => ({ ...prev, [node.id]: { ...prev[node.id], text_content: e.target.value } }))}
                    rows={currentText.split('\n').length || 1}
                  />
                )}
                {node.latex && (
                  <textarea 
                    className="w-full text-sm font-mono bg-background/50 border-b border-transparent hover:border-border focus:border-accent focus:outline-none resize-y mt-1 p-1"
                    value={currentLatex || ""}
                    onChange={(e) => setEdits(prev => ({ ...prev, [node.id]: { ...prev[node.id], latex: e.target.value } }))}
                    rows={currentLatex.split('\n').length || 1}
                  />
                )}
              </div>
            </div>
          </div>
        )}
        {node.children && node.children.length > 0 && (
          <div className="pl-6 border-l-2 border-border/30 mt-2">
            {node.children.map(c => renderASTNode(c, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="animate-spin text-accent" size={32} /></div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Button variant="ghost" onClick={() => navigate('/documents')} className="mb-4 text-muted-foreground -ml-4">
        <ArrowLeft size={16} className="mr-2" /> Back to Documents
      </Button>
      
      <div className="mb-8">
        <h1 className="text-3xl font-serif font-bold text-foreground flex items-center gap-3">
          Pipeline: {doc?.title}
        </h1>
        <p className="text-muted-foreground font-mono mt-1 text-sm">{documentId}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Pipeline Column */}
        <div className="lg:col-span-1 space-y-6">
          <div>
            <h2 className="text-sm font-bold tracking-wider text-muted-foreground uppercase mb-3 flex items-center gap-2">
              <FileJson size={16} /> Phase 1: Parse
            </h2>
            {renderJobCard(getJob('PARSE'))}
            {renderJobCard(getJob('AST'))}
          </div>

          <div>
            <h2 className="text-sm font-bold tracking-wider text-muted-foreground uppercase mb-3 flex items-center gap-2">
              <LinkIcon size={16} /> Phase 2: Knowledge Extraction
            </h2>
            <div className="pl-4 border-l-2 border-border/50">
              {renderJobCard(getJob('FORMULA'))}
              {renderJobCard(getJob('QUESTION'))}
              {renderJobCard(getJob('ENTITY'))}
              {renderJobCard(getJob('RELATION'))}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-bold tracking-wider text-muted-foreground uppercase mb-3 flex items-center gap-2">
              <Database size={16} /> Phase 3: Indexing
            </h2>
            {renderJobCard(getJob('CHUNK'))}
            {renderJobCard(getJob('EMBED'))}
            {renderJobCard(getJob('GRAPH'))}
            {renderJobCard(getJob('MANIFEST'))}
          </div>
        </div>

        {/* Verification Column */}
        <div className="lg:col-span-2">
          <Card className="h-[calc(100vh-12rem)] flex flex-col bg-card border-border shadow-md">
            <CardHeader className="border-b border-border bg-muted/20 shrink-0 flex flex-row justify-between items-center">
              <div>
                <CardTitle className="font-serif">Data Verification</CardTitle>
                <CardDescription>Review and correct the parsed canonical AST before extracting knowledge.</CardDescription>
              </div>
              {Object.keys(edits).length > 0 && (
                <Button 
                  onClick={handleApplyEdits} 
                  disabled={applyingEdits}
                  className="bg-accent text-accent-foreground hover:bg-accent/90"
                >
                  {applyingEdits ? <Loader2 className="animate-spin mr-2" size={16}/> : <CheckCircle2 className="mr-2" size={16}/>}
                  Apply {Object.keys(edits).length} Fixes & Continue
                </Button>
              )}
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6 bg-muted/5">
              {!astData ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  {astLoading ? (
                    <><Loader2 className="animate-spin mb-2 text-accent" size={32} /> Loading AST preview...</>
                  ) : (
                    <><FileJson className="mb-2 opacity-50" size={32} /> Complete the Parse and AST stages to view the document structure here.</>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex gap-4 mb-4 text-xs font-medium text-muted-foreground p-3 bg-card rounded-lg border border-border">
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-green-500"></div> High Confidence (&gt;80%)</div>
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-amber-500"></div> Medium Confidence</div>
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-red-500"></div> Low Confidence (&lt;50%)</div>
                  </div>
                  {astData.nodes?.map(n => renderASTNode(n))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DocumentPipeline;
