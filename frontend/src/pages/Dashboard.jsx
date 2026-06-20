import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BookOpen, Users, Library, Activity, ArrowRight } from 'lucide-react';
import api from '../lib/api';
import { motion } from 'framer-motion';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    departments: 0,
    courses: 0,
    documents: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const deptRes = await api.get('/api/v1/academic/departments');
        setStats(prev => ({ ...prev, departments: deptRes.data.data?.length || 0 }));
      } catch (err) {
        console.error("Failed to fetch stats", err);
      }
    };
    fetchStats();
  }, []);

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

      <motion.div variants={containerVariants} className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <motion.div variants={itemVariants}>
          <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Departments</CardTitle>
              <Library className="h-4 w-4 text-accent" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold font-serif text-foreground">{stats.departments}</div>
              <p className="text-xs text-muted-foreground mt-2">+1 from last month</p>
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
              <div className="text-3xl font-bold font-serif text-foreground">124</div>
              <p className="text-xs text-muted-foreground mt-2">+12% from last month</p>
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
              <p className="text-xs text-muted-foreground mt-2">+18% from last month</p>
            </CardContent>
          </Card>
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Documents Processed</CardTitle>
              <Activity className="h-4 w-4 text-accent" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold font-serif text-foreground">8,234</div>
              <p className="text-xs text-muted-foreground mt-2">+201 since last hour</p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      <motion.div variants={containerVariants} className="grid gap-8 md:grid-cols-2 lg:grid-cols-7">
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
    </motion.div>
  );
};

export default Dashboard;
