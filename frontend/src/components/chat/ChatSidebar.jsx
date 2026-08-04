import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronLeft, Sparkles, Settings as SettingsIcon, ChevronDown, MessageSquare, Zap, Brain, Globe, Key, Lock, Eye, EyeOff, Trash2, Plus } from "lucide-react";

export const ChatSidebar = ({
  navigate,
  departments,
  filteredCourses,
  offerings,
  selectedDeptId,
  setSelectedDeptId,
  selectedCourseId,
  setSelectedCourseId,
  selectedOfferingId,
  setSelectedOfferingId,
  useCitations,
  setUseCitations,
  analysisMode,
  setAnalysisMode,
  byokProvider,
  setByokProvider,
  byokModel,
  setByokModel,
  byokKey,
  setByokKey,
  setMemoriesOpen,
  clearMemories,
  conversations,
  activeConversationId,
  loadConversation,
  createNewChat,
  deleteConversation,
  isConversationsLoading,
  CHUNK_TYPE_CONFIG
}) => {
  return (
    <div className="w-full md:w-72 shrink-0 flex flex-col bg-card/80 text-card-foreground backdrop-blur-md rounded-2xl border border-border shadow-sm p-4 overflow-y-auto no-scrollbar">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border shrink-0">
        <Button
          variant="ghost" size="icon"
          onClick={() => navigate(-1)}
          className="h-8 w-8 rounded-full hover:bg-accent hover:text-accent-foreground shrink-0"
        >
          <ChevronLeft className="w-5 h-5 text-muted-foreground" />
        </Button>
        <div className="p-2 bg-gradient-to-br from-primary/20 to-primary/5 rounded-lg text-primary shadow-sm border border-primary/10">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-sm font-bold leading-none mb-1 text-foreground">KnowledgeOS</h1>
          <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Academic Tutor</p>
        </div>
      </div>

            <div className="pt-4 mt-2 border-t border-border">
              <div className="flex flex-col gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full text-muted-foreground hover:text-foreground justify-center text-[11px]"
                  onClick={() => setMemoriesOpen(true)}
                >
                  <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                  View AI Memory
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 border-red-200 dark:border-red-900/50 justify-center text-[11px]"
                  onClick={clearMemories}
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                  Clear AI Memory
                </Button>
              </div>
              <p className="text-[10px] text-muted-foreground mt-2 text-center px-1 leading-tight">
                Manage the facts the assistant has learned about you.
              </p>
            </div>

      {/* ── Recent Chats ───────────────────────────────────────────── */}
      <div className="flex flex-col gap-2 flex-1 min-h-0 pt-4">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
            <MessageSquare size={14} className="text-muted-foreground" /> Recent Chats
          </h2>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded hover:bg-accent"
            onClick={createNewChat}
            title="New Chat"
          >
            <Plus className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto no-scrollbar space-y-1 pr-1">
          {isConversationsLoading ? (
            <div className="space-y-2">
              <div className="h-8 w-full bg-muted/60 animate-pulse rounded-lg"></div>
              <div className="h-8 w-[90%] bg-muted/60 animate-pulse rounded-lg"></div>
              <div className="h-8 w-[95%] bg-muted/60 animate-pulse rounded-lg"></div>
              <div className="h-8 w-[85%] bg-muted/60 animate-pulse rounded-lg"></div>
            </div>
          ) : conversations.length === 0 ? (
            <p className="text-[11px] text-muted-foreground py-2 text-center">No recent chats</p>
          ) : (
            conversations.map(conv => (
              <div key={conv.id} className="relative group">
                <button
                  onClick={() => loadConversation(conv.id)}
                  className={`w-full text-left px-2 py-2 pr-8 text-[12px] rounded-lg transition-all truncate border ${
                    activeConversationId === conv.id
                      ? 'bg-primary/10 border-primary/20 text-primary font-medium dark:bg-primary/20 dark:text-primary-foreground'
                      : 'bg-transparent border-transparent text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  {conv.title || 'Untitled Conversation'}
                </button>
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Delete Chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-col gap-2 pt-4 border-t border-border">
        <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Source Types</h2>
        {Object.entries(CHUNK_TYPE_CONFIG).map(([type, cfg]) => {
          const Icon = cfg.icon;
          return (
            <div key={type} className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[9px] font-bold ${cfg.color}`}>
                <Icon className="w-2.5 h-2.5" /> {cfg.label}
              </span>
              <span className="text-[11px] text-muted-foreground capitalize">{type.replace('_', ' ')}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
