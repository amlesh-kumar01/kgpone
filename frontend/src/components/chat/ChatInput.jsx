import React from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, Brain, Lock } from "lucide-react";

export const ChatInput = ({ 
  input, 
  setInput, 
  handleSubmit, 
  isLoading, 
  selectedCourseId, 
  analysisMode, 
  byokKey 
}) => {
  return (
    <div className="pt-4 pb-2 shrink-0">
      <form onSubmit={handleSubmit} className="flex items-end gap-3 max-w-4xl mx-auto">
        <div className="relative flex-1 bg-card text-foreground rounded-3xl shadow-sm border border-border/80 focus-within:ring-4 focus-within:ring-primary/10 focus-within:border-primary/30 transition-all duration-300">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={selectedCourseId ? 'Ask about the selected course...' : 'Ask about a topic, prerequisites, formulas, or figures...'}
            className="py-4 px-6 h-auto min-h-[60px] text-[15px] bg-transparent border-none shadow-none focus-visible:ring-0 resize-none rounded-3xl"
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { 
                e.preventDefault(); 
                if (input.trim() && !isLoading) handleSubmit(e); 
              }
            }}
          />
        </div>
        <Button
          type="submit"
          size="icon"
          disabled={!input.trim() || isLoading}
          className="h-[60px] w-[60px] rounded-3xl shadow-md shrink-0 bg-primary hover:bg-primary/90 transition-all duration-200 hover:scale-[1.04] active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
        >
          <Send className="w-5 h-5 ml-0.5" />
        </Button>
      </form>
      <div className="flex items-center justify-between mt-3 px-1">
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
          <Bot className="w-3.5 h-3.5" />
          <span>AI responses may be inaccurate.</span>
        </div>
        <div className="flex items-center gap-1.5">
          {analysisMode === 'advanced' && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-violet-100 to-pink-100 dark:from-violet-900/30 dark:to-pink-900/30 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800">
              <Brain className="w-2.5 h-2.5" /> Agent
            </span>
          )}
          {byokKey && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
              <Lock className="w-2.5 h-2.5" /> BYOK
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
