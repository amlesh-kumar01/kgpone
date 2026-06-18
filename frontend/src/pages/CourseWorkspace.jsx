import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useParams } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import api from '../services/api';

export default function CourseWorkspace() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { courseId } = useParams();

  // Workspace selections
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'graph'

  // Documents/Materials
  const [documents, setDocuments] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);

  // Chat/Query state
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'assistant',
      text: "Hello! Select a course and ask me any academic questions. I will walk through your study notes and prerequisite course graphs to ground my answers.",
      citations: [],
      graph: null
    }
  ]);
  const [isQuerying, setIsQuerying] = useState(false);

  // Interactive details
  const [selectedCitation, setSelectedCitation] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    if (selectedCourse) {
      fetchDocuments(selectedCourse.code);
    }
  }, [selectedCourse]);

  const fetchCourses = async () => {
    try {
      const res = await api.get('/content/courses');
      setCourses(res.data);
      if (res.data.length > 0) {
        // Find if URL param matches any course code
        const matching = res.data.find(c => c.code.toLowerCase() === courseId?.toLowerCase());
        setSelectedCourse(matching || res.data[0]);
      }
    } catch (error) {
      console.error("Failed to load workspace courses", error);
    }
  };

  const fetchDocuments = async (courseCode) => {
    setIsLoadingDocs(true);
    try {
      const res = await api.get('/content/my-content');
      // Filter documents belonging to the active course
      const filtered = res.data.filter(doc => doc.course_code.toLowerCase() === courseCode.toLowerCase());
      setDocuments(filtered);
    } catch (error) {
      console.error("Failed to load documents", error);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isQuerying]);

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || !selectedCourse || isQuerying) return;

    const currentQuery = query;
    setQuery('');
    setIsQuerying(true);

    // Append user message
    setChatHistory(prev => [...prev, { role: 'user', text: currentQuery }]);

    try {
      const res = await api.post('/content/query', {
        query: currentQuery,
        course_code: selectedCourse.code
      });

      // Append assistant message
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        text: res.data.answer,
        citations: res.data.citations || [],
        graph: res.data.graph || null
      }]);
    } catch (error) {
      console.error("Query failed", error);
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        text: "I encountered an error executing your query. Please make sure the backend services are running properly.",
        citations: [],
        graph: null
      }]);
    } finally {
      setIsQuerying(false);
    }
  };

  // Extract the latest graph structure from chat history to display
  const latestGraphMsg = [...chatHistory].reverse().find(msg => msg.graph && msg.graph.nodes && msg.graph.nodes.length > 0);
  const activeGraph = latestGraphMsg ? latestGraphMsg.graph : null;

  return (
    <div className="bg-theme-bg text-theme-text min-h-screen flex flex-col antialiased transition-colors duration-300">
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />

      {/* Top Header */}
      <header className="flex items-center justify-between px-8 py-4 border-b border-theme-border transition-colors duration-300 bg-theme-surface/30 backdrop-blur-md sticky top-0 z-30">
        <div className="flex items-center gap-6">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-theme-border transition-colors text-theme-text-muted hover:text-theme-text"
          >
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          </button>
          
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-theme-accent text-[26px]">terminal</span>
            <h1 className="font-sans text-lg font-semibold text-theme-text leading-none">Research Workspace</h1>
          </div>

          {/* Course Selector Dropdown */}
          <div className="relative">
            <select
              value={selectedCourse?.code || ''}
              onChange={(e) => {
                const found = courses.find(c => c.code === e.target.value);
                if (found) {
                  setSelectedCourse(found);
                  navigate(`/workspace/${found.code}`);
                }
              }}
              className="bg-theme-surface border border-theme-border rounded-xl px-4 py-2 text-sm font-medium text-theme-text focus:outline-none focus:border-theme-accent cursor-pointer transition-colors"
            >
              {courses.map(course => (
                <option key={course.code} value={course.code}>
                  {course.code} - {course.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <ThemeToggle />
          <div className="flex flex-col items-end text-xs font-mono text-theme-text-muted">
            <span>Role: {user?.role}</span>
          </div>
        </div>
      </header>

      {/* Main Workspace split panel */}
      <main className="flex-1 flex overflow-hidden h-[calc(100vh-69px)]">
        
        {/* Left Side Panel: Document library and tab controls */}
        <section className="w-80 border-r border-theme-border flex flex-col bg-theme-surface/10 transition-colors duration-300">
          <div className="p-4 border-b border-theme-border">
            <h2 className="text-sm font-mono text-theme-text-muted uppercase tracking-wider mb-2">Lecture Notes Library</h2>
            <p className="text-xs text-theme-text-muted leading-relaxed">
              Materials indexed under the active course vector space.
            </p>
          </div>

          {/* Document List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {isLoadingDocs ? (
              <div className="flex items-center justify-center py-8">
                <span className="material-symbols-outlined animate-spin text-theme-accent">refresh</span>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12 text-theme-text-muted border border-dashed border-theme-border rounded-xl p-4">
                <span className="material-symbols-outlined text-3xl opacity-50 mb-2">folder_open</span>
                <p className="text-xs">No lecture materials found.</p>
                <p className="text-[10px] mt-1">Upload files through the Publisher Portal to index them.</p>
              </div>
            ) : (
              documents.map((doc, idx) => (
                <div 
                  key={idx} 
                  className="p-3.5 rounded-xl border border-theme-border bg-theme-surface/40 hover:border-theme-accent transition-all duration-300 group flex items-start gap-3"
                >
                  <span className="material-symbols-outlined text-theme-accent mt-0.5">draft</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-theme-text truncate">{doc.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] px-2 py-0.5 rounded-md font-mono bg-theme-border text-theme-text-strong">
                        {doc.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Center Panel: Visualization Pane */}
        <section className="flex-1 flex flex-col border-r border-theme-border relative bg-theme-bg">
          {/* Header controls for Visualizations */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-theme-border bg-theme-surface/20">
            <div className="flex gap-2">
              <button 
                onClick={() => setActiveTab('chat')}
                className={`px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                  activeTab === 'chat' 
                    ? 'bg-theme-accent-light text-theme-accent border border-theme-accent-light/50' 
                    : 'text-theme-text-muted hover:text-theme-text'
                }`}
              >
                GROUNDED CHAT
              </button>
              <button 
                onClick={() => setActiveTab('graph')}
                className={`px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                  activeTab === 'graph' 
                    ? 'bg-theme-accent-light text-theme-accent border border-theme-accent-light/50' 
                    : 'text-theme-text-muted hover:text-theme-text'
                }`}
              >
                PREREQUISITE CONCEPT GRAPH
              </button>
            </div>
            {activeTab === 'graph' && (
              <span className="text-[10px] font-mono text-theme-text-muted flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-theme-accent"></span>
                Interactive Path Rendering
              </span>
            )}
          </div>

          {/* Visualization Container */}
          <div className="flex-1 relative overflow-hidden flex flex-col">
            {activeTab === 'graph' ? (
              <div className="absolute inset-0 flex flex-col p-6">
                <div className="mb-4">
                  <h3 className="text-base font-semibold text-theme-text">Curriculum Time-Travel Pathway</h3>
                  <p className="text-xs text-theme-text-muted mt-1">
                    Visualizing concept nodes walked during query reasoning. Amber nodes indicate missing prerequisites located in previous years.
                  </p>
                </div>

                <div className="flex-1 bg-theme-surface/10 border border-theme-border rounded-2xl relative overflow-hidden flex items-center justify-center">
                  {activeGraph ? (
                    <svg className="w-full h-full min-h-[400px]">
                      {/* Draw Edges */}
                      {activeGraph.edges?.map((edge, idx) => {
                        const srcNode = activeGraph.nodes.find(n => n.id === edge.source);
                        const tarNode = activeGraph.nodes.find(n => n.id === edge.target);
                        if (!srcNode || !tarNode) return null;

                        // Give coordinates based on index or layout type
                        const srcIdx = activeGraph.nodes.indexOf(srcNode);
                        const tarIdx = activeGraph.nodes.indexOf(tarNode);
                        
                        const x1 = 150 + srcIdx * 120;
                        const y1 = 200 + (srcIdx % 2) * 80;
                        const x2 = 150 + tarIdx * 120;
                        const y2 = 200 + (tarIdx % 2) * 80;

                        return (
                          <g key={idx}>
                            <line 
                              x1={x1} y1={y1} x2={x2} y2={y2} 
                              stroke="var(--theme-border-strong, #1c2e24)" 
                              strokeWidth="2.5" 
                              strokeDasharray="5,5"
                            />
                            {/* Direction Arrow */}
                            <circle cx={(x1+x2)/2} cy={(y1+y2)/2} r="4" fill="var(--theme-accent, #4edea3)" />
                          </g>
                        );
                      })}

                      {/* Draw Nodes */}
                      {activeGraph.nodes?.map((node, idx) => {
                        const x = 150 + idx * 120;
                        const y = 200 + (idx % 2) * 80;

                        // Type colors
                        const isPrereq = node.type === 'prerequisite';
                        const isTarget = node.type === 'target';
                        const circleColor = isPrereq 
                          ? 'fill-amber-500/20 stroke-amber-500 shadow-md' 
                          : isTarget 
                            ? 'fill-emerald-500/20 stroke-theme-accent' 
                            : 'fill-slate-500/20 stroke-slate-500';

                        return (
                          <g key={idx} className="cursor-pointer group">
                            <circle 
                              cx={x} cy={y} r="28" 
                              className={`${circleColor} transition-all duration-300 stroke-2 hover:r-32`} 
                            />
                            <text 
                              x={x} y={y + 45} 
                              textAnchor="middle" 
                              className="text-xs font-medium fill-theme-text font-sans select-none"
                            >
                              {node.label}
                            </text>
                            <text 
                              x={x} y={y + 58} 
                              textAnchor="middle" 
                              className="text-[9px] font-mono fill-theme-text-muted"
                            >
                              ({node.course})
                            </text>
                            <circle cx={x} cy={y} r="4" fill="var(--theme-text)" />
                          </g>
                        );
                      })}
                    </svg>
                  ) : (
                    <div className="text-center text-theme-text-muted p-8">
                      <span className="material-symbols-outlined text-4xl opacity-50 mb-2">account_tree</span>
                      <p className="text-sm">Prerequisite dependency path is currently empty.</p>
                      <p className="text-xs mt-1">Submit a search query containing advanced concepts to map dependencies.</p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              // Grounded Chat Interface
              <div className="absolute inset-0 flex flex-col bg-theme-bg">
                {/* Chat Log Message Scroller */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {chatHistory.map((message, idx) => (
                    <div 
                      key={idx} 
                      className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {message.role !== 'user' && (
                        <div className="w-9 h-9 rounded-xl bg-theme-accent-light flex items-center justify-center shrink-0 border border-theme-accent-light/40">
                          <span className="material-symbols-outlined text-theme-accent text-[20px]">terminal</span>
                        </div>
                      )}
                      
                      <div className="max-w-xl flex flex-col gap-2">
                        <div 
                          className={`rounded-2xl p-4 text-sm leading-relaxed border transition-colors ${
                            message.role === 'user'
                              ? 'bg-theme-surface border-theme-border text-theme-text shadow-sm'
                              : 'bg-theme-surface/50 border-theme-border/50 text-theme-text'
                          }`}
                        >
                          <p className="whitespace-pre-wrap">{message.text}</p>

                          {/* Show inline citation tags clickable preview */}
                          {message.citations && message.citations.length > 0 && (
                            <div className="mt-4 pt-3 border-t border-theme-border flex flex-wrap gap-2">
                              {message.citations.map((cit) => (
                                <button
                                  key={cit.citation_id}
                                  onClick={() => setSelectedCitation(cit)}
                                  className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-theme-border text-theme-text-strong border border-theme-border hover:border-theme-accent transition-colors"
                                >
                                  <span className="material-symbols-outlined text-[14px]">bookmark</span>
                                  {cit.citation_id}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {isQuerying && (
                    <div className="flex gap-4 justify-start">
                      <div className="w-9 h-9 rounded-xl bg-theme-accent-light flex items-center justify-center shrink-0 animate-pulse">
                        <span className="material-symbols-outlined text-theme-accent text-[20px]">terminal</span>
                      </div>
                      <div className="rounded-2xl p-4 text-sm bg-theme-surface/20 border border-theme-border/30 text-theme-text-muted flex items-center gap-2">
                        <span className="material-symbols-outlined animate-spin text-xs">sync</span>
                        Querying Vector DB and traversing dependency chains...
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Question Input Container */}
                <form 
                  onSubmit={handleQuerySubmit}
                  className="p-6 border-t border-theme-border bg-theme-surface/10 flex gap-3"
                >
                  <input 
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={isQuerying || !selectedCourse}
                    placeholder={
                      selectedCourse 
                        ? `Ask a question about ${selectedCourse.code} (e.g. 'Explain A* search')...` 
                        : "Please select/add a course to start chat"
                    }
                    className="flex-1 bg-theme-surface border border-theme-border rounded-xl px-4 py-3 text-sm text-theme-text focus:outline-none focus:border-theme-accent disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={!query.trim() || isQuerying || !selectedCourse}
                    className="bg-theme-accent text-white font-medium px-5 rounded-xl hover:bg-theme-accent-hover transition-colors disabled:opacity-50 flex items-center justify-center"
                  >
                    <span className="material-symbols-outlined">send</span>
                  </button>
                </form>
              </div>
            )}
          </div>
        </section>

        {/* Right Drawer: Selected Citation detailed view */}
        {selectedCitation && (
          <aside className="w-80 border-l border-theme-border flex flex-col bg-theme-surface/20 p-6 transition-colors duration-300">
            <div className="flex items-center justify-between border-b border-theme-border pb-4 mb-4">
              <h3 className="font-semibold text-theme-text flex items-center gap-2">
                <span className="material-symbols-outlined text-theme-accent text-[18px]">verified</span>
                Source Provenance
              </h3>
              <button 
                onClick={() => setSelectedCitation(null)}
                className="w-6 h-6 rounded-md hover:bg-theme-border flex items-center justify-center text-theme-text-muted hover:text-theme-text"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <div className="space-y-4 flex-1 overflow-y-auto pr-1">
              <div>
                <span className="text-[10px] font-mono text-theme-text-muted uppercase tracking-wider block">Citation Tag</span>
                <span className="text-sm font-semibold text-theme-accent">{selectedCitation.citation_id}</span>
              </div>

              <div>
                <span className="text-[10px] font-mono text-theme-text-muted uppercase tracking-wider block">Document Title</span>
                <span className="text-sm font-medium text-theme-text">{selectedCitation.source_title}</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[10px] font-mono text-theme-text-muted uppercase tracking-wider block">Course Code</span>
                  <span className="text-xs text-theme-text">{selectedCitation.course_code}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-theme-text-muted uppercase tracking-wider block">Relevance</span>
                  <span className="text-xs text-theme-text">{(selectedCitation.score * 100).toFixed(0)}% Score</span>
                </div>
              </div>

              {selectedCitation.is_prerequisite && (
                <div className="p-3 bg-amber-500/15 border border-amber-500/30 rounded-xl">
                  <h4 className="text-xs font-semibold text-amber-500 flex items-center gap-1.5 mb-1">
                    <span className="material-symbols-outlined text-[14px]">warning</span>
                    Prerequisite Grounding
                  </h4>
                  <p className="text-[10px] text-theme-text leading-relaxed">
                    Retrieved from your previous year course covering prerequisite topic: <strong>{selectedCitation.prerequisite_concept}</strong>.
                  </p>
                </div>
              )}

              <div>
                <span className="text-[10px] font-mono text-theme-text-muted uppercase tracking-wider block mb-1">Direct text snippet</span>
                <div className="p-3 bg-theme-surface/50 border border-theme-border/50 rounded-xl text-xs leading-relaxed text-theme-text-muted font-mono whitespace-pre-wrap max-h-64 overflow-y-auto">
                  {selectedCitation.text_snippet}
                </div>
              </div>
            </div>
          </aside>
        )}

      </main>
    </div>
  );
}
