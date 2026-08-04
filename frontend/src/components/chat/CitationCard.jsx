import React from 'react';
import { Sigma, ImageIcon } from "lucide-react";

export const CitationCard = React.memo(({ cit, onCitationClick }) => {
  const isClickable = (cit.document_id && cit.document_id !== 'GRAPH') || cit.source_url;

  return (
    <div className="relative group">
      <div
        id={cit.citation_id}
        onClick={isClickable ? (e) => onCitationClick(e, cit) : undefined}
        className={`flex items-center gap-1.5 bg-background border border-border rounded-lg px-2.5 py-1.5 shadow-sm text-xs transition-all duration-200 hover:shadow-md select-none
          ${isClickable ? 'cursor-pointer hover:border-primary/50 hover:bg-primary/5' : 'cursor-default'}`}
      >
        <span className={`font-mono text-[10px] font-bold ${isClickable ? 'text-primary' : 'text-muted-foreground'}`}>
          [{cit.citation_id}]
        </span>
        <span
          className={`font-medium max-w-[160px] truncate ${isClickable ? 'text-foreground hover:underline' : 'text-muted-foreground'}`}
          title={cit.source_title}
        >
          {cit.source_title}
        </span>
        {cit.page_number && (
          <span className="text-muted-foreground font-normal text-[10px]">p.{cit.page_number}</span>
        )}
      </div>

      {/* Rich hover tooltip */}
      <div className="absolute bottom-full left-0 mb-2 hidden group-hover:flex flex-col z-50 w-80 bg-popover text-popover-foreground text-xs rounded-2xl shadow-2xl border border-border opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none overflow-hidden">
        {/* Tooltip header */}
        <div className="bg-muted px-4 py-3 border-b border-border flex items-start gap-3">
          <div className="flex flex-col gap-1 min-w-0">
            <div className="font-semibold text-foreground truncate">{cit.source_title}</div>
            {cit.page_number && (
              <span className="text-muted-foreground text-[10px]">· Page {cit.page_number}</span>
            )}
          </div>
        </div>

        {/* Equation block */}
        {cit.chunk_type === 'equation' && cit.raw_latex && (
          <div className="px-3 py-2 border-b border-border">
            <div className="text-[10px] text-primary font-semibold mb-1 flex items-center gap-1">
              <Sigma className="w-3 h-3" />
              {cit.equation_label ? `Equation (${cit.equation_label})` : 'Equation'}
            </div>
            <code className="block bg-muted/50 rounded-lg px-2 py-1.5 font-mono text-primary-foreground text-[11px] break-all leading-relaxed">
              {cit.raw_latex}
            </code>
          </div>
        )}

        {/* Figure image preview */}
        {cit.chunk_type === 'figure' && cit.image_url && (
          <div className="px-3 py-2 border-b border-border">
            <div className="text-[10px] text-primary font-semibold mb-1.5 flex items-center gap-1">
              <ImageIcon className="w-3 h-3" /> Figure Preview
            </div>
            <img
              src={cit.image_url}
              alt="Figure from document"
              className="w-full rounded-lg object-contain max-h-36 bg-muted"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          </div>
        )}

        {/* Text snippet */}
        {cit.chunk_type !== 'figure' && cit.chunk_type !== 'equation' && cit.snippet && (
          <div className="px-3 py-2.5 flex-1 min-w-0">
            <div className="text-[10px] text-muted-foreground font-semibold mb-1 uppercase tracking-wider">Snippet</div>
            <p className="line-clamp-4 leading-relaxed text-foreground">
              "{cit.snippet}"
            </p>
          </div>
        )}
      </div>
    </div>
  );
});
