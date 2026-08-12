import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle2, XCircle, Download, Eye, Zap } from 'lucide-react';
import { pollAnalysisJob, getAnalysisDownloadUrls } from '@/lib/analysisApi';

const STATUS_CONFIG = {
  PENDING:   { icon: <Loader2 className="w-4 h-4 animate-spin text-amber-500" />, label: 'Queued', color: 'text-amber-600 bg-amber-50 border-amber-200 dark:bg-amber-950/30 dark:border-amber-800' },
  RUNNING:   { icon: <Loader2 className="w-4 h-4 animate-spin text-blue-500" />, label: 'Running', color: 'text-blue-600 bg-blue-50 border-blue-200 dark:bg-blue-950/30 dark:border-blue-800' },
  COMPLETED: { icon: <CheckCircle2 className="w-4 h-4 text-emerald-500" />, label: 'Completed', color: 'text-emerald-600 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800' },
  FAILED:    { icon: <XCircle className="w-4 h-4 text-red-500" />, label: 'Failed', color: 'text-red-600 bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800' },
};

/**
 * AnalysisJobCard – shows a job's status, auto-polls, and exposes view/download actions.
 *
 * Props:
 *   initialJob     – { id, status, analysis_type, ... } from the API
 *   onResultReady  – called with { jsonUrl, mdUrl } when COMPLETED
 *   label          – display label e.g. "Summary"
 *   icon           – ReactNode
 */
const AnalysisJobCard = ({ initialJob, onResultReady, label, icon }) => {
  const [job, setJob] = useState(initialJob);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!job) return;
    if (job.status === 'PENDING' || job.status === 'RUNNING') {
      intervalRef.current = pollAnalysisJob(job.id, (updated) => {
        setJob(updated);
        if (updated.status === 'COMPLETED') {
          getAnalysisDownloadUrls(updated.id)
            .then(res => onResultReady?.(res.data.data))
            .catch(console.error);
        }
      });
    } else if (job.status === 'COMPLETED') {
      getAnalysisDownloadUrls(job.id)
        .then(res => onResultReady?.(res.data.data))
        .catch(console.error);
    }
    return () => clearInterval(intervalRef.current);
  }, [job?.id]);

  if (!job) return null;

  const config = STATUS_CONFIG[job.status] || STATUS_CONFIG.PENDING;

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg border ${config.color}`}>
      <div className="flex items-center gap-2.5">
        {icon && <span className="text-muted-foreground">{icon}</span>}
        <div>
          <p className="text-sm font-semibold">{label}</p>
          <p className="text-xs opacity-70">Job ID: {job.id?.slice(0, 8)}…</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full border ${config.color}`}>
          {config.icon} {config.label}
        </span>
      </div>
    </div>
  );
};

export default AnalysisJobCard;
