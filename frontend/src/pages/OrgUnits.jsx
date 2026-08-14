import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BookOpen, Users, Library, ArrowRight, Plus } from "lucide-react";
import { motion } from 'framer-motion';
import { useAcademic } from '../context/AcademicContext';
import { useToast } from "@/hooks/use-toast";

const OrgUnits = () => {
  const navigate = useNavigate();
  const { orgUnits, loading, addOrgUnit } = useAcademic();
  const { toast } = useToast();
  
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newDept, setNewDept] = useState({ code: '', name: '' });

  const handleAddOrgUnit = async () => {
    setIsSubmitting(true);
    try {
      await addOrgUnit(newDept);
      setAddDialogOpen(false);
      setNewDept({ code: '', name: '' });
      toast({
        title: "OrgUnit Created",
        description: `Successfully added ${newDept.name}.`,
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err.message || "Failed to create org_unit.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

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
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-4xl font-serif font-bold text-foreground mb-3">Academic OrgUnits</h1>
          <p className="text-muted-foreground text-lg max-w-2xl">
            Browse and manage the hierarchical structure of Knowledge OS academic programs.
          </p>
        </div>
        <button 
          onClick={() => setAddDialogOpen(true)}
          className="px-5 py-2.5 bg-accent text-accent-foreground font-semibold rounded-lg shadow-sm hover:shadow-md hover:bg-opacity-90 transition-all flex items-center gap-2"
        >
          <Plus size={20} /> Add OrgUnit
        </button>
      </div>

      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="sm:max-w-[425px] bg-card border-border shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-foreground">Create OrgUnit</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4 mt-2">
            <div className="grid gap-2">
              <Label htmlFor="code" className="text-sm font-medium text-foreground">OrgUnit Code</Label>
              <Input
                id="code"
                placeholder="e.g. CS"
                className="col-span-3 bg-background border-border focus:ring-accent"
                value={newDept.code}
                onChange={(e) => setNewDept(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="name" className="text-sm font-medium text-foreground">OrgUnit Name</Label>
              <Input
                id="name"
                placeholder="e.g. Computer Science"
                className="col-span-3 bg-background border-border focus:ring-accent"
                value={newDept.name}
                onChange={(e) => setNewDept(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter className="mt-4">
            <button 
              onClick={handleAddOrgUnit}
              disabled={isSubmitting || !newDept.code || !newDept.name}
              className="px-6 py-2.5 bg-accent text-accent-foreground font-semibold rounded-lg shadow-sm hover:bg-opacity-90 transition-all disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Save OrgUnit"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => <div key={i} className="h-48 bg-muted rounded-lg animate-pulse" />)}
        </div>
      ) : orgUnits.length > 0 ? (
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {orgUnits.map((dept) => (
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
                    <span className="flex items-center gap-2"><BookOpen size={16}/> Assigned StudyUnits</span>
                    <span className="font-semibold text-foreground">View Catalog</span>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span className="flex items-center gap-2"><Users size={16}/> Enrolled Students</span>
                    <span className="font-semibold text-foreground">Active</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-4 pb-6 px-6 border-t border-border/50 bg-background/50">
                  <button 
                    onClick={() => navigate(`/marketplace?org_unit_id=${dept.id}`)}
                    className="w-full px-4 py-3 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-opacity-90 transition-colors flex justify-center items-center gap-2"
                  >
                    Explore StudyUnits <ArrowRight size={18} />
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
          <h3 className="text-xl font-serif font-semibold text-foreground mb-2">No orgUnits established</h3>
          <p className="text-muted-foreground mb-6">There are currently no academic orgUnits configured in the system.</p>
          <button 
            onClick={() => setAddDialogOpen(true)}
            className="px-6 py-3 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-opacity-90 transition-colors"
          >
            Create First OrgUnit
          </button>
        </div>
      )}
    </div>
  );
};

export default OrgUnits;
