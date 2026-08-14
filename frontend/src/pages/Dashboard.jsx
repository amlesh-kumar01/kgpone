import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BookOpen, Users, Library, Activity, ArrowRight, SearchX } from 'lucide-react';
import api from '../lib/api';
import { motion } from 'framer-motion';

import MarketplaceSearch from '../components/marketplace/MarketplaceSearch';
import OrgUnitSidebar from '../components/marketplace/OrgUnitSidebar';
import StudyUnitCard from '../components/marketplace/StudyUnitCard';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [stats, setStats] = useState({
    orgUnits: 0,
    studyUnits: 0,
    documents: 0,
    students: 0
  });

  const [orgUnits, setOrgUnits] = useState([]);
  const [allStudyUnits, setAllStudyUnits] = useState([]);
  const [loading, setLoading] = useState(true);

  // Search results state
  const [selectedDeptId, setSelectedDeptId] = useState(null);
  const [selectedYear, setSelectedYear] = useState(null);
  const [displayedStudyUnits, setDisplayedStudyUnits] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [deptRes, studyUnitsRes] = await Promise.all([
          api.get('/api/v1/academic/orgUnits'),
          api.get('/api/v1/academic/') // fetch all studyUnits for global search
        ]);
        
        const fetchedDepts = deptRes.data.data || [];
        const fetchedStudyUnits = studyUnitsRes.data.data || [];
        
        setOrgUnits(fetchedDepts);
        setAllStudyUnits(fetchedStudyUnits);
        
        let studentCount = 0;
        let docCount = 0;

        if (user?.role === 'ADMIN' || user?.role === 'PUBLISHER') {
            try {
                const docsRes = await api.get('/api/v1/documents/');
                docCount = docsRes.data.data?.length || 0;
            } catch (e) {
                console.warn('Failed to fetch documents stats', e);
            }
        }
        
        if (user?.role === 'ADMIN') {
            try {
                const usersRes = await api.get('/api/v1/users/');
                studentCount = usersRes.data.data?.filter(u => u.role === 'STUDENT').length || 0;
            } catch (e) {
                console.warn('Failed to fetch users stats', e);
            }
        }
        
        setStats(prev => ({ 
          ...prev, 
          orgUnits: fetchedDepts.length,
          studyUnits: fetchedStudyUnits.length,
          documents: docCount,
          students: studentCount
        }));
      } catch (err) {
        console.error("Failed to fetch data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Update displayed studyUnits when a org_unit and year are selected
  useEffect(() => {
    if (selectedDeptId && selectedYear) {
      const filtered = allStudyUnits.filter(study_unit => {
        if (String(study_unit.org_unit_id) !== String(selectedDeptId)) return false;
        return study_unit.offerings && study_unit.offerings.some(offering => offering.year === parseInt(selectedYear));
      });
      setDisplayedStudyUnits(filtered);
    } else if (selectedDeptId && !selectedYear) {
      // If only org_unit is selected
      const filtered = allStudyUnits.filter(study_unit => String(study_unit.org_unit_id) === String(selectedDeptId));
      setDisplayedStudyUnits(filtered);
    } else {
      setDisplayedStudyUnits([]);
    }
  }, [selectedDeptId, selectedYear, allStudyUnits]);

  const handleOrgUnitYearSelect = (deptId, yearVal) => {
    setSelectedDeptId(deptId);
    setSelectedYear(yearVal);
  };

  const handleStudyUnitSelect = (study_unitId) => {
    // Placeholder route for study_unit material
    navigate(`/study-units/${study_unitId}`);
  };

  const getDeptName = (deptId) => {
    return orgUnits.find(d => String(d.id) === String(deptId))?.name || 'Unknown OrgUnit';
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
      className="flex flex-col gap-8 w-full"
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
          orgUnits={orgUnits}
          studyUnits={allStudyUnits}
          onOrgUnitYearSelect={handleOrgUnitYearSelect}
          onStudyUnitSelect={handleStudyUnitSelect}
        />
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col space-y-8">
          {/* Stats Overview */}
          <motion.div variants={containerVariants} className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            <motion.div variants={itemVariants}>
              <Card className="rounded-xl bg-card border border-border/60 shadow-none hover:border-primary/20 transition-colors">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Total OrgUnits</CardTitle>
                  <Library className="h-4 w-4 text-primary" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">{stats.orgUnits}</div>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <Card className="rounded-xl bg-card border border-border/60 shadow-none hover:border-primary/20 transition-colors">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Total StudyUnits</CardTitle>
                  <BookOpen className="h-4 w-4 text-primary" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">{stats.studyUnits}</div>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <Card className="rounded-xl bg-card border border-border/60 shadow-none hover:border-primary/20 transition-colors">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Active Students</CardTitle>
                  <Users className="h-4 w-4 text-primary" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">{stats.students || (user?.role === 'STUDENT' ? 'N/A' : 0)}</div>
                </CardContent>
              </Card>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <Card className="rounded-xl bg-card border border-border/60 shadow-none hover:border-primary/20 transition-colors">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Documents</CardTitle>
                  <Activity className="h-4 w-4 text-primary" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold font-serif text-foreground">{stats.documents || (user?.role === 'STUDENT' ? 'N/A' : 0)}</div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>

          {/* Search Results / Discovery Area */}
          {selectedDeptId && (
            <motion.div variants={itemVariants} className="pt-6 border-t border-border">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-serif font-bold text-foreground">
                  {getDeptName(selectedDeptId)} {selectedYear ? `- Year ${selectedYear}` : 'StudyUnits'}
                </h2>
                <button 
                  onClick={() => { setSelectedDeptId(null); setSelectedYear(null); }}
                  className="text-sm text-accent hover:underline"
                >
                  Clear Results
                </button>
              </div>

              {displayedStudyUnits.length === 0 ? (
                <div className="bg-card border border-border rounded-lg p-16 text-center">
                  <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4 flex items-center justify-center">
                    <SearchX size={48} />
                  </div>
                  <h3 className="text-xl font-serif font-semibold text-foreground mb-2">No studyUnits found</h3>
                  <p className="text-muted-foreground">There are no studyUnits matching this selection.</p>
                </div>
              ) : (
                <div className="space-y-8">
                  {['AUTUMN', 'SPRING'].map((semesterName) => {
                    // If a year is selected, check offerings for that specific year and semester
                    // If no year selected, just group by semester
                    const semesterStudyUnits = displayedStudyUnits.filter(study_unit => 
                      study_unit.offerings && study_unit.offerings.some(offering => 
                        offering.semester === semesterName && (!selectedYear || offering.year === parseInt(selectedYear))
                      )
                    );

                    if (semesterStudyUnits.length === 0) return null;

                    return (
                      <div key={semesterName} className="space-y-4">
                        <h3 className="text-xl font-serif font-semibold text-foreground border-b border-border pb-2 capitalize">
                          {semesterName.toLowerCase()} Semester
                        </h3>
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                          {semesterStudyUnits.map((study_unit) => (
                            <StudyUnitCard 
                              key={study_unit.id} 
                              study_unit={study_unit} 
                              org_unitName={getDeptName(study_unit.org_unit_id)} 
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
                <Card className="rounded-xl bg-card border border-border/60 shadow-none h-full flex flex-col">
                  <CardHeader>
                    <CardTitle className="font-serif text-xl">Recent Activity</CardTitle>
                    <CardDescription className="text-sm">
                      A summary of recent document ingestions and study_unit additions.
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
                <Card className="rounded-xl bg-card border border-border/60 shadow-none h-full">
                  <CardHeader>
                    <CardTitle className="font-serif text-xl">Quick Actions</CardTitle>
                    <CardDescription className="text-sm">
                      Common administrative tasks.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="p-4 bg-background rounded-lg border border-border text-sm flex justify-between items-center cursor-pointer hover:border-accent hover:shadow-sm transition-all group">
                        <span className="font-medium text-foreground">Add New OrgUnit</span>
                        <ArrowRight className="w-4 h-4 text-accent group-hover:translate-x-1 transition-transform" />
                      </div>
                      <div className="p-4 bg-background rounded-lg border border-border text-sm flex justify-between items-center cursor-pointer hover:border-accent hover:shadow-sm transition-all group">
                        <span className="font-medium text-foreground">Create StudyUnit Offering</span>
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

        {/* Right Sidebar: OrgUnits */}
        <div className="w-full md:w-64 shrink-0">
          <OrgUnitSidebar orgUnits={orgUnits} />
        </div>
      </div>
    </motion.div>
  );
};

export default Dashboard;
