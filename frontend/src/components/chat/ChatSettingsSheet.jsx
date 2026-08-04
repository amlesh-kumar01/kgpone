import React, { useState } from 'react';
import { useTheme } from '../../context/ThemeContext';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Settings2, Key, Lock, Eye, EyeOff, ChevronDown } from "lucide-react";

export const ChatSettingsSheet = ({
  open,
  onOpenChange,
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
  byokProvider,
  setByokProvider,
  byokModel,
  setByokModel,
  byokKey,
  setByokKey,
}) => {
  const [byokOpen, setByokOpen] = useState(false);
  const [byokKeyVisible, setByokKeyVisible] = useState(false);
  const { theme, setTheme } = useTheme();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[300px] sm:w-[400px] overflow-y-auto border-l border-border bg-background/95 backdrop-blur-md">
        <SheetHeader className="mb-6">
          <SheetTitle className="flex items-center gap-2 text-foreground">
            <Settings2 className="w-5 h-5 text-primary" />
            Chat Settings
          </SheetTitle>
          <SheetDescription>Configure your course context and API keys.</SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-6">
          {/* Filters */}
          <div className="flex flex-col gap-3">
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Course Context</h3>
            <Select value={selectedDeptId} onValueChange={(val) => {
              setSelectedDeptId(val === 'all' ? '' : val);
              setSelectedCourseId('');
              setSelectedOfferingId('');
            }}>
              <SelectTrigger className="h-10 text-sm rounded-lg bg-muted border-border shadow-sm focus:ring-2 focus:ring-primary/20">
                <SelectValue placeholder="1. Department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Department</SelectItem>
                {departments.map(d => <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>)}
              </SelectContent>
            </Select>

            <Select value={selectedCourseId} onValueChange={(val) => {
              setSelectedCourseId(val === 'all' ? '' : val);
              setSelectedOfferingId('');
            }} disabled={!selectedDeptId}>
              <SelectTrigger className="h-10 text-sm rounded-lg bg-muted border-border shadow-sm focus:ring-2 focus:ring-primary/20">
                <SelectValue placeholder="2. Course" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Course</SelectItem>
                {filteredCourses.map(c => <SelectItem key={c.id} value={c.id}>{c.code} - {c.title}</SelectItem>)}
              </SelectContent>
            </Select>

            <Select
              value={selectedOfferingId}
              onValueChange={(val) => setSelectedOfferingId(val === 'all' ? '' : val)}
              disabled={!selectedCourseId || offerings.length === 0}
            >
              <SelectTrigger className="h-10 text-sm rounded-lg bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 shadow-sm focus:ring-2 focus:ring-primary/20">
                <SelectValue placeholder={offerings.length === 0 && selectedCourseId ? 'No offerings' : '3. Offering'} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Offering</SelectItem>
                {offerings.map(o => <SelectItem key={o.id} value={o.id}>{o.semester} {o.year}</SelectItem>)}
              </SelectContent>
            </Select>
            
            <div className="pt-2">
              <label className="text-sm font-medium text-foreground flex items-center cursor-pointer select-none hover:text-primary transition-colors">
                <input
                  type="checkbox"
                  checked={useCitations}
                  onChange={(e) => setUseCitations(e.target.checked)}
                  className="mr-3 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary transition-all shadow-sm"
                />
                Enable Inline Citations
              </label>
            </div>
          </div>

          <div className="h-px bg-border w-full" />

          {/* Theme Selector */}
          <div className="flex flex-col gap-3">
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Appearance</h3>
            <Select value={theme} onValueChange={setTheme}>
              <SelectTrigger className="h-10 text-sm rounded-lg bg-muted border-border shadow-sm focus:ring-2 focus:ring-primary/20">
                <SelectValue placeholder="Select Theme" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="system">System Default</SelectItem>
                <SelectItem value="light">Light Mode</SelectItem>
                <SelectItem value="dark">Dark Mode (Neutral)</SelectItem>
                <SelectItem value="slate">Dark Mode (Slate)</SelectItem>
                <SelectItem value="black">Dark Mode (Black)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="h-px bg-border w-full" />

          {/* BYOK Settings */}
          <div className="flex flex-col gap-2">
            <button
              onClick={() => setByokOpen(o => !o)}
              className="flex items-center justify-between w-full group py-1"
            >
              <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5 group-hover:text-foreground transition-colors">
                <Key size={14} className="text-muted-foreground" /> Bring Your Own Key
                {byokKey && (
                  <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400 ml-1">
                    <Lock className="w-3 h-3" />
                  </span>
                )}
              </h3>
              <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform duration-200 ${byokOpen ? 'rotate-180' : ''}`} />
            </button>

            {byokOpen && (
              <div className="kgp-byok-open flex flex-col gap-3 mt-2 bg-muted/60 rounded-xl p-3 border border-border">
                <div className="flex flex-col gap-1.5">
                  <Select value={byokProvider} onValueChange={(val) => { setByokProvider(val); setByokModel(''); }}>
                    <SelectTrigger className="h-9 text-xs rounded-lg bg-background border-border shadow-sm focus:ring-2 focus:ring-primary/20">
                      <SelectValue placeholder="Provider (Server Default)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">Provider (Server Default)</SelectItem>
                      <SelectItem value="gemini">Google Gemini</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="groq">Groq</SelectItem>
                      <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {byokProvider && (
                  <div>
                    <input
                      type="text"
                      value={byokModel}
                      onChange={e => setByokModel(e.target.value)}
                      placeholder="Model (optional)"
                      className="w-full text-xs rounded-lg border border-border bg-background text-foreground px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50 shadow-sm"
                    />
                  </div>
                )}
                {byokProvider && (
                  <div className="relative">
                    <input
                      type={byokKeyVisible ? 'text' : 'password'}
                      value={byokKey}
                      onChange={e => setByokKey(e.target.value)}
                      placeholder="API Key"
                      className="w-full text-xs rounded-lg border border-border bg-background text-foreground px-3 py-2 pr-9 focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono shadow-sm"
                    />
                    <button
                      type="button"
                      onClick={() => setByokKeyVisible(v => !v)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                    >
                      {byokKeyVisible ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                )}
                {byokKey && (
                  <button
                    type="button"
                    onClick={() => { setByokKey(''); setByokProvider(''); setByokModel(''); }}
                    className="text-xs text-red-500 hover:text-red-700 text-left font-semibold transition-colors mt-1"
                  >
                    ✕ Clear API Key
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};
