import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function Marketplace() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDept, setSelectedDept] = useState('ALL');
  const [selectedCourse, setSelectedCourse] = useState(null);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    setIsLoading(true);
    try {
      // Fetch from API
      const res = await api.get('/academic/');
      // Fallback stub if backend is empty
      if (res.data && res.data.length > 0) {
        setCourses(res.data);
      } else {
        setCourses([
          { id: '1', code: 'CS101', title: 'Programming & Data Structures', credits: 4, department: 'CSE', description: 'Basic programming constructs, arrays, linked lists, stacks, and binary trees.', prerequisites: [] },
          { id: '2', code: 'CS202', title: 'Algorithms Design & Analysis', credits: 4, department: 'CSE', description: 'Asymptotic analysis, divide & conquer, greedy strategy, dynamic programming, and graphs.', prerequisites: ['CS101'] },
          { id: '3', code: 'CS303', title: 'Artificial Intelligence & Agents', credits: 3, department: 'CSE', description: 'State space search, game playing, heuristic evaluation, and machine learning models.', prerequisites: ['CS202'] },
          { id: '4', code: 'EE101', title: 'Basic Electrical Technology', credits: 4, department: 'EE', description: 'Network theorems, AC circuits, transformers, and magnetic networks.', prerequisites: [] },
          { id: '5', code: 'EE202', title: 'Signals and Systems', credits: 3, department: 'EE', description: 'Continuous-time and discrete-time signals, Fourier series, Laplace, and Z-transforms.', prerequisites: ['EE101'] },
          { id: '6', code: 'MA101', title: 'Engineering Mathematics I', credits: 4, department: 'MA', description: 'Calculus of single variable, sequences and series, multivariable derivatives.', prerequisites: [] }
        ]);
      }
    } catch (err) {
      console.error("Failed to load courses from API", err);
      // Failover list for UI demonstration
      setCourses([
        { id: '1', code: 'CS101', title: 'Programming & Data Structures', credits: 4, department: 'CSE', description: 'Basic programming constructs, arrays, linked lists, stacks, and binary trees.', prerequisites: [] },
        { id: '2', code: 'CS202', title: 'Algorithms Design & Analysis', credits: 4, department: 'CSE', description: 'Asymptotic analysis, divide & conquer, greedy strategy, dynamic programming, and graphs.', prerequisites: ['CS101'] },
        { id: '3', code: 'CS303', title: 'Artificial Intelligence & Agents', credits: 3, department: 'CSE', description: 'State space search, game playing, heuristic evaluation, and machine learning models.', prerequisites: ['CS202'] },
        { id: '4', code: 'EE101', title: 'Basic Electrical Technology', credits: 4, department: 'EE', description: 'Network theorems, AC circuits, transformers, and magnetic networks.', prerequisites: [] },
        { id: '5', code: 'EE202', title: 'Signals and Systems', credits: 3, department: 'EE', description: 'Continuous-time and discrete-time signals, Fourier series, Laplace, and Z-transforms.', prerequisites: ['EE101'] },
        { id: '6', code: 'MA101', title: 'Engineering Mathematics I', credits: 4, department: 'MA', description: 'Calculus of single variable, sequences and series, multivariable derivatives.', prerequisites: [] }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter logic
  const filteredCourses = courses.filter(course => {
    const matchesSearch = 
      course.code.toLowerCase().includes(searchQuery.toLowerCase()) || 
      course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (course.description && course.description.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesDept = selectedDept === 'ALL' || course.department === selectedDept || (course.code.startsWith(selectedDept));
    return matchesSearch && matchesDept;
  });

  return (
    <div className="bg-[#060d13] text-white min-h-screen flex flex-col antialiased font-sans transition-colors duration-300">
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      <style dangerouslySetInnerHTML={{
        __html: `
          body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #060d13;
          }
          .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
          }
          .search-pill {
            background-color: #0D1520;
            border: 1px border #1e2d3d;
            border-radius: 9999px;
            padding: 4px 6px 4px 18px;
          }
          .cyan-glow {
            box-shadow: 0 0 25px rgba(0, 210, 255, 0.04);
          }
          .cyan-glow-intense:hover {
            box-shadow: 0 0 15px rgba(0, 210, 255, 0.15);
            border-color: #00D2FF;
          }
        `
      }} />

      {/* Top Header */}
      <header className="flex items-center justify-between px-8 py-4 border-b border-[#1e2d3d] bg-[#0D1520]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-6">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-[#1e2d3d] transition-colors text-[#9CA3AF] hover:text-white"
          >
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          </button>
          
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#00D2FF] text-[24px]">terminal</span>
            <div className="flex items-center gap-1 font-bold text-lg tracking-tight">
              <span>Kgp</span>
              <span className="text-[#00D2FF]">One</span>
            </div>
          </div>
        </div>

        {/* Elegant curved search bar inside header */}
        <div className="flex-1 max-w-xl mx-8 relative flex items-center search-pill border border-[#1e2d3d]">
          <span className="material-symbols-outlined text-[#6B7280] mr-2.5">search</span>
          <input 
            type="text" 
            placeholder="Search courses, prerequisites, topics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm focus:outline-none text-white placeholder:text-[#4B5563]"
          />
          <button 
            className="bg-[#00D2FF] text-black text-xs font-semibold px-5 py-2 rounded-full hover:bg-[#1AD1FF] transition-colors"
            onClick={() => {}}
          >
            Search
          </button>
        </div>

        <div className="flex items-center gap-6">
          <ThemeToggle />
          <div className="flex flex-col items-end text-xs font-mono text-[#6B7280]">
            <span>{user?.email}</span>
          </div>
        </div>
      </header>

      {/* Main Layout Grid */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 flex flex-col gap-6">
        
        {/* Dept Selector Tags */}
        <div className="flex items-center gap-2.5 overflow-x-auto pb-2 border-b border-[#1e2d3d]/50">
          {['ALL', 'CSE', 'EE', 'MA'].map(dept => (
            <button
              key={dept}
              onClick={() => setSelectedDept(dept)}
              className={`px-4.5 py-1.5 rounded-full text-xs font-semibold tracking-wider uppercase border transition-all ${
                selectedDept === dept
                  ? 'bg-[#00D2FF] text-black border-[#00D2FF] shadow-[0_0_10px_rgba(0,210,255,0.2)]'
                  : 'bg-[#0D1520] text-[#9CA3AF] border-[#1e2d3d] hover:text-white hover:border-[#6B7280]'
              }`}
            >
              {dept}
            </button>
          ))}
        </div>

        {/* Catalog Body */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* Courses List */}
          <section className="lg:col-span-2 space-y-5">
            <div className="flex justify-between items-center mb-1">
              <h2 className="text-xl font-bold tracking-tight text-white">Academic Index</h2>
              <span className="text-xs font-mono text-[#6B7280]">Found {filteredCourses.length} syllabus entries</span>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-20 bg-[#0D1520] border border-[#1e2d3d] rounded-2xl">
                <span className="material-symbols-outlined animate-spin text-[#00D2FF] text-3xl">refresh</span>
              </div>
            ) : filteredCourses.length === 0 ? (
              <div className="text-center py-16 bg-[#0D1520] border border-[#1e2d3d] border-dashed rounded-2xl p-6 text-[#9CA3AF]">
                <span className="material-symbols-outlined text-4xl opacity-50 mb-3">explore</span>
                <p className="text-sm">No course syllabus matches your search parameters.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredCourses.map(course => (
                  <div
                    key={course.id || course.code}
                    onClick={() => setSelectedCourse(course)}
                    className={`group p-5 bg-[#0D1520] border rounded-2xl transition-all cursor-pointer flex flex-col justify-between h-48 ${
                      selectedCourse?.code === course.code 
                        ? 'border-[#00D2FF] shadow-[0_0_15px_rgba(0,210,255,0.08)]' 
                        : 'border-[#1e2d3d] cyan-glow-intense'
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-bold tracking-widest text-[#00D2FF] uppercase font-mono">{course.code}</span>
                        <span className="text-[10px] font-medium bg-[#1e2d3d] text-[#9CA3AF] px-2.5 py-0.5 rounded-full">{course.credits} Credits</span>
                      </div>
                      <h3 className="text-sm font-bold text-white mb-2 line-clamp-1 group-hover:text-[#00D2FF] transition-colors">{course.title}</h3>
                      <p className="text-[#9CA3AF] text-xs line-clamp-2 leading-relaxed">{course.description}</p>
                    </div>

                    {course.prerequisites && course.prerequisites.length > 0 && (
                      <div className="flex items-center gap-1.5 overflow-hidden mt-3 pt-3 border-t border-[#1e2d3d]/50">
                        <span className="text-[9px] font-bold text-[#6B7280] uppercase tracking-wider">Prereqs:</span>
                        {course.prerequisites.map(prereq => (
                          <span key={prereq} className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#00D2FF]/10 text-[#00D2FF] border border-[#00D2FF]/20">
                            {prereq}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Sidebar Detail Card */}
          <section className="lg:col-span-1 space-y-6">
            <div className="bg-[#0D1520] border border-[#1e2d3d] rounded-2xl p-6 shadow-md cyan-glow min-h-[380px] flex flex-col justify-between">
              
              {selectedCourse ? (
                <div className="space-y-5">
                  <div className="border-b border-[#1e2d3d] pb-4">
                    <span className="text-xs font-bold text-[#00D2FF] tracking-widest uppercase font-mono">{selectedCourse.code}</span>
                    <h3 className="text-lg font-bold text-white mt-1 leading-snug">{selectedCourse.title}</h3>
                    <p className="text-xs text-[#6B7280] mt-1">Allocation: {selectedCourse.credits} Credits, Lecture-Tutorial-Practical structure</p>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-[#6B7280] tracking-wider uppercase block">Course Description</span>
                    <p className="text-xs text-[#9CA3AF] leading-relaxed">{selectedCourse.description}</p>
                  </div>

                  {/* SVG Dependency Flow Render */}
                  <div className="space-y-2.5 pt-2">
                    <span className="text-[10px] font-bold text-[#6B7280] tracking-wider uppercase block">Prerequisite Pathway</span>
                    <div className="bg-[#060d13] border border-[#1e2d3d] rounded-xl p-4 flex flex-col items-center justify-center min-h-[120px]">
                      {selectedCourse.prerequisites && selectedCourse.prerequisites.length > 0 ? (
                        <div className="flex items-center gap-3 w-full justify-center">
                          {selectedCourse.prerequisites.map((prereq, index) => (
                            <div key={prereq} className="flex items-center gap-3">
                              <div className="px-3 py-1.5 rounded-lg border border-[#00D2FF]/20 bg-[#00D2FF]/5 text-center">
                                <span className="text-[10px] font-bold text-[#00D2FF] font-mono block">{prereq}</span>
                                <span className="text-[8px] text-[#6B7280]">Required</span>
                              </div>
                              <span className="material-symbols-outlined text-xs text-[#6B7280]">arrow_forward</span>
                            </div>
                          ))}
                          <div className="px-3 py-1.5 rounded-lg border border-[#00FF88]/20 bg-[#00FF88]/5 text-center">
                            <span className="text-[10px] font-bold text-[#00FF88] font-mono block">{selectedCourse.code}</span>
                            <span className="text-[8px] text-[#6B7280]">Unlock</span>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-[#6B7280] text-xs">
                          <span className="material-symbols-outlined text-lg mb-1 opacity-50 block">check_circle</span>
                          No prerequisites required. Available for enrollment.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center text-[#9CA3AF]">
                  <span className="material-symbols-outlined text-4xl text-[#6B7280] mb-3 opacity-60">info</span>
                  <p className="text-sm font-semibold">No Course Selected</p>
                  <p className="text-xs text-[#6B7280] mt-1 max-w-[200px]">Select a course syllabus card to view syllabus details and requirement paths.</p>
                </div>
              )}

              {selectedCourse && (
                <button
                  onClick={() => navigate(`/workspace/${selectedCourse.code}`)}
                  className="w-full bg-[#00D2FF] hover:bg-[#1AD1FF] active:scale-[0.99] text-black font-semibold text-xs py-3 rounded-lg transition-all flex items-center justify-center gap-2 shadow-[0_0_12px_rgba(0,210,255,0.15)] mt-6"
                >
                  Enter Workspace
                  <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </button>
              )}
            </div>
          </section>

        </div>

      </main>

      {/* Footer Status Bar */}
      <footer className="w-full py-4 border-t border-[#1e2d3d] px-8 bg-[#0D1520]/60 backdrop-blur-md flex items-center justify-between text-[10px] font-mono text-[#6B7280]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00FF88] shadow-[0_0_8px_#00FF88]"></span>
          <span className="text-[#00FF88] tracking-widest font-bold uppercase">System Active</span>
        </div>
        <div>
          <span>© 2026 KgpOne. Catalog Index.</span>
        </div>
      </footer>

    </div>
  );
}
