import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Calendar } from "lucide-react";
import api from '../lib/api';

const ManageOfferings = ({ study_unit }) => {
  const [offerings, setOfferings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  
  const [formData, setFormData] = useState({
    offering_id: study_unit.id,
    year: new Date().getFullYear(),
    semester: 'AUTUMN'
  });
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  const fetchOfferings = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/academic/${study_unit.id}/offerings`);
      setOfferings(res.data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isDialogOpen) {
      fetchOfferings();
    }
  }, [isDialogOpen, study_unit.id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.post(`/api/v1/academic/${study_unit.id}/offerings`, formData);
      if (res.data.status === 'success') {
        toast({ title: "Offering added successfully!" });
        setFormData({ ...formData, year: new Date().getFullYear(), semester: 'AUTUMN' });
        fetchOfferings();
      }
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Failed to add offering",
        description: err.response?.data?.message || err.message,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="ml-2">
          <Calendar className="mr-2 h-4 w-4" /> Offerings
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Manage Offerings - {study_unit.code}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="border border-border rounded-lg p-4 bg-muted/20">
            <h3 className="font-medium mb-3">Add New Offering</h3>
            <form onSubmit={handleSubmit} className="flex gap-2 items-end">
              <div className="space-y-2 flex-1">
                <Label htmlFor="semester">Semester</Label>
                <Select 
                  value={formData.semester} 
                  onValueChange={(val) => setFormData({...formData, semester: val})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="AUTUMN">Autumn</SelectItem>
                    <SelectItem value="SPRING">Spring</SelectItem>
                    <SelectItem value="SUMMER">Summer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 w-24">
                <Label htmlFor="year">Year</Label>
                <Input 
                  id="year" type="number" 
                  value={formData.year} 
                  onChange={(e) => setFormData({...formData, year: parseInt(e.target.value)})} 
                  required 
                />
              </div>
              <Button type="submit" disabled={submitting}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              </Button>
            </form>
          </div>

          <div>
            <h3 className="font-medium mb-2">Current Offerings</h3>
            {loading ? (
              <div className="flex justify-center py-4"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
            ) : offerings.length === 0 ? (
              <p className="text-sm text-muted-foreground py-2 text-center border border-dashed rounded-lg">No offerings found.</p>
            ) : (
              <ul className="space-y-2">
                {offerings.map(o => (
                  <li key={o.id} className="flex justify-between items-center p-3 bg-card border border-border rounded-lg text-sm">
                    <span className="font-medium">{o.semester} {o.year}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ManageOfferings;
