import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Sparkles, Trash2 } from "lucide-react";
import api from '@/lib/api';

export const MemoryViewerDialog = ({ open, onOpenChange, memories, setMemories, activeConversationId }) => {
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (open) {
      const fetchMemories = async () => {
        try {
          setIsLoading(true);
          const response = await api.get('/api/v1/chat/memories');
          setMemories(response.data || []);
        } catch (error) {
          console.error("Failed to fetch memories:", error);
        } finally {
          setIsLoading(false);
        }
      };
      fetchMemories();
    }
  }, [open, setMemories, activeConversationId]);

  const deleteMemory = async (memoryId) => {
    try {
      await api.delete(`/api/v1/chat/memories/${memoryId}`);
      setMemories(prev => prev.filter(m => m.id !== memoryId));
    } catch (error) {
      console.error("Failed to delete memory:", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md max-h-[80vh] flex flex-col p-0 overflow-hidden bg-[#fdfaf6] dark:bg-slate-900 border-none rounded-xl shadow-2xl">
        <DialogHeader className="px-6 py-4 border-b border-slate-200/50 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur shrink-0">
          <DialogTitle className="flex items-center gap-2 text-foreground font-bold text-lg font-serif">
            <Sparkles className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            AI Memory
          </DialogTitle>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
          <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
            These are the facts the assistant has learned about you across all conversations to personalize its responses.
          </p>

          {isLoading ? (
            <div className="flex flex-col gap-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 rounded-xl bg-slate-100 dark:bg-slate-800/50 animate-pulse" />
              ))}
            </div>
          ) : memories.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center bg-white/50 dark:bg-slate-800/20 rounded-2xl border border-slate-100 dark:border-slate-800">
              <Sparkles className="w-10 h-10 text-muted-foreground mb-4" />
              <p className="text-foreground font-medium">No memories found</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
                The assistant hasn't learned any specific facts about you yet.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {memories.map((mem) => (
                <div 
                  key={mem.id} 
                  className="group flex items-start justify-between gap-4 p-4 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <p className="text-sm text-foreground leading-relaxed font-medium">
                    {mem.fact}
                  </p>
                  <button
                    onClick={() => deleteMemory(mem.id)}
                    className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md opacity-0 group-hover:opacity-100 transition-all shrink-0 mt-0.5"
                    title="Forget this fact"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
