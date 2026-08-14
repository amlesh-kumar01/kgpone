import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, BookOpen, BrainCircuit } from "lucide-react";
import api from '../lib/api';
import { useAcademic } from '../context/AcademicContext';
import ManageOfferings from '../components/ManageOfferings';
import { useNavigate } from 'react-router-dom';

const StudyUnits = () => {
  const { orgUnits, studyUnits, loading, refreshAcademicData } = useAcademic();
  const navigate = useNavigate();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  
  const [formData, setFormData] = useState({ 
    org_unit_id: '', 
    code: '', 
    title: '', 
    description: '', 
    credits: 4 
  });
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.post('/api/v1/academic/', formData);
      if (res.data.status === 'success') {
        toast({ title: "StudyUnit created successfully!" });
        setIsDialogOpen(false);
        setFormData({ org_unit_id: '', code: '', title: '', description: '', credits: 4 });
        refreshAcademicData();
      }
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Failed to create study_unit",
        description: err.response?.data?.message || err.message,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">StudyUnits</h1>
          <p className="text-slate-500">Manage academic studyUnits across orgUnits.</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> Add StudyUnit
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New StudyUnit</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="org_unit">OrgUnit</Label>
                <Select 
                  value={formData.org_unit_id} 
                  onValueChange={(val) => setFormData({...formData, org_unit_id: val})}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a org_unit" />
                  </SelectTrigger>
                  <SelectContent>
                    {orgUnits.map(dept => (
                      <SelectItem key={dept.id} value={dept.id}>{dept.code} - {dept.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="code">StudyUnit Code</Label>
                  <Input 
                    id="code" placeholder="e.g., CS101"
                    value={formData.code} 
                    onChange={(e) => setFormData({...formData, code: e.target.value})} 
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="credits">Credits</Label>
                  <Input 
                    id="credits" type="number" min="1"
                    value={formData.credits} 
                    onChange={(e) => setFormData({...formData, credits: parseInt(e.target.value)})} 
                    required 
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="title">StudyUnit Title</Label>
                <Input 
                  id="title" 
                  value={formData.title} 
                  onChange={(e) => setFormData({...formData, title: e.target.value})} 
                  required 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Input 
                  id="description" 
                  value={formData.description} 
                  onChange={(e) => setFormData({...formData, description: e.target.value})} 
                />
              </div>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Save StudyUnit
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Credits</TableHead>
                <TableHead>OrgUnit</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-slate-500">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                  </TableCell>
                </TableRow>
              ) : studyUnits.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-slate-500">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <BookOpen className="h-10 w-10 text-slate-300" />
                      <p>No studyUnits found. Create one to get started.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                studyUnits.map((study_unit) => (
                  <TableRow key={study_unit.id}>
                    <TableCell className="font-medium text-primary">{study_unit.code}</TableCell>
                    <TableCell>{study_unit.title}</TableCell>
                    <TableCell>{study_unit.credits}</TableCell>
                    <TableCell>
                      {orgUnits.find(d => d.id === study_unit.org_unit_id)?.code || 'Unknown'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/study-units/${study_unit.id}/analyze`)}
                          className="gap-1.5 text-accent border-accent/30 hover:bg-accent/5"
                        >
                          <BrainCircuit className="w-4 h-4" /> StudyUnit Studio
                        </Button>
                        <ManageOfferings study_unit={study_unit} />
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default StudyUnits;
