import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { BookOpen, Users, Library, ArrowRight } from "lucide-react";
import { motion } from 'framer-motion';
import { useAcademic } from '../context/AcademicContext';

const Departments = () => {
  const navigate = useNavigate();
  const { departments, loading } = useAcademic();

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
      <div>
        <h1 className="text-4xl font-serif font-bold text-foreground mb-3">Academic Departments</h1>
        <p className="text-muted-foreground text-lg max-w-2xl">
          Browse and manage the hierarchical structure of Lumière's academic programs.
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => <div key={i} className="h-48 bg-muted rounded-lg animate-pulse" />)}
        </div>
      ) : departments.length > 0 ? (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {departments.map((dept) => (
            <motion.div key={dept.id} variants={itemVariants}>
              <Card className="rounded-lg bg-card border-border shadow-sm hover:shadow-md hover:border-accent transition-all h-full flex flex-col group">
                <CardHeader className="pb-3 border-b border-border/50">
                  <div className="flex justify-between items-start mb-2">
                    <span className="px-3 py-1 bg-muted text-muted-foreground text-xs font-bold rounded-full font-mono">
                      {dept.code}
                    </span>
                    <div className="bg-accent/10 p-2 rounded-lg">
                      <Library className="h-5 w-5 text-accent" />
                    </div>
                  </div>
                  <CardTitle className="text-2xl font-serif text-foreground leading-tight">{dept.name}</CardTitle>
                </CardHeader>
                <CardContent className="pt-6 flex-1 flex flex-col justify-center space-y-4">
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span className="flex items-center gap-2"><BookOpen size={16}/> Assigned Courses</span>
                    <span className="font-semibold text-foreground">View Catalog</span>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span className="flex items-center gap-2"><Users size={16}/> Enrolled Students</span>
                    <span className="font-semibold text-foreground">Active</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-4 pb-6 px-6 border-t border-border/50 bg-background/50">
                  <button 
                    onClick={() => navigate(`/marketplace?department_id=${dept.id}`)}
                    className="w-full px-4 py-3 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-opacity-90 transition-colors flex justify-center items-center gap-2"
                  >
                    Explore Courses <ArrowRight size={18} />
                  </button>
                </CardFooter>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <div className="bg-card border border-border rounded-lg p-16 text-center shadow-sm">
          <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4 flex items-center justify-center">
            <Library size={48} />
          </div>
          <h3 className="text-xl font-serif font-semibold text-foreground mb-2">No departments established</h3>
          <p className="text-muted-foreground mb-6">There are currently no academic departments configured in the system.</p>
          <button className="px-6 py-3 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-opacity-90 transition-colors">
            Create First Department
          </button>
        </div>
      )}
    </div>
  );
};

export default Departments;
