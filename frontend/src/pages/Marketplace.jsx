import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BookOpen, SearchX } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../lib/api';

import MarketplaceSearch from '../components/marketplace/MarketplaceSearch';
import CourseCard from '../components/marketplace/CourseCard';
import DepartmentSidebar from '../components/marketplace/DepartmentSidebar';
import { useThrottle } from '../hooks/useThrottle';

const Marketplace = () => {
  const { departmentId } = useParams();
  const navigate = useNavigate();

  const [courses, setCourses] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(false);

  const [searchTerm, setSearchTerm] = useState('');
  const throttledSearch = useThrottle(searchTerm, 100);

  // Fetch departments on mount
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const res = await api.get('/api/v1/academic/departments');
        setDepartments(res.data.data || []);
      } catch (err) {
        console.error("Failed to load departments", err);
      }
    };
    fetchDepartments();
  }, []);

  // Fetch courses only when department is selected or search term is present
  useEffect(() => {
    const fetchCourses = async () => {
      // "will not fetch all courses by default"
      // Only fetch if a department is selected or user has typed a search term
      if (!departmentId && !throttledSearch) {
        setCourses([]);
        return;
      }

      setLoadingCourses(true);
      try {
        // If departmentId exists, fetch for that dept. Else fetch all courses to filter locally
        const params = departmentId ? { department_id: departmentId } : {};
        const res = await api.get('/api/v1/academic/', { params });
        setCourses(res.data.data || []);
      } catch (err) {
        console.error("Failed to load courses", err);
      } finally {
        setLoadingCourses(false);
      }
    };

    fetchCourses();
  }, [departmentId, throttledSearch]);

  const getDeptName = (deptId) => {
    return departments.find(d => String(d.id) === String(deptId))?.name || 'Unknown Department';
  };

  const filteredCourses = courses.filter(course => {
    if (!throttledSearch) return true;
    const lowerSearch = throttledSearch.toLowerCase();
    return course.title.toLowerCase().includes(lowerSearch) ||
      course.code.toLowerCase().includes(lowerSearch);
  });

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row gap-8">
      {/* Sidebar: Lists departments */}
      <DepartmentSidebar departments={departments} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="mb-8">
          <h1 className="text-4xl font-serif font-bold text-foreground mb-3">
            Course Catalog
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl">
            Discover and explore all academic programs available on the platform.
          </p>
        </div>

        <MarketplaceSearch
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
        />

        {loadingCourses ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-64 bg-muted rounded-lg animate-pulse" />
            ))}
          </div>
        ) : !departmentId && !throttledSearch ? (
          <div className="bg-card border border-border rounded-lg p-16 text-center shadow-sm">
            <div className="mx-auto h-12 w-12 text-accent/50 mb-4 flex items-center justify-center">
              <BookOpen size={48} />
            </div>
            <h3 className="text-xl font-serif font-semibold text-foreground mb-2">Welcome to Marketplace</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              Select a department from the sidebar to view its courses, or search for a specific course by title or code.
            </p>
          </div>
        ) : filteredCourses.length === 0 ? (
          <div className="bg-card border border-border rounded-lg p-16 text-center">
            <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4 flex items-center justify-center">
              <SearchX size={48} />
            </div>
            <h3 className="text-xl font-serif font-semibold text-foreground mb-2">No courses found</h3>
            <p className="text-muted-foreground">Try adjusting your search criteria or selecting a different department.</p>
            <button
              onClick={() => { setSearchTerm(''); navigate('/marketplace'); }}
              className="mt-6 px-6 py-3 border border-border text-foreground font-medium rounded-lg hover:bg-muted transition-colors"
            >
              Clear all filters
            </button>
          </div>
        ) : (
          <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {filteredCourses.map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                departmentName={getDeptName(course.department_id)}
              />
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Marketplace;
