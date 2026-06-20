import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Search, BookOpen, GraduationCap, X, Library } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../lib/api';

const Marketplace = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const departmentIdParam = searchParams.get('department_id');
  
  const [courses, setCourses] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState(departmentIdParam || 'all');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [coursesRes, deptRes] = await Promise.all([
          api.get('/api/v1/academic/courses'),
          api.get('/api/v1/academic/departments')
        ]);
        setCourses(coursesRes.data.data || []);
        setDepartments(deptRes.data.data || []);
      } catch (err) {
        console.error("Failed to load marketplace data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleDeptSelect = (deptId) => {
    setSelectedDept(deptId);
    if (deptId === 'all') {
      searchParams.delete('department_id');
    } else {
      searchParams.set('department_id', deptId);
    }
    setSearchParams(searchParams);
  };

  const filteredCourses = courses.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          course.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDept = selectedDept === 'all' || String(course.department_id) === String(selectedDept);
    return matchesSearch && matchesDept;
  });

  const getDeptName = (deptId) => {
    return departments.find(d => String(d.id) === String(deptId))?.name || 'Unknown Department';
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
      <div>
        <h1 className="text-4xl font-serif font-bold text-foreground mb-3">
          Course Catalog
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl">
          Discover and explore all academic programs available on the Lumière platform.
        </p>
      </div>

      <div className="bg-card border border-border rounded-lg p-6 flex flex-col md:flex-row gap-4 shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Search courses by title or code..." 
            className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent transition-all"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select 
          className="px-4 py-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-accent appearance-none cursor-pointer md:w-64"
          value={selectedDept}
          onChange={(e) => handleDeptSelect(e.target.value)}
        >
          <option value="all">All Departments</option>
          {departments.map(dept => (
            <option key={dept.id} value={dept.id}>{dept.name}</option>
          ))}
        </select>
        {selectedDept !== 'all' && (
          <button 
            onClick={() => handleDeptSelect('all')}
            className="px-4 py-3 border border-border text-foreground font-medium rounded-lg hover:bg-muted transition-colors flex items-center gap-2"
          >
            <X size={18} /> Clear
          </button>
        )}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-64 bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
      ) : filteredCourses.length === 0 ? (
        <div className="bg-card border border-border rounded-lg p-16 text-center">
          <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4 flex items-center justify-center">
            <BookOpen size={48} />
          </div>
          <h3 className="text-xl font-serif font-semibold text-foreground mb-2">No courses found</h3>
          <p className="text-muted-foreground">Try adjusting your search criteria or department filter.</p>
          <button 
            onClick={() => { setSearchTerm(''); handleDeptSelect('all'); }}
            className="mt-6 px-6 py-3 border border-border text-foreground font-medium rounded-lg hover:bg-muted transition-colors"
          >
            Clear all filters
          </button>
        </div>
      ) : (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredCourses.map((course) => (
            <motion.div key={course.id} variants={itemVariants}>
              <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-all h-full flex flex-col hover:border-accent">
                <CardHeader className="pb-3 border-b border-border/50">
                  <div className="flex justify-between items-start mb-2">
                    <span className="px-3 py-1 bg-muted text-muted-foreground text-xs font-bold rounded-full font-mono">
                      {course.code}
                    </span>
                    <span className="text-xs font-semibold text-accent flex items-center gap-1 bg-accent/10 px-2 py-1 rounded-md">
                      <GraduationCap size={14} /> {course.credits || 3} Credits
                    </span>
                  </div>
                  <CardTitle className="text-xl font-serif font-bold text-foreground leading-tight line-clamp-2">
                    {course.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4 flex-1">
                  <p className="text-sm text-muted-foreground line-clamp-3 mb-4 leading-relaxed">
                    {course.description || "No description available for this course. Please contact the department for more details."}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium">
                    <Library size={14} className="text-accent" />
                    <span>{getDeptName(course.department_id)}</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-4 pb-6 px-6 border-t border-border/50 bg-background/50">
                  <button className="w-full px-4 py-2 border-2 border-accent text-accent font-medium rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors flex justify-center items-center gap-2">
                    View Knowledge Graph
                  </button>
                </CardFooter>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
};

export default Marketplace;
