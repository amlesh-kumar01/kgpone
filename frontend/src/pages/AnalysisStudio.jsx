import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import {
  ArrowLeft, FileText, Loader2, Download, Sparkles, BookOpen,
  FlaskConical, BrainCircuit, HelpCircle, Layers, CheckCircle2,
  AlertCircle, ExternalLink, FileDiff, RefreshCw
} from 'lucide-react';
import api from '@/lib/api';
import {
  triggerSummarize, triggerQuiz, triggerFormulaRevision,
  getAnalysisDownloadUrls, pollAnalysisJob, fetchArtifactMarkdown, fetchArtifactJson
} from '@/lib/analysisApi';
import MarkdownResult from '@/components/analysis/MarkdownResult';
import ArtifactViewer from '@/components/analysis/ArtifactViewer';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const StatusBadge = ({ status }) => {
  const map = {
    COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-700',
    FAILED:    'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:border-red-700',
    RUNNING:   'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:border-blue-700',
    PENDING:   'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:border-amber-700',
  };
  const icons = {
    COMPLETED: <CheckCircle2 className="w-3 h-3" />,
    FAILED:    <AlertCircle className="w-3 h-3" />,
    RUNNING:   <Loader2 className="w-3 h-3 animate-spin" />,
    PENDING:   <Loader2 className="w-3 h-3 animate-spin" />,
  };
  const cfg = map[status] || map.PENDING;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${cfg}`}>
      {icons[status]} {status}
    </span>
  );
};

// ─── Analysis Panel ──────────────────────────────────────────────────────────

const AnalysisPanel = ({ title, description, icon, triggerFn, documentId }) => {
  const [job, setJob] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [mdContent, setMdContent] = useState(null);
  const [mdUrl, setMdUrl] = useState(null);
  const intervalRef = useRef(null);
  const { toast } = useToast();

  const onResultReady = useCallback(async (urls) => {
    setMdUrl(urls?.md_url);
    if (urls?.md_url) {
      try {
        const text = await fetchArtifactMarkdown(urls.md_url);
        setMdContent(text);
      } catch (e) {
        console.error('Failed to fetch markdown:', e);
      }
    }
  }, []);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const res = await triggerFn(documentId);
      const newJob = { id: res.data.data.analysis_id, status: 'PENDING' };
      setJob(newJob);
      toast({ title: `${title} job started!` });

      intervalRef.current = pollAnalysisJob(newJob.id, async (updated) => {
        setJob(updated);
        if (updated.status === 'COMPLETED') {
          const dlRes = await getAnalysisDownloadUrls(updated.id);
          onResultReady(dlRes.data.data);
        }
      });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Failed to start job', description: err.response?.data?.message || err.message });
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => () => clearInterval(intervalRef.current), []);

  const isRunning = job?.status === 'PENDING' || job?.status === 'RUNNING';

  return (
    <div className="space-y-5">
      {/* Header Card */}
      <div className="rounded-xl border border-border bg-gradient-to-br from-card to-muted/30 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-accent/15 flex items-center justify-center shrink-0 mt-0.5">
              {icon}
            </div>
            <div>
              <h3 className="font-serif font-bold text-foreground text-lg">{title}</h3>
              <p className="text-muted-foreground text-sm mt-0.5">{description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {job && <StatusBadge status={job.status} />}
            <Button
              onClick={handleTrigger}
              disabled={triggering || isRunning}
              size="sm"
              className="bg-accent text-accent-foreground hover:bg-accent/90 gap-2 min-w-[120px]"
            >
              {triggering || isRunning
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</>
                : job?.status === 'COMPLETED'
                  ? <><RefreshCw className="w-4 h-4" /> Regenerate</>
                  : <><Sparkles className="w-4 h-4" /> Generate</>}
            </Button>
          </div>
        </div>
        {job?.error_message && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm dark:bg-red-950/30 dark:border-red-800 dark:text-red-400">
            {job.error_message}
          </div>
        )}
      </div>

      {/* Result */}
      {mdContent && (
        <MarkdownResult content={mdContent} downloadUrl={mdUrl} downloadLabel={`Download ${title}`} />
      )}

      {isRunning && !mdContent && (
        <div className="rounded-xl border border-border bg-card p-12 flex flex-col items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-accent" />
          </div>
          <p className="text-muted-foreground text-sm">AI is processing your document…</p>
          <p className="text-xs text-muted-foreground/60">This usually takes 10–30 seconds.</p>
        </div>
      )}
    </div>
  );
};

// ─── Quiz Panel ───────────────────────────────────────────────────────────────

const QuizPanel = ({ documentId }) => {
  const [job, setJob] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [revealed, setRevealed] = useState({});
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef(null);
  const { toast } = useToast();

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const res = await triggerQuiz(documentId);
      const newJob = { id: res.data.data.analysis_id, status: 'PENDING' };
      setJob(newJob);
      toast({ title: 'Quiz generation started!' });

      intervalRef.current = pollAnalysisJob(newJob.id, async (updated) => {
        setJob(updated);
        if (updated.status === 'COMPLETED') {
          try {
            const dlRes = await getAnalysisDownloadUrls(updated.id);
            const jsonUrl = dlRes.data.data?.json_url;
            if (jsonUrl) {
              const quizData = await fetchArtifactJson(jsonUrl);
              setQuestions(quizData.questions || []);
            }
          } catch (e) {
            console.error('Failed to load quiz:', e);
          }
        }
      });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Failed to start quiz', description: err.response?.data?.message || err.message });
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => () => clearInterval(intervalRef.current), []);

  const toggleReveal = (idx) => {
    setRevealed(prev => {
      const next = { ...prev, [idx]: !prev[idx] };
      setProgress(Math.round((Object.values(next).filter(Boolean).length / questions.length) * 100));
      return next;
    });
  };

  const isRunning = job?.status === 'PENDING' || job?.status === 'RUNNING';
  const revealedCount = Object.values(revealed).filter(Boolean).length;

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-border bg-gradient-to-br from-card to-muted/30 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-purple-500/15 flex items-center justify-center shrink-0">
              <HelpCircle className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <h3 className="font-serif font-bold text-foreground text-lg">Practice Quiz</h3>
              <p className="text-muted-foreground text-sm">AI-generated MCQs with answers — test your understanding</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {job && <StatusBadge status={job.status} />}
            <Button onClick={handleTrigger} disabled={triggering || isRunning} size="sm"
              className="bg-purple-600 hover:bg-purple-700 text-white gap-2 min-w-[120px]">
              {triggering || isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</>
                : questions.length > 0 ? <><RefreshCw className="w-4 h-4" /> Regenerate</>
                : <><Sparkles className="w-4 h-4" /> Generate</>}
            </Button>
          </div>
        </div>
      </div>

      {questions.length > 0 && (
        <>
          {/* Progress bar */}
          <div className="rounded-xl border border-border bg-card p-4">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium text-foreground">Progress</p>
              <p className="text-sm text-muted-foreground">{revealedCount} / {questions.length} answered</p>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-accent rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* MCQ Cards */}
          <div className="space-y-4">
            {questions.map((q, idx) => (
              <div key={idx} className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start gap-3">
                    <span className="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center text-xs font-bold text-accent shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <p className="font-medium text-foreground">{q.question_text}</p>
                  </div>
                  {q.options && (
                    <div className="mt-4 ml-10 grid grid-cols-1 gap-2">
                      {q.options.map((opt, oi) => {
                        const letter = ['A', 'B', 'C', 'D'][oi];
                        const isCorrect = revealed[idx] && opt === q.correct_answer;
                        return (
                          <div key={oi}
                            className={`flex items-start gap-2 p-3 rounded-lg border text-sm transition-colors ${
                              isCorrect
                                ? 'bg-emerald-50 border-emerald-300 text-emerald-800 dark:bg-emerald-950/30 dark:border-emerald-700 dark:text-emerald-300'
                                : 'bg-muted/30 border-border text-muted-foreground'
                            }`}>
                            <span className="font-bold shrink-0">{letter})</span>
                            <span>{opt}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
                <div className="px-5 pb-4 ml-10">
                  <button
                    onClick={() => toggleReveal(idx)}
                    className="text-xs font-semibold text-accent hover:opacity-70 transition-opacity"
                  >
                    {revealed[idx] ? '▲ Hide Answer' : '▼ Show Answer & Explanation'}
                  </button>
                  {revealed[idx] && q.explanation && (
                    <div className="mt-2 p-3 rounded-lg bg-accent/5 border border-accent/20 text-sm text-muted-foreground">
                      <span className="font-semibold text-foreground">Explanation: </span>
                      {q.explanation}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {isRunning && questions.length === 0 && (
        <div className="rounded-xl border border-border bg-card p-12 flex flex-col items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
          </div>
          <p className="text-muted-foreground text-sm">Building your quiz…</p>
        </div>
      )}
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const AnalysisStudio = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!documentId) return;
    api.get(`/api/v1/documents/${documentId}`)
      .then(res => setDoc(res.data.data))
      .catch(err => console.error('Failed to load doc', err))
      .finally(() => setLoading(false));
  }, [documentId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex flex-col gap-6">
      {/* Breadcrumb Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/documents')} className="shrink-0">
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground uppercase tracking-wide font-semibold">Analysis Studio</p>
          <h1 className="text-2xl font-serif font-bold text-foreground truncate">{doc?.title || 'Document Analysis'}</h1>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-2 shrink-0">
          {doc && (
            <>
              <span className="text-xs font-mono bg-muted px-2 py-1 rounded text-muted-foreground">{doc.doc_type}</span>
              {doc.status === 'COMPLETED'
                ? <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                : <Loader2 className="w-5 h-5 animate-spin text-amber-500" />}
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-0">
        <TabsList className="w-full h-auto bg-muted/50 border border-border rounded-xl p-1 flex flex-wrap gap-1">
          {[
            { value: 'overview',  label: 'Overview',  icon: <FileText className="w-4 h-4" /> },
            { value: 'artifacts', label: 'Artifacts', icon: <Layers className="w-4 h-4" /> },
            { value: 'summary',   label: 'Summary',   icon: <BookOpen className="w-4 h-4" /> },
            { value: 'quiz',      label: 'Quiz',      icon: <HelpCircle className="w-4 h-4" /> },
            { value: 'formulas',  label: 'Formulas',  icon: <FlaskConical className="w-4 h-4" /> },
          ].map(tab => (
            <TabsTrigger key={tab.value} value={tab.value}
              className="flex-1 gap-2 data-[state=active]:bg-card data-[state=active]:shadow-sm rounded-lg py-2 text-sm">
              {tab.icon} {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* ── Overview ── */}
        <TabsContent value="overview" className="mt-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { label: 'Title',       value: doc?.title },
              { label: 'Type',        value: doc?.doc_type },
              { label: 'Format',      value: doc?.format },
              { label: 'Status',      value: doc?.status },
              { label: 'File Size',   value: doc?.file_size_bytes ? `${Math.round(doc.file_size_bytes / 1024)} KB` : '—' },
              { label: 'Ingested At', value: doc?.created_at ? new Date(doc.created_at).toLocaleString() : '—' },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl border border-border bg-card p-4">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
                <p className="font-medium text-foreground">{value || '—'}</p>
              </div>
            ))}
          </div>
          {doc?.description && (
            <div className="mt-4 rounded-xl border border-border bg-card p-5">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Description</p>
              <p className="text-muted-foreground text-sm leading-relaxed">{doc.description}</p>
            </div>
          )}
        </TabsContent>

        {/* ── Artifacts ── */}
        <TabsContent value="artifacts" className="mt-5 space-y-3">
          <p className="text-sm text-muted-foreground mb-1">
            These are the structured JSON files extracted from the document during ingestion.
            Click any item to expand and inspect the raw data.
          </p>
          <ArtifactViewer documentId={documentId} artifactKey="entities"  label="Named Entities"   countLabel="entities" />
          <ArtifactViewer documentId={documentId} artifactKey="formulas"  label="Formulas"         countLabel="formulas" />
          <ArtifactViewer documentId={documentId} artifactKey="questions" label="Questions (PYQ)"  countLabel="questions" />
          <ArtifactViewer documentId={documentId} artifactKey="chunks"    label="Semantic Chunks"  countLabel="chunks" />
        </TabsContent>

        {/* ── Summary ── */}
        <TabsContent value="summary" className="mt-5">
          <AnalysisPanel
            title="Document Summary"
            description="AI-generated structured summary of key concepts, topics, and insights from this document."
            icon={<BookOpen className="w-5 h-5 text-accent" />}
            triggerFn={triggerSummarize}
            documentId={documentId}
          />
        </TabsContent>

        {/* ── Quiz ── */}
        <TabsContent value="quiz" className="mt-5">
          <QuizPanel documentId={documentId} />
        </TabsContent>

        {/* ── Formulas ── */}
        <TabsContent value="formulas" className="mt-5">
          <AnalysisPanel
            title="Formula Revision Sheet"
            description="Complete reference of all extracted formulas with variables, units, and related concepts from graph."
            icon={<FlaskConical className="w-5 h-5 text-rose-500" />}
            triggerFn={triggerFormulaRevision}
            documentId={documentId}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalysisStudio;
