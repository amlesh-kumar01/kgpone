import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BookOpen, Users, Library, Activity, ArrowRight, SearchX } from 'lucide-react';
import api from '../lib/api';
import { motion } from 'framer-motion';

import MarketplaceSearch from '../components/marketplace/MarketplaceSearch';
import DepartmentSidebar from '../components/marketplace/DepartmentSidebar';
import CourseCard from '../components/marketplace/CourseCard';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [stats, setStats] = useState({
    departments: 0,
    courses: 0,
    documents: 0
  });

  const [departments, setDepartments] = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  // Search results state
  const [selectedDeptId, setSelectedDeptId] = useState(null);
  const [selectedYear, setSelectedYear] = useState(null);
  const [displayedCourses, setDisplayedCourses] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [deptRes, coursesRes] = await Promise.all([
          api.get('/api/v1/academic/departments'),
          api.get('/api/v1/academic/') // fetch all courses for global search
        ]);
        
        const fetchedDepts = deptRes.data.data || [];
        const fetchedCourses = coursesRes.data.data || [];
        
        setDepartments(fetchedDepts);
        setAllCourses(fetchedCourses);
        
        setStats(prev => ({ 
          ...prev, 
          departments: fetchedDepts.length,
          courses: fetchedCourses.length 
        }));
      } catch (err) {
        console.error("Failed to fetch data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Update displayed courses when a department and year are selected
  useEffect(() => {
    if (selectedDeptId && selectedYear) {
      const filtered = allCourses.filter(course => {
        if (String(course.department_id) !== String(selectedDeptId)) return false;
        return course.offerings && course.offerings.some(offering => offering.year === parseInt(selectedYear));
      });
      setDisplayedCourses(filtered);
    } else if (selectedDeptId && !selectedYear) {
      // If only department is selected
      const filtered = allCourses.filter(course => String(course.department_id) === String(selectedDeptId));
      setDisplayedCourses(filtered);
    } else {
      setDisplayedCourses([]);
    }
  }, [selectedDeptId, selectedYear, allCourses]);

  const handleDepartmentYearSelect = (deptId, yearVal) => {
    setSelectedDeptId(deptId);
    setSelectedYear(yearVal);
  };

  const handleCourseSelect = (courseId) => {
    // Placeholder route for course material
    navigate(`/courses/${courseId}`);
  };

  const getDeptName = (deptId) => {
    return departments.find(d => String(d.id) === String(deptId))?.name || 'Unknown Department';
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col gap-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
    >
      <div className="mb-4">
        <h1 className="text-4xl font-serif font-bold text-foreground mb-3">
          Dashboard Overview
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl">
          Welcome back, {user?.full_name}. Monitor platform activity and manage the academic knowledge graph.
        </p>
      </div>

      <div className="w-full">
        <MarketplaceSearch 
          departments={departments}
          courses={allCourses}
          onDepartmentYearSelect={handleDepartmentYearSelect}
          onCourseSelect={handleCourseSelect}
        />
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col space-y-8">
          {/* Stats Overview */}
          <motion.div variants={containerVariants} className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            <motion.div variants={itemVariants}>
              <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Total Departments</CardTitle>
                  <Library className="h-4 w-4 text-accent" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">{stats.departments}</div>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Total Courses</CardTitle>
                  <BookOpen className="h-4 w-4 text-accent" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">{stats.courses}</div>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Active Students</CardTitle>
                  <Users className="h-4 w-4 text-accent" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">2,350</div>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Documents</CardTitle>
                  <Activity className="h-4 w-4 text-accent" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">8,234</div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>

          {/* Search Results / Discovery Area */}
          {selectedDeptId && (
            <motion.div variants={itemVariants} className="pt-6 border-t border-border">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-serif font-bold text-foreground">
                  {getDeptName(selectedDeptId)} {selectedYear ? `- Year ${selectedYear}` : 'Courses'}
                </h2>
                <button 
                  onClick={() => { setSelectedDeptId(null); setSelectedYear(null); }}
                  className="text-sm text-accent hover:underline"
                >
                  Clear Results
                </button>
              </div>

              {displayedCourses.length === 0 ? (
                <div className="bg-card border border-border rounded-lg p-16 text-center">
                  <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4 flex items-center justify-center">
                    <SearchX size={48} />
                  </div>
                  <h3 className="text-xl font-serif font-semibold text-foreground mb-2">No courses found</h3>
                  <p className="text-muted-foreground">There are no courses matching this selection.</p>
                </div>
              ) : (
                <div className="space-y-8">
                  {['AUTUMN', 'SPRING'].map((semesterName) => {
                    // If a year is selected, check offerings for that specific year and semester
                    // If no year selected, just group by semester
                    const semesterCourses = displayedCourses.filter(course => 
                      course.offerings && course.offerings.some(offering => 
                        offering.semester === semesterName && (!selectedYear || offering.year === parseInt(selectedYear))
                      )
                    );

                    if (semesterCourses.length === 0) return null;

                    return (
                      <div key={semesterName} className="space-y-4">
                        <h3 className="text-xl font-serif font-semibold text-foreground border-b border-border pb-2 capitalize">
                          {semesterName.toLowerCase()} Semester
                        </h3>
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                          {semesterCourses.map((course) => (
                            <CourseCard 
                              key={course.id} 
                              course={course} 
                              departmentName={getDeptName(course.department_id)} 
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}

          {/* Default view when no search is active */}
          {!selectedDeptId && (
            <motion.div variants={containerVariants} className="grid gap-8 md:grid-cols-2 lg:grid-cols-7 pt-6 border-t border-border">
              <motion.div variants={itemVariants} className="col-span-4">
                <Card className="rounded-lg bg-card border-border shadow-sm h-full flex flex-col">
                  <CardHeader>
                    <CardTitle className="font-serif text-xl">Recent Activity</CardTitle>
                    <CardDescription className="text-sm">
                      A summary of recent document ingestions and course additions.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1 flex flex-col justify-center">
                    <div className="flex items-center justify-center h-48 text-muted-foreground/60 text-sm border border-dashed border-border rounded-lg bg-muted/30">
                      [ ACTIVITY GRAPH RENDER ZONE ]
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
              
              <motion.div variants={itemVariants} className="col-span-3">
                <Card className="rounded-lg bg-card border-border shadow-sm h-full">
                  <CardHeader>
                    <CardTitle className="font-serif text-xl">Quick Actions</CardTitle>
                    <CardDescription className="text-sm">
                      Common administrative tasks.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="p-4 bg-background rounded-lg border border-border text-sm flex justify-between items-center cursor-pointer hover:border-accent hover:shadow-sm transition-all group">
                        <span className="font-medium text-foreground">Add New Department</span>
                        <ArrowRight className="w-4 h-4 text-accent group-hover:translate-x-1 transition-transform" />
                      </div>
                      <div className="p-4 bg-background rounded-lg border border-border text-sm flex justify-between items-center cursor-pointer hover:border-accent hover:shadow-sm transition-all group">
                        <span className="font-medium text-foreground">Create Course Offering</span>
                        <ArrowRight className="w-4 h-4 text-accent group-hover:translate-x-1 transition-transform" />
                      </div>
                      <div className="p-4 bg-background rounded-lg border border-border text-sm flex justify-between items-center cursor-pointer hover:border-accent hover:shadow-sm transition-all group">
                        <span className="font-medium text-foreground">Upload Document</span>
                        <ArrowRight className="w-4 h-4 text-accent group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </motion.div>
          )}
        </div>

        {/* Right Sidebar: Departments */}
        <div className="w-full md:w-64 shrink-0">
          <DepartmentSidebar departments={departments} />
        </div>
      </div>
    </motion.div>
  );
};

export default Dashboard;
