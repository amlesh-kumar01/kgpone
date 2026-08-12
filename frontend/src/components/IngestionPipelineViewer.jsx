import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, Loader2, CheckCircle2, Download, FileJson, FileImage } from "lucide-react";
import api from '../lib/api';
import { useToast } from "@/hooks/use-toast";
import PDFAnnotator from './PDFAnnotator';

const IngestionPipelineViewer = ({ documentId }) => {
  const [jobs, setJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [retryingStage, setRetryingStage] = useState(null);
  const { toast } = useToast();

  const [artifacts, setArtifacts] = useState({});
  const [loadingArtifacts, setLoadingArtifacts] = useState(false);

  const fetchJobs = async () => {
    try {
      setLoadingJobs(true);
      const res = await api.get(`/api/v1/ingestion/${documentId}/jobs`);
      setJobs(res.data.data || []);
    } catch (err) {
      console.error("Failed to load jobs", err);
    } finally {
      setLoadingJobs(false);
    }
  };

  const fetchArtifacts = async () => {
    setLoadingArtifacts(true);
    const endpoints = [
      { key: "manifest", url: `/api/v1/inspect/${documentId}/manifest` },
      { key: "canonical", url: `/api/v1/inspect/${documentId}/canonical` },
      { key: "chunks", url: `/api/v1/inspect/${documentId}/chunks` },
      { key: "formulas", url: `/api/v1/inspect/${documentId}/knowledge/formulas` },
      { key: "entities", url: `/api/v1/inspect/${documentId}/knowledge/entities` },
      { key: "questions", url: `/api/v1/inspect/${documentId}/knowledge/questions` },
      { key: "relations", url: `/api/v1/inspect/${documentId}/knowledge/relations` },
    ];

    const results = {};
    for (const ep of endpoints) {
      try {
        const res = await api.get(ep.url);
        results[ep.key] = res.data.data;
      } catch (err) {
        results[ep.key] = null; // 404 or error
      }
    }
    setArtifacts(results);
    setLoadingArtifacts(false);
  };

  useEffect(() => {
    if (documentId) {
      fetchJobs();
      fetchArtifacts();
    }
  }, [documentId]);

  const handleRetry = async (stage) => {
    setRetryingStage(stage);
    try {
      await api.post(`/api/v1/ingestion/${documentId}/jobs/${stage}/retry`);
      toast({ title: `Retrying phase: ${stage}` });
      fetchJobs();
    } catch (err) {
      toast({ variant: "destructive", title: "Failed to retry", description: err.message });
    } finally {
      setRetryingStage(null);
    }
  };

  const getStatusBadge = (status) => {
    switch(status?.toUpperCase()) {
      case 'COMPLETED':
        return <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700 border border-green-200"><CheckCircle2 size={12}/> Done</span>;
      case 'FAILED':
        return <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 border border-red-200"><AlertCircle size={12}/> Failed</span>;
      default:
        return <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-200"><Loader2 className="animate-spin" size={12}/> Wait</span>;
    }
  };

  const downloadJson = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderArtifactTab = (key, title) => {
    const data = artifacts[key];
    if (!data) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-muted-foreground border rounded-md h-full">
          <AlertCircle size={24} className="mb-2 opacity-50" />
          <p>Artifact not found or not generated yet.</p>
        </div>
      );
    }

    return (
      <div className="flex flex-col h-full border rounded-md overflow-hidden bg-muted/10 relative">
        <div className="flex justify-between items-center bg-muted/30 px-4 py-2 border-b">
          <span className="font-mono text-sm font-medium">{title}</span>
          <Button variant="outline" size="sm" onClick={() => downloadJson(data, `${documentId}_${key}`)} className="h-7 text-xs gap-1">
            <Download size={14} /> Download JSON
          </Button>
        </div>
        <div className="flex-1 overflow-auto p-4 bg-zinc-950 text-zinc-50 font-mono text-xs">
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col md:flex-row gap-4 h-[600px]">
      {/* Left: Pipeline Jobs */}
      <div className="w-full md:w-1/3 flex flex-col border rounded-xl overflow-hidden bg-card">
        <div className="bg-muted/30 px-4 py-3 border-b flex justify-between items-center">
          <h3 className="font-semibold text-sm">Pipeline Phases</h3>
          <Button variant="ghost" size="sm" onClick={fetchJobs} className="h-7 text-xs" disabled={loadingJobs}>
            {loadingJobs ? <Loader2 className="h-3 w-3 animate-spin" /> : "Refresh"}
          </Button>
        </div>
        <div className="flex-1 overflow-auto p-3 space-y-2">
          {loadingJobs && jobs.length === 0 ? (
            <div className="flex justify-center p-4"><Loader2 className="animate-spin text-muted-foreground" /></div>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center p-4">No jobs found.</p>
          ) : (
            jobs.map((job, idx) => (
              <div key={job.stage} className="flex flex-col p-3 rounded-lg border border-border bg-background hover:bg-muted/10 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
                      {idx + 1}
                    </div>
                    <span className="text-sm font-medium">{job.stage}</span>
                  </div>
                  {getStatusBadge(job.status)}
                </div>
                {job.error_message && (
                  <p className="text-xs text-red-500 mb-2 line-clamp-2" title={job.error_message}>{job.error_message}</p>
                )}
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full text-xs h-7"
                  disabled={retryingStage === job.stage || job.status === 'RUNNING'}
                  onClick={() => handleRetry(job.stage)}
                >
                  {retryingStage === job.stage ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                  Retry Phase
                </Button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right: Artifact Viewer */}
      <div className="w-full md:w-2/3 flex flex-col border rounded-xl overflow-hidden bg-card">
        <div className="bg-muted/30 px-4 py-3 border-b flex justify-between items-center">
          <h3 className="font-semibold text-sm flex items-center gap-2"><FileJson size={16} className="text-accent" /> Raw Artifacts</h3>
          <Button variant="ghost" size="sm" onClick={fetchArtifacts} className="h-7 text-xs" disabled={loadingArtifacts}>
            {loadingArtifacts ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : "Refresh"}
          </Button>
        </div>
        <div className="flex-1 p-3 overflow-hidden">
          {loadingArtifacts && Object.keys(artifacts).length === 0 ? (
            <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin text-muted-foreground" /></div>
          ) : (
            <Tabs defaultValue="pdf" className="w-full h-full flex flex-col">
              <TabsList className="flex flex-wrap w-full h-auto min-h-10 mb-2 justify-start gap-1 p-1 bg-muted/50 rounded-lg">
                <TabsTrigger value="pdf" className="text-[10px] md:text-xs bg-emerald-500/10 text-emerald-600 data-[state=active]:bg-emerald-500 data-[state=active]:text-white"><FileImage size={12} className="mr-1"/> Visual PDF Review</TabsTrigger>
                <TabsTrigger value="manifest" className="text-[10px] md:text-xs">Manifest</TabsTrigger>
                <TabsTrigger value="canonical" className="text-[10px] md:text-xs">AST</TabsTrigger>
                <TabsTrigger value="chunks" className="text-[10px] md:text-xs">Chunks</TabsTrigger>
                <TabsTrigger value="entities" className="text-[10px] md:text-xs">Entities</TabsTrigger>
                <TabsTrigger value="formulas" className="text-[10px] md:text-xs">Formulas</TabsTrigger>
                <TabsTrigger value="questions" className="text-[10px] md:text-xs">Questions</TabsTrigger>
                <TabsTrigger value="relations" className="text-[10px] md:text-xs">Relations</TabsTrigger>
              </TabsList>
              
              <TabsContent value="pdf" className="flex-1 mt-0 h-full"><PDFAnnotator documentId={documentId} canonicalAst={artifacts["canonical"]} /></TabsContent>
              <TabsContent value="manifest" className="flex-1 mt-0 h-full">{renderArtifactTab("manifest", "Pipeline Manifest")}</TabsContent>
              <TabsContent value="canonical" className="flex-1 mt-0 h-full">{renderArtifactTab("canonical", "Canonical AST")}</TabsContent>
              <TabsContent value="chunks" className="flex-1 mt-0 h-full">{renderArtifactTab("chunks", "Semantic Chunks")}</TabsContent>
              <TabsContent value="entities" className="flex-1 mt-0 h-full">{renderArtifactTab("entities", "Extracted Entities")}</TabsContent>
              <TabsContent value="formulas" className="flex-1 mt-0 h-full">{renderArtifactTab("formulas", "Extracted Formulas")}</TabsContent>
              <TabsContent value="questions" className="flex-1 mt-0 h-full">{renderArtifactTab("questions", "Extracted Questions")}</TabsContent>
              <TabsContent value="relations" className="flex-1 mt-0 h-full">{renderArtifactTab("relations", "Entity Relations")}</TabsContent>
            </Tabs>
          )}
        </div>
      </div>
    </div>
  );
};

export default IngestionPipelineViewer;
