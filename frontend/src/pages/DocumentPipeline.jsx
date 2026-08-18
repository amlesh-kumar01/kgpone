import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2, ArrowLeft, Play, RefreshCw, CheckCircle2, AlertCircle, FileJson, Link as LinkIcon, Database, Check, ChevronRight, BookOpen, Download, Plus, Network } from "lucide-react";
import api from '../lib/api';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus as doclingStyle } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const PIPELINE_STAGES = [
  { group: 'Phase 1: Parse', icon: <FileJson size={14} />, stages: ['PARSE', 'AST'] },
  { group: 'Phase 2: Knowledge', icon: <Network size={14} />, stages: ['ENTITY', 'RELATION', 'GRAPH'] },
  { group: 'Phase 3: Indexing', icon: <Database size={14} />, stages: ['CHUNK', 'EMBED'] },
  { group: 'Phase 4: Completion', icon: <CheckCircle2 size={14} />, stages: ['MANIFEST'] },
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
  const [triggeringStage, setTriggeringStage] = useState(null);

  // Analysis Studio State
  const [generations, setGenerations] = useState([]);
  const [selectedGenId, setSelectedGenId] = useState('new');
  const [topics, setTopics] = useState([]);
  const [analysisType, setAnalysisType] = useState("FORMULA_SHEET");
  const [analysisTitle, setAnalysisTitle] = useState("");
  const [analysisPrompt, setAnalysisPrompt] = useState("");
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [genOutput, setGenOutput] = useState("");
  
  const selectedGen = generations.find(g => g.id === selectedGenId);

  useEffect(() => {
    const fetchGenOutput = async () => {
      if (selectedGen && selectedGen.output_url) {
        try {
          const res = await fetch(selectedGen.output_url);
          const text = await res.text();
          setGenOutput(text);
        } catch (e) {
          setGenOutput("Failed to load markdown.");
        }
      } else {
        setGenOutput("");
      }
    };
    fetchGenOutput();
  }, [selectedGen?.output_url]);

  const fetchPipeline = async () => {
    try {
      const [docRes, jobsRes, genRes, topicsRes] = await Promise.all([
        api.get(`/api/v1/documents/${documentId}`),
        api.get(`/api/v1/ingestion/${documentId}/jobs`),
        api.get(`/api/v1/generations/${documentId}/history`),
        api.get(`/api/v1/generations/${documentId}/topics`)
      ]);
      setDoc(docRes.data.data);
      setJobs(jobsRes.data.data);
      setGenerations(genRes.data.data || []);
      setTopics(topicsRes.data.data || []);
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
        if (isRunning) fetchPipeline();
        return currentJobs;
      });
      setGenerations(currentGens => {
        const isRunning = currentGens.some(g => g.status === 'RUNNING' || g.status === 'PENDING');
        if (isRunning) fetchPipeline();
        return currentGens;
      });
    }, 5000);
    return () => clearInterval(interval);
  }, [documentId]);

  const outputUrl = jobs.find(j => j.stage === selectedStage)?.output_url;
  const outputUrlBase = outputUrl ? outputUrl.split('?')[0] : null;

  useEffect(() => {
    const fetchOutput = async () => {
      if (!outputUrl) {
        setOutputData(null);
        return;
      }
      setOutputLoading(true);
      try {
        const res = await fetch(outputUrl);
        const data = await res.json();
        setOutputData(data);
      } catch (err) {
        console.error("Error fetching output:", err);
      } finally {
        setOutputLoading(false);
      }
    };
    fetchOutput();
  }, [outputUrlBase]);

  const handleRetryStage = async (stage) => {
    setTriggeringStage(stage);
    try {
      await api.post(`/api/v1/ingestion/${documentId}/jobs/${stage}/retry`);
      toast({ title: "Pipeline Triggered", description: `Stage ${stage} queued for execution.` });
      fetchPipeline();
    } catch (err) {
      toast({ variant: "destructive", title: "Action Failed", description: err.message });
    } finally {
      setTriggeringStage(null);
    }
  };

  const handleGenerateAnalysis = async () => {
    if (!analysisTitle || !analysisPrompt) {
      toast({ variant: "destructive", title: "Missing Fields", description: "Title and Prompt are required." });
      return;
    }
    setIsGenerating(true);
    try {
      await api.post(`/api/v1/generations/${documentId}/trigger`, {
        type: analysisType,
        title: analysisTitle,
        prompt: analysisPrompt,
        topics: selectedTopics
      });
      toast({ title: "Generation Started", description: "Your study material is being prepared." });
      fetchPipeline();
      setAnalysisTitle("");
      setAnalysisPrompt("");
      setSelectedTopics([]);
    } catch (err) {
      toast({ variant: "destructive", title: "Generation Failed", description: err.message });
    } finally {
      setIsGenerating(false);
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'COMPLETED': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      case 'RUNNING': return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      case 'FAILED': return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
      case 'SKIPPED': return 'bg-slate-500/10 text-muted-foreground border-slate-500/20';
      default: return 'bg-card hover:bg-accent text-muted-foreground border-border/50';
    }
  };

  if (loading) return <div className="p-8 flex items-center justify-center"><Loader2 className="animate-spin text-amber-500" /></div>;
  if (!doc) return <div className="p-8">Document not found</div>;

  const isComplete = jobs.find(j => j.stage === 'MANIFEST')?.status === 'COMPLETED';

  const toggleTopic = (topicName) => {
    if (selectedTopics.includes(topicName)) {
      setSelectedTopics(selectedTopics.filter(t => t !== topicName));
    } else {
      setSelectedTopics([...selectedTopics, topicName]);
    }
  };

  return (
    <div className="p-6 max-w-[1400px] mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/documents')}>
            <ArrowLeft size={18} />
          </Button>
          <div>
            <h1 className="text-2xl font-bold font-serif text-foreground">{doc.title}</h1>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span className="font-mono bg-card hover:bg-accent px-2 py-0.5 rounded text-xs">{doc.doc_type}</span>
              <span>•</span>
              <span>{doc.study_unit?.code}</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {!isComplete && (
            <Button 
              disabled={triggeringStage === 'PARSE'}
              onClick={() => handleRetryStage('PARSE')} 
              className="bg-[#fed488] hover:bg-[#e9c176] text-[#29210d]"
            >
              {triggeringStage === 'PARSE' ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Play size={16} className="mr-2" />}
              {jobs.some(j => j.status !== 'PENDING') ? 'Restart Pipeline' : 'Start Processing'}
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="pipeline" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="pipeline">Ingestion Pipeline</TabsTrigger>
          <TabsTrigger value="analysis">Analysis Studio</TabsTrigger>
        </TabsList>

        <TabsContent value="pipeline" className="space-y-4">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-4 space-y-6">
              {PIPELINE_STAGES.map((group, gidx) => (
                <div key={gidx} className="space-y-3">
                  <div className="flex items-center space-x-2 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    {group.icon}
                    <span>{group.group}</span>
                  </div>
                  
                  <div className="space-y-2 relative before:absolute before:inset-0 before:ml-[15px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-800 before:to-transparent">
                    {group.stages.map((stageName) => {
                      const job = jobs.find(j => j.stage === stageName);
                      const status = job ? job.status : 'PENDING';
                      const isSelected = selectedStage === stageName;
                      
                      return (
                        <div 
                          key={stageName}
                          onClick={() => setSelectedStage(stageName)}
                          className={`relative flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                            isSelected ? 'bg-card hover:bg-accent border-[#fed488]/50 shadow-[0_0_15px_rgba(254,212,136,0.1)]' : 'bg-background border-border hover:border-border/50'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center border ${getStatusColor(status)}`}>
                              {status === 'COMPLETED' ? <CheckCircle2 size={16} /> :
                               status === 'RUNNING' ? <Loader2 size={16} className="animate-spin" /> :
                               status === 'FAILED' ? <AlertCircle size={16} /> :
                               <div className="w-2 h-2 rounded-full bg-current opacity-50" />}
                            </div>
                            <div>
                              <div className={`font-medium ${isSelected ? 'text-[#fed488]' : 'text-foreground'}`}>
                                {stageName}
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {true && (
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                className="h-8 w-8 p-0 text-muted-foreground hover:text-[#fed488] hover:bg-[#fed488]/10"
                                onClick={(e) => { e.stopPropagation(); handleRetryStage(stageName); }}
                                disabled={triggeringStage === stageName}
                                title={`Restart ${stageName} and downstream stages`}
                              >
                                {triggeringStage === stageName ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                              </Button>
                            )}
                            <ChevronRight size={16} className={isSelected ? 'text-[#fed488]' : 'text-muted-foreground'} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="col-span-8">
              <Card className="h-full border-border bg-background/50 backdrop-blur">
                <CardHeader className="border-b border-border pb-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg font-medium text-[#fed488] flex items-center">
                        <FileJson size={18} className="mr-2" />
                        {selectedStage} Output
                      </CardTitle>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="mt-2 text-xs h-8 border-border hover:bg-accent"
                        disabled={!outputData}
                        onClick={() => {
                          if (!outputData) return;
                          const blob = new Blob([JSON.stringify(outputData, null, 2)], { type: 'application/json' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `${selectedStage.toLowerCase()}_output.json`;
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                      >
                        <Download size={14} className="mr-2" /> Download JSON
                      </Button>
                      <CardDescription>
                        {jobs.find(j => j.stage === selectedStage)?.status === 'COMPLETED' 
                          ? 'Artifact generated successfully.' 
                          : 'Artifact not yet available.'}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {outputLoading ? (
                    <div className="h-[600px] flex items-center justify-center">
                      <Loader2 size={24} className="animate-spin text-[#fed488]" />
                    </div>
                  ) : outputData ? (
                    selectedStage === 'MANIFEST' ? (
                      <div className="h-[600px] overflow-auto p-6 space-y-6">
                        <div className="flex items-center space-x-3 mb-6">
                          <CheckCircle2 size={32} className="text-[#fed488]" />
                          <div>
                            <h3 className="text-2xl font-serif text-[#fed488]">Processing Complete</h3>
                            <p className="text-muted-foreground">Document fully ingested and ready for analysis.</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <Card className="bg-background/50 border-border">
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm font-medium text-muted-foreground">Document Identity</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-lg font-semibold">{outputData.title || "Untitled Document"}</div>
                              <div className="text-xs text-muted-foreground mt-1 font-mono">{outputData.document_id}</div>
                            </CardContent>
                          </Card>
                          
                          <Card className="bg-background/50 border-border">
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm font-medium text-muted-foreground">Knowledge Extracted</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="flex space-x-6">
                                <div>
                                  <div className="text-2xl font-semibold text-[#fed488]">{outputData.stats?.entities || 0}</div>
                                  <div className="text-xs text-muted-foreground uppercase tracking-wider">Entities</div>
                                </div>
                                <div>
                                  <div className="text-2xl font-semibold text-[#fed488]">{outputData.stats?.chunks || 0}</div>
                                  <div className="text-xs text-muted-foreground uppercase tracking-wider">Chunks</div>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      </div>
                    ) : (
                      <div className="h-[600px] overflow-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent rounded-b-lg">
                        <SyntaxHighlighter
                          language="json"
                          style={doclingStyle}
                          customStyle={{ margin: 0, padding: '1.5rem', background: '#000b21', fontSize: '13px', minHeight: '100%' }}
                        >
                          {JSON.stringify(outputData, null, 2)}
                        </SyntaxHighlighter>
                      </div>
                    )
                  ) : (
                    <div className="h-[600px] flex items-center justify-center text-muted-foreground">
                      <div className="text-center">
                        <Database size={48} className="mx-auto mb-4 opacity-20" />
                        <p>No output available for this stage yet.</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4">
          <div className="grid grid-cols-12 gap-6 h-[800px]">
            <div className="col-span-3 border-r border-border pr-4 space-y-4 overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
              <Button 
                className="w-full bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border border-amber-500/30"
                onClick={() => setSelectedGenId('new')}
              >
                <Plus size={16} className="mr-2" /> New Generation
              </Button>
              
              <div className="space-y-2 mt-6">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Generation History</h3>
                {generations.map(gen => (
                  <div
                    key={gen.id}
                    onClick={() => setSelectedGenId(gen.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedGenId === gen.id ? 'bg-card hover:bg-accent border-amber-500/30' : 'bg-background/50 border-border hover:border-border/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-foreground">{gen.title}</span>
                      <div className={`w-2 h-2 rounded-full ${gen.status === 'COMPLETED' ? 'bg-emerald-500' : gen.status === 'RUNNING' ? 'bg-amber-500 animate-pulse' : 'bg-rose-500'}`} />
                    </div>
                    <div className="text-xs text-muted-foreground">{gen.type.replace('_', ' ')}</div>
                  </div>
                ))}
                {generations.length === 0 && (
                  <div className="text-sm text-muted-foreground text-center py-4">No history yet.</div>
                )}
              </div>
            </div>
            
            <div className="col-span-9 pl-2 h-full overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
              {selectedGenId === 'new' ? (
                <Card className="border-border bg-background/50 h-full">
                  <CardHeader>
                    <CardTitle className="text-amber-500">Create Study Material</CardTitle>
                    <CardDescription>Generate customized formula sheets, quizzes, and summaries based on your prompt.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Type</Label>
                        <Select value={analysisType} onValueChange={setAnalysisType}>
                          <SelectTrigger className="bg-background border-border">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="FORMULA_SHEET">Formula Sheet</SelectItem>
                            <SelectItem value="QUESTION_BANK">Question Bank</SelectItem>
                            <SelectItem value="CONCEPT_SUMMARY">Concept Summary</SelectItem>
                            <SelectItem value="REVISION_NOTES">Revision Notes</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Title</Label>
                        <Input 
                          placeholder="e.g., Chapter 3 Calculus Formulas" 
                          value={analysisTitle} 
                          onChange={(e) => setAnalysisTitle(e.target.value)}
                          className="bg-background border-border"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Custom Prompt (Instructions for Gemini)</Label>
                      <Input 
                        placeholder="e.g., Extract all differential equations related to kinematics." 
                        value={analysisPrompt} 
                        onChange={(e) => setAnalysisPrompt(e.target.value)}
                        className="bg-background border-border"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Select Topics (Optional filter from Knowledge Graph)</Label>
                      <div className="flex flex-wrap gap-2 p-4 rounded-md border border-border bg-background/50 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
                        {topics.map(t => (
                          <div 
                            key={t.name}
                            onClick={() => toggleTopic(t.name)}
                            className={`px-3 py-1 rounded-full text-xs font-medium cursor-pointer border transition-colors ${
                              selectedTopics.includes(t.name) 
                                ? 'bg-amber-500/20 text-amber-400 border-amber-500/50' 
                                : 'bg-card hover:bg-accent text-muted-foreground border-border/50 hover:bg-muted'
                            }`}
                          >
                            {t.name}
                          </div>
                        ))}
                        {topics.length === 0 && <span className="text-muted-foreground text-sm">No topics extracted yet. Run the pipeline first.</span>}
                      </div>
                    </div>
                    
                    <Button 
                      className="w-full bg-amber-500 hover:bg-amber-600 text-background font-medium"
                      onClick={handleGenerateAnalysis}
                      disabled={isGenerating}
                    >
                      {isGenerating ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Play size={16} className="mr-2" />}
                      Generate Material
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-border bg-background/50 h-full flex flex-col">
                  <CardHeader className="border-b border-border flex flex-row items-center justify-between py-4">
                    <div>
                      <CardTitle className="text-amber-500 text-lg">{selectedGen?.title}</CardTitle>
                      <CardDescription>{selectedGen?.prompt}</CardDescription>
                    </div>
                    {selectedGen?.status === 'COMPLETED' && (
                      <Button variant="outline" className="border-border/50 text-foreground/90" onClick={() => window.open(selectedGen.output_url)}>
                        <Download size={14} className="mr-2" /> Download Markdown
                      </Button>
                    )}
                  </CardHeader>
                  <CardContent className="flex-1 p-6 overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent prose prose-sm md:prose-base dark:prose-invert prose-amber max-w-none bg-card p-6 rounded-lg border border-border shadow-sm">
                    {selectedGen?.status === 'RUNNING' || selectedGen?.status === 'PENDING' ? (
                      <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                        <Loader2 size={32} className="animate-spin text-amber-500 mb-4" />
                        <p>Gemini is thinking... Generating your material.</p>
                      </div>
                    ) : selectedGen?.status === 'FAILED' ? (
                      <div className="text-rose-400 p-4 bg-rose-500/10 rounded border border-rose-500/20">
                        Failed to generate: {selectedGen.error_message}
                      </div>
                    ) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{genOutput || "No content generated yet."}</ReactMarkdown>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DocumentPipeline;
