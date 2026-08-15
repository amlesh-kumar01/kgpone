import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import {
  ArrowLeft, Loader2, BookOpen, HelpCircle, FlaskConical,
  Sparkles, RefreshCw, CheckCircle2, AlertCircle, GraduationCap,
  FileText, Search, ChevronDown, ChevronUp, TrendingUp, GitCompare, Layers
} from 'lucide-react';
import api from '@/lib/api';
import {
  triggerStudyUnitSummary, triggerQuiz, triggerFormulaRevision, triggerComparison,
  getAnalysisDownloadUrls, pollAnalysisJob, fetchArtifactMarkdown, fetchArtifactJson
} from '@/lib/analysisApi';
import MarkdownResult from '@/components/analysis/MarkdownResult';
import { StudioChatTab } from '@/components/chat/StudioChatTab';

// ─── Helpers ────────────────────────────────────────────────────────────────

const StatusBadge = ({ status }) => {
  const map = {
    COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-700',
    FAILED:    'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:border-red-700',
    RUNNING:   'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:border-blue-700',
    PENDING:   'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:border-amber-700',
  };
  const icons = {
    COMPLETED: <CheckCircle2 className="w-3 h-3" />,
    FAILED: <AlertCircle className="w-3 h-3" />,
    RUNNING: <Loader2 className="w-3 h-3 animate-spin" />,
    PENDING: <Loader2 className="w-3 h-3 animate-spin" />,
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${map[status] || map.PENDING}`}>
      {icons[status]} {status}
    </span>
  );
};

// ─── Stat Card ───────────────────────────────────────────────────────────────

const StatCard = ({ icon, label, value, color = 'accent' }) => (
  <div className="rounded-xl border border-border bg-card p-5 flex items-center gap-4">
    <div className={`w-11 h-11 rounded-xl bg-${color}/10 flex items-center justify-center shrink-0`}>
      {icon}
    </div>
    <div>
      <p className="text-2xl font-bold text-foreground font-mono">{value}</p>
      <p className="text-xs text-muted-foreground font-medium">{label}</p>
    </div>
  </div>
);

// ─── MD Analysis Panel ────────────────────────────────────────────────────────

const MdPanel = ({ title, description, icon, iconColor = 'text-accent', triggerFn, docIds, disabled = false }) => {
  const [job, setJob] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [mdContent, setMdContent] = useState(null);
  const [mdUrl, setMdUrl] = useState(null);
  const intervalRef = useRef(null);
  const { toast } = useToast();

  const handleTrigger = async () => {
    if (!docIds?.length) return;
    setTriggering(true);
    try {
      const res = await triggerFn(docIds);
      const newJob = { id: res.data.data.analysis_id, status: 'PENDING' };
      setJob(newJob);
      toast({ title: `${title} started!` });

      intervalRef.current = pollAnalysisJob(newJob.id, async (updated) => {
        setJob(updated);
        if (updated.status === 'COMPLETED') {
          try {
            const dlRes = await getAnalysisDownloadUrls(updated.id);
            const url = dlRes.data.data?.md_url;
            setMdUrl(url);
            if (url) {
              const text = await fetchArtifactMarkdown(url);
              setMdContent(text);
            }
          } catch (e) { console.error(e); }
        }
      });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Failed', description: err.response?.data?.message || err.message });
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => () => clearInterval(intervalRef.current), []);

  const isRunning = job?.status === 'PENDING' || job?.status === 'RUNNING';

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-border bg-gradient-to-br from-card to-muted/30 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-accent/15 flex items-center justify-center shrink-0 mt-0.5">
              <span className={iconColor}>{icon}</span>
            </div>
            <div>
              <h3 className="font-serif font-bold text-foreground text-lg">{title}</h3>
              <p className="text-muted-foreground text-sm mt-0.5">{description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {job && <StatusBadge status={job.status} />}
            <Button onClick={handleTrigger} disabled={triggering || isRunning || disabled} size="sm"
              className="bg-accent text-accent-foreground hover:bg-accent/90 gap-2 min-w-[130px]">
              {triggering || isRunning
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Processing…</>
                : mdContent
                  ? <><RefreshCw className="w-4 h-4" /> Regenerate</>
                  : <><Sparkles className="w-4 h-4" /> Generate</>}
            </Button>
          </div>
        </div>
        {disabled && (
          <p className="mt-3 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-700 rounded-lg px-3 py-2">
            Select a study_unit offering above to enable this feature.
          </p>
        )}
      </div>

      {mdContent && <MarkdownResult content={mdContent} downloadUrl={mdUrl} downloadLabel={`Download ${title}`} />}

      {isRunning && !mdContent && (
        <div className="rounded-xl border border-border bg-card p-12 flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-accent" />
          </div>
          <p className="text-muted-foreground text-sm">AI is working across your documents…</p>
          <p className="text-xs text-muted-foreground/60">This may take up to a minute.</p>
        </div>
      )}
    </div>
  );
};

// ─── StudyUnit Quiz Panel ────────────────────────────────────────────────────────

const StudyUnitQuizPanel = ({ docIds, disabled }) => {
  const [jobs, setJobs] = useState([]);
  const [triggering, setTriggering] = useState(false);
  const [allQuestions, setAllQuestions] = useState([]);
  const [revealed, setRevealed] = useState({});
  const [filter, setFilter] = useState('');
  const { toast } = useToast();
  const intervalsRef = useRef([]);

  const handleTrigger = async () => {
    if (!docIds?.length) return;
    setTriggering(true);
    setAllQuestions([]);
    setRevealed({});

    try {
      const newJobs = [];
      for (const docId of docIds) {
        const res = await triggerQuiz(docId);
        newJobs.push({ id: res.data.data.analysis_id, status: 'PENDING', docId });
      }
      setJobs(newJobs);
      toast({ title: `Generating quiz for ${docIds.length} documents…` });

      const collectedQuestions = [];
      for (const j of newJobs) {
        const interval = pollAnalysisJob(j.id, async (updated) => {
          setJobs(prev => prev.map(jb => jb.id === j.id ? { ...jb, status: updated.status } : jb));
          if (updated.status === 'COMPLETED') {
            try {
              const dlRes = await getAnalysisDownloadUrls(updated.id);
              const jsonUrl = dlRes.data.data?.json_url;
              if (jsonUrl) {
                const quizData = await fetchArtifactJson(jsonUrl);
                const qs = (quizData.questions || []).map(q => ({ ...q, _docId: j.docId }));
                collectedQuestions.push(...qs);
                setAllQuestions([...collectedQuestions]);
              }
            } catch (e) { console.error(e); }
          }
        });
        intervalsRef.current.push(interval);
      }
    } catch (err) {
      toast({ variant: 'destructive', title: 'Failed', description: err.message });
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => () => intervalsRef.current.forEach(clearInterval), []);

  const toggleReveal = (idx) => setRevealed(prev => ({ ...prev, [idx]: !prev[idx] }));
  const revealedCount = Object.values(revealed).filter(Boolean).length;
  const progress = allQuestions.length > 0 ? Math.round((revealedCount / allQuestions.length) * 100) : 0;

  const filtered = filter
    ? allQuestions.filter(q => q.question_text?.toLowerCase().includes(filter.toLowerCase()))
    : allQuestions;

  const anyRunning = jobs.some(j => j.status === 'PENDING' || j.status === 'RUNNING');

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-border bg-gradient-to-br from-card to-muted/30 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-purple-500/15 flex items-center justify-center shrink-0">
              <HelpCircle className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <h3 className="font-serif font-bold text-foreground text-lg">Master Quiz Bank</h3>
              <p className="text-muted-foreground text-sm">Comprehensive MCQs generated from all study_unit documents</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button onClick={handleTrigger} disabled={triggering || anyRunning || disabled} size="sm"
              className="bg-purple-600 hover:bg-purple-700 text-white gap-2 min-w-[130px]">
              {triggering || anyRunning
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</>
                : allQuestions.length ? <><RefreshCw className="w-4 h-4" /> Regenerate</>
                : <><Sparkles className="w-4 h-4" /> Generate All</>}
            </Button>
          </div>
        </div>
        {jobs.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {jobs.map((j, i) => <StatusBadge key={i} status={j.status} />)}
          </div>
        )}
      </div>

      {allQuestions.length > 0 && (
        <>
          {/* Progress */}
          <div className="rounded-xl border border-border bg-card p-4">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium text-foreground flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-accent" /> Study Progress
              </p>
              <p className="text-sm text-muted-foreground">{revealedCount} / {allQuestions.length} answered</p>
            </div>
            <div className="h-2.5 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-purple-500 to-accent rounded-full transition-all duration-700"
                style={{ width: `${progress}%` }} />
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input placeholder="Search questions…" className="pl-9" value={filter} onChange={e => setFilter(e.target.value)} />
          </div>

          {/* Questions */}
          <div className="space-y-3">
            {filtered.map((q, idx) => (
              <div key={idx} className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start gap-3">
                    <span className="w-7 h-7 rounded-full bg-purple-500/10 flex items-center justify-center text-xs font-bold text-purple-600 shrink-0 mt-0.5">
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
                          <div key={oi} className={`flex items-start gap-2 p-3 rounded-lg border text-sm transition-all ${
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
                  <button onClick={() => toggleReveal(idx)}
                    className="text-xs font-semibold text-purple-600 hover:opacity-70 transition-opacity dark:text-purple-400">
                    {revealed[idx] ? '▲ Hide Answer' : '▼ Show Answer & Explanation'}
                  </button>
                  {revealed[idx] && q.explanation && (
                    <div className="mt-2 p-3 rounded-lg bg-purple-500/5 border border-purple-500/20 text-sm text-muted-foreground">
                      <span className="font-semibold text-foreground">Explanation: </span>{q.explanation}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// ─── Formula Bank Panel ───────────────────────────────────────────────────────

const FormulaBankPanel = ({ docIds, disabled }) => {
  const [jobs, setJobs] = useState([]);
  const [triggering, setTriggering] = useState(false);
  const [allFormulas, setAllFormulas] = useState([]);
  const [search, setSearch] = useState('');
  const { toast } = useToast();
  const intervalsRef = useRef([]);

  const handleTrigger = async () => {
    if (!docIds?.length) return;
    setTriggering(true);
    setAllFormulas([]);
    try {
      const newJobs = [];
      for (const docId of docIds) {
        const res = await triggerFormulaRevision(docId);
        newJobs.push({ id: res.data.data.analysis_id, status: 'PENDING', docId });
      }
      setJobs(newJobs);
      toast({ title: `Generating formula bank for ${docIds.length} documents…` });

      const collected = [];
      for (const j of newJobs) {
        const interval = pollAnalysisJob(j.id, async (updated) => {
          setJobs(prev => prev.map(jb => jb.id === j.id ? { ...jb, status: updated.status } : jb));
          if (updated.status === 'COMPLETED') {
            try {
              const dlRes = await getAnalysisDownloadUrls(updated.id);
              const jsonUrl = dlRes.data.data?.json_url;
              if (jsonUrl) {
                const data = await fetchArtifactJson(jsonUrl);
                const fs = (data.formulas || []);
                collected.push(...fs);
                setAllFormulas([...collected]);
              }
            } catch (e) { console.error(e); }
          }
        });
        intervalsRef.current.push(interval);
      }
    } catch (err) {
      toast({ variant: 'destructive', title: 'Failed', description: err.message });
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => () => intervalsRef.current.forEach(clearInterval), []);

  const anyRunning = jobs.some(j => j.status === 'PENDING' || j.status === 'RUNNING');
  const filtered = search
    ? allFormulas.filter(f => f.name?.toLowerCase().includes(search.toLowerCase()) || f.equation?.toLowerCase().includes(search.toLowerCase()))
    : allFormulas;

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-border bg-gradient-to-br from-card to-muted/30 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-rose-500/15 flex items-center justify-center shrink-0">
              <FlaskConical className="w-5 h-5 text-rose-500" />
            </div>
            <div>
              <h3 className="font-serif font-bold text-foreground text-lg">Formula Bank</h3>
              <p className="text-muted-foreground text-sm">Searchable reference of all formulas across the study_unit</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button onClick={handleTrigger} disabled={triggering || anyRunning || disabled} size="sm"
              className="bg-rose-600 hover:bg-rose-700 text-white gap-2 min-w-[130px]">
              {triggering || anyRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</>
                : allFormulas.length ? <><RefreshCw className="w-4 h-4" /> Regenerate</>
                : <><Sparkles className="w-4 h-4" /> Build Bank</>}
            </Button>
          </div>
        </div>
      </div>

      {allFormulas.length > 0 && (
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input placeholder="Search formulas…" className="pl-9" value={search} onChange={e => setSearch(e.target.value)} />
          </div>

          <div className="grid grid-cols-1 gap-4">
            {filtered.map((f, idx) => (
              <div key={idx} className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start gap-4">
                    <div className="w-9 h-9 rounded-lg bg-rose-500/10 flex items-center justify-center shrink-0 mt-0.5">
                      <FlaskConical className="w-4 h-4 text-rose-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-foreground">{f.name || `Formula ${idx + 1}`}</h4>
                      {f.equation && (
                        <div className="mt-2 p-3 bg-muted/50 rounded-lg font-mono text-sm text-foreground border border-border">
                          {f.equation}
                        </div>
                      )}
                      {f.description && (
                        <p className="mt-2 text-sm text-muted-foreground">{f.description}</p>
                      )}
                      {f.variables && f.variables.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {f.variables.map((v, vi) => (
                            <span key={vi} className="inline-flex items-center gap-1 bg-accent/10 text-accent px-2 py-1 rounded text-xs font-mono">
                              <span className="font-bold">{v.symbol}</span>
                              {v.description && <span className="text-muted-foreground">— {v.description}</span>}
                            </span>
                          ))}
                        </div>
                      )}
                      {f.related_concepts_graph && f.related_concepts_graph.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {f.related_concepts_graph.map((c, ci) => (
                            <span key={ci} className="text-xs bg-muted px-2 py-0.5 rounded-full text-muted-foreground">
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {anyRunning && allFormulas.length === 0 && (
        <div className="rounded-xl border border-border bg-card p-12 flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-rose-500/10 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-rose-500" />
          </div>
          <p className="text-muted-foreground text-sm">Extracting formulas from all documents…</p>
        </div>
      )}
    </div>
  );
};

// ─── PYQ Panel ────────────────────────────────────────────────────────────────

const PYQPanel = ({ documents }) => {
  const pyqDocs = (documents || []).filter(d => d.doc_type === 'PYQ');
  const [expanded, setExpanded] = useState({});
  const [allQuestions, setAllQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!pyqDocs.length) return;
    setLoading(true);
    Promise.all(
      pyqDocs.map(doc =>
        api.get(`/api/v1/documents/${doc.id}/artifacts/questions`)
          .then(res => ({ docId: doc.id, docTitle: doc.title, questions: res.data.data?.questions || [] }))
          .catch(() => ({ docId: doc.id, docTitle: doc.title, questions: [] }))
      )
    ).then(results => {
      const all = results.flatMap(r => r.questions.map(q => ({ ...q, _docTitle: r.docTitle })));
      setAllQuestions(all);
    }).finally(() => setLoading(false));
  }, [pyqDocs.length]);

  const filtered = search ? allQuestions.filter(q => q.question_text?.toLowerCase().includes(search.toLowerCase())) : allQuestions;

  if (!pyqDocs.length) {
    return (
      <div className="rounded-xl border border-border bg-card p-12 text-center">
        <GraduationCap className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
        <p className="text-muted-foreground font-medium">No PYQ documents found in this offering.</p>
        <p className="text-xs text-muted-foreground mt-1">Upload documents with type "PYQ" to see past year questions here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-serif font-bold text-foreground text-lg">Past Year Questions</h3>
          <p className="text-muted-foreground text-sm">{pyqDocs.length} PYQ document(s) · {allQuestions.length} questions extracted</p>
        </div>
      </div>

      {loading ? (
        <div className="p-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-accent" /></div>
      ) : (
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input placeholder="Search questions…" className="pl-9" value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="space-y-3">
            {filtered.map((q, idx) => (
              <div key={idx} className="rounded-xl border border-border bg-card p-4">
                <div className="flex items-start gap-3">
                  <span className="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center text-xs font-bold text-accent shrink-0 mt-0.5">{idx + 1}</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{q.question_text}</p>
                    <div className="mt-1.5 flex flex-wrap gap-2">
                      {q.question_type && <span className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full dark:bg-blue-950/30 dark:border-blue-700 dark:text-blue-300">{q.question_type}</span>}
                      {q.marks && <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">{q.marks} marks</span>}
                      {q.year && <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">{q.year}</span>}
                      <span className="text-xs text-muted-foreground/60">from: {q._docTitle}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const StudyUnitAnalysisStudio = () => {
  const { study_unitId } = useParams();
  const navigate = useNavigate();
  const [study_unit, setStudyUnit] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const [selectedDocIds, setSelectedDocIds] = useState(new Set());

  useEffect(() => {
    if (!study_unitId) return;
    api.get(`/api/v1/academic/${study_unitId}`)
      .then(res => setStudyUnit(res.data.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [study_unitId]);

  useEffect(() => {
    if (!study_unitId) { setDocuments([]); return; }
    setLoadingDocs(true);
    api.get(`/api/v1/documents/study-unit/${study_unitId}`)
      .then(res => {
        const docs = res.data.data || [];
        setDocuments(docs);
        // Default select all completed docs
        const completedIds = docs.filter(d => d.status === 'COMPLETED').map(d => d.id);
        setSelectedDocIds(new Set(completedIds));
      })
      .catch(() => setDocuments([]))
      .finally(() => setLoadingDocs(false));
  }, [study_unitId]);

  const toggleDocSelection = (docId) => {
    setSelectedDocIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(docId)) {
        newSet.delete(docId);
      } else {
        newSet.add(docId);
      }
      return newSet;
    });
  };

  const activeDocIds = Array.from(selectedDocIds);
  const hasDocuments = activeDocIds.length > 0;

  // Aggregate stats
  const totalDocs = documents.length;
  const completedDocs = documents.filter(d => d.status === 'COMPLETED').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Ultra-compact Header */}
      <div className="flex items-center gap-3 border-b border-border bg-card px-4 py-2 shrink-0">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="h-8 w-8 shrink-0 rounded-full hover:bg-muted">
          <ArrowLeft className="w-4 h-4 text-muted-foreground" />
        </Button>
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-accent" />
          <h1 className="text-base font-serif font-bold text-foreground">
            {study_unit?.code ? <span className="text-accent">{study_unit.code}</span> : ''} {study_unit?.code ? '—' : ''} {study_unit?.title || 'Studio'}
          </h1>
        </div>
      </div>

      <div className="flex-1 overflow-hidden p-4">
        {/* Sidebar Layout */}
        <Tabs defaultValue="overview" className="flex flex-col md:flex-row gap-6 items-start h-full" orientation="vertical">
          <TabsList className="flex flex-col h-fit w-full md:w-60 shrink-0 bg-card border border-border rounded-xl p-2 space-y-1">
            <div className="px-3 py-2 mb-1 border-b border-border">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Analysis Tools</p>
            </div>
            {[
              { value: 'overview',  label: 'Document Selector', icon: <Layers className="w-4 h-4" /> },
              { value: 'assistant', label: 'AI Tutor',       icon: <Sparkles className="w-4 h-4 text-purple-500" /> },
              { value: 'summary',   label: 'StudyUnit Summary', icon: <BookOpen className="w-4 h-4" /> },
              { value: 'quiz',      label: 'Quiz Bank',      icon: <HelpCircle className="w-4 h-4" /> },
              { value: 'formulas',  label: 'Formula Bank',   icon: <FlaskConical className="w-4 h-4" /> },
              { value: 'pyq',       label: 'PYQ Patterns',   icon: <GraduationCap className="w-4 h-4" /> },
              { value: 'compare',   label: 'Compare Docs',   icon: <GitCompare className="w-4 h-4" /> },
            ].map(tab => (
              <TabsTrigger key={tab.value} value={tab.value}
                className="w-full flex items-center justify-start gap-3 py-2.5 px-3 data-[state=active]:bg-accent/10 data-[state=active]:text-accent hover:bg-muted rounded-lg text-sm font-medium transition-colors">
                {tab.icon} <span>{tab.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="flex-1 w-full h-full min-w-0 bg-transparent overflow-y-auto pr-2 custom-scrollbar">
            {/* ── Overview ── */}
            <TabsContent value="overview" className="mt-0 h-full outline-none">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <StatCard icon={<FileText className="w-5 h-5 text-accent" />} label="Total Documents" value={loadingDocs ? '…' : totalDocs} />
                <StatCard icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />} label="Processed" value={loadingDocs ? '…' : completedDocs} color="emerald-500" />
                <StatCard icon={<HelpCircle className="w-5 h-5 text-purple-500" />} label="PYQ Docs" value={loadingDocs ? '…' : documents.filter(d => d.doc_type === 'PYQ').length} color="purple-500" />
                <StatCard icon={<GraduationCap className="w-5 h-5 text-blue-500" />} label="Selected for Analysis" value={loadingDocs ? '…' : activeDocIds.length} color="blue-500" />
              </div>
          {loadingDocs ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 animate-spin text-accent" />
            </div>
          ) : documents.length === 0 ? (
            <div className="rounded-xl border border-border bg-card p-12 text-center">
              <FileText className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-muted-foreground font-medium">No documents in this Study Unit yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-muted/30 p-4 rounded-xl border border-border flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-foreground">Select Documents for Analysis</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">The AI tools in the other tabs will only analyze the documents you select here.</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium bg-accent/10 text-accent px-3 py-1 rounded-full">{activeDocIds.length} selected</span>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {documents.map(doc => {
                  const isCompleted = doc.status === 'COMPLETED';
                  const isSelected = selectedDocIds.has(doc.id);
                  return (
                    <div 
                      key={doc.id} 
                      className={`rounded-xl border p-4 flex items-start gap-4 transition-all ${
                        isSelected ? 'border-accent bg-accent/5 ring-1 ring-accent' : 'border-border bg-card hover:bg-muted/50'
                      } ${!isCompleted ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
                      onClick={() => isCompleted && toggleDocSelection(doc.id)}
                    >
                      <div className="pt-1">
                        <input 
                          type="checkbox"
                          className="w-5 h-5 rounded border-border text-accent focus:ring-accent accent-accent bg-card cursor-pointer disabled:cursor-not-allowed"
                          checked={isSelected} 
                          disabled={!isCompleted}
                          onChange={() => isCompleted && toggleDocSelection(doc.id)}
                        />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex justify-between items-start gap-2">
                          <p className={`font-semibold truncate ${isSelected ? 'text-accent' : 'text-foreground'}`}>{doc.title}</p>
                        </div>
                        <div className="flex items-center gap-3 mt-2">
                          <span className="text-xs font-mono bg-muted text-muted-foreground px-2 py-0.5 rounded">{doc.doc_type}</span>
                          <span className={`text-[10px] uppercase font-bold tracking-wider ${isCompleted ? 'text-emerald-500' : 'text-amber-500'}`}>
                            {isCompleted ? 'Ready' : 'Processing'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          </TabsContent>

          {/* ── StudyUnit Summary ── */}
          <TabsContent value="summary" className="mt-0 outline-none">
          <MdPanel
            title="StudyUnit Summary"
            description={`Synthesizes all ${activeDocIds.length} selected documents into a unified study overview with learning path.`}
            icon={<BookOpen className="w-5 h-5" />}
            iconColor="text-accent"
            triggerFn={triggerStudyUnitSummary}
            docIds={activeDocIds}
            disabled={!hasDocuments}
          />
          </TabsContent>

          {/* ── Quiz Bank ── */}
          <TabsContent value="quiz" className="mt-0 outline-none">
            <StudyUnitQuizPanel docIds={activeDocIds} disabled={!hasDocuments} />
          </TabsContent>

          {/* ── Formula Bank ── */}
          <TabsContent value="formulas" className="mt-0 outline-none">
            <FormulaBankPanel docIds={activeDocIds} disabled={!hasDocuments} />
          </TabsContent>

          {/* ── PYQ ── */}
          <TabsContent value="pyq" className="mt-0 outline-none">
            <PYQPanel documents={documents} />
          </TabsContent>

          {/* ── Compare ── */}
          <TabsContent value="compare" className="mt-0 outline-none">
          <MdPanel
            title="Document Comparison"
            description="AI diff of concepts and formulas between all selected documents — find gaps in your study materials."
            icon={<GitCompare className="w-5 h-5" />}
            iconColor="text-blue-500"
            triggerFn={triggerComparison}
            docIds={activeDocIds.slice(0, 2)}
            disabled={activeDocIds.length < 2}
          />
          {activeDocIds.length < 2 && activeDocIds.length > 0 && (
            <p className="text-xs text-amber-600 mt-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-700 px-4 py-2 rounded-lg">
              At least 2 selected documents are needed for comparison. Currently: {activeDocIds.length}.
            </p>
          )}
          </TabsContent>

          {/* ── Assistant ── */}
          <TabsContent value="assistant" className="mt-0 h-full outline-none">
            <div className="h-full pb-4">
              <StudioChatTab 
                studyUnitId={study_unit?.id} 
                studyUnitCode={study_unit?.code} 
              />
            </div>
          </TabsContent>
        </div>
      </Tabs>
      </div>
    </div>
  );
};

export default StudyUnitAnalysisStudio;
