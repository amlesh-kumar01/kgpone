import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { Loader2, UploadCloud, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import api from '../lib/api';
import { useAcademic } from '../context/AcademicContext';

const Documents = () => {
  const { departments, courses: allCourses } = useAcademic();
  const [documents, setDocuments] = useState([]);
  const [filteredCourses, setFilteredCourses] = useState([]);
  const [offerings, setOfferings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  
  // Cascading Selection State
  const [selectedDeptId, setSelectedDeptId] = useState('');
  const [selectedCourseId, setSelectedCourseId] = useState('');
  
  const [formData, setFormData] = useState({ 
    course_offering_id: '', 
    title: '', 
    description: '', 
    parsing_instructions: '',
    doc_type: 'NOTES',
    file: null
  });
  
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  // Filter courses when department changes
  useEffect(() => {
    if (selectedDeptId) {
      setFilteredCourses(allCourses.filter(c => String(c.department_id) === String(selectedDeptId)));
      setSelectedCourseId('');
      setOfferings([]);
      setFormData(prev => ({ ...prev, course_offering_id: '' }));
    } else {
      setFilteredCourses([]);
    }
  }, [selectedDeptId, allCourses]);

  // Fetch offerings when course changes
  useEffect(() => {
    if (selectedCourseId) {
      api.get(`/api/v1/academic/${selectedCourseId}/offerings`)
        .then(res => setOfferings(res.data.data || []))
        .catch(err => console.error("Failed to fetch offerings", err));
    } else {
      setOfferings([]);
      setFormData(prev => ({ ...prev, course_offering_id: '' }));
    }
  }, [selectedCourseId]);

  // Fetch documents when a course offering is fully selected
  useEffect(() => {
    if (formData.course_offering_id) {
      setLoading(true);
      api.get(`/api/v1/documents/offering/${formData.course_offering_id}`)
        .then(res => setDocuments(res.data.data || []))
        .catch(err => {
          console.error("Failed to load documents", err);
          setDocuments([]);
        })
        .finally(() => setLoading(false));
    } else {
      setDocuments([]);
    }
  }, [formData.course_offering_id]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFormData({ ...formData, file: e.target.files[0] });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.file) {
      toast({ variant: "destructive", title: "Please select a file" });
      return;
    }
    if (!formData.course_offering_id) {
      toast({ variant: "destructive", title: "Please select a Course Offering" });
      return;
    }
    
    setSubmitting(true);
    try {
      // 1. Get presigned URL
      const presignedRes = await api.post('/api/v1/documents/presigned-url', {
        course_offering_id: formData.course_offering_id,
        filename: formData.file.name,
        content_type: formData.file.type || 'application/pdf'
      });
      
      const { upload_url, file_key } = presignedRes.data.data;

      // 2. Upload file directly to S3
      await fetch(upload_url, {
        method: 'PUT',
        body: formData.file,
        headers: {
          'Content-Type': formData.file.type || 'application/pdf'
        }
      });

      // 3. Register document in backend
      const format = formData.file.name.split('.').pop().toUpperCase();
      await api.post('/api/v1/documents/', {
        course_offering_id: formData.course_offering_id,
        title: formData.title,
        description: formData.description,
        parsing_instructions: formData.parsing_instructions,
        doc_type: formData.doc_type,
        format: format,
        s3_key: file_key,
        file_size_bytes: formData.file.size,
        metadata_entries: []
      });

      toast({ title: "Document uploaded and processing started!" });
      setIsDialogOpen(false);
      setFormData({ 
        course_offering_id: formData.course_offering_id, 
        title: '', description: '', 
        parsing_instructions: '', doc_type: 'NOTES', file: null 
      });
      
      // Reload documents for current offering
      setLoading(true);
      const docsRes = await api.get(`/api/v1/documents/offering/${formData.course_offering_id}`);
      setDocuments(docsRes.data.data || []);
      setLoading(false);
      
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Upload failed",
        description: err.response?.data?.message || err.message,
      });
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch(status?.toUpperCase()) {
      case 'COMPLETED':
        return <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700 border border-green-200"><CheckCircle2 size={12}/> Processed</span>;
      case 'FAILED':
        return <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 border border-red-200"><AlertCircle size={12}/> Failed</span>;
      default:
        return <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 border border-amber-200"><Loader2 className="animate-spin" size={12}/> Processing</span>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-serif font-bold tracking-tight text-foreground mb-2">Knowledge Ingestion</h1>
          <p className="text-muted-foreground text-lg">Upload and process documents for the global semantic graph.</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <button className="px-6 py-3 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-opacity-90 transition-colors flex items-center gap-2">
              <UploadCloud size={20} /> Upload Knowledge
            </button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto bg-card border border-border p-8 rounded-xl shadow-xl">
            <DialogHeader className="mb-6">
              <DialogTitle className="text-2xl font-serif font-bold text-foreground">Upload Document</DialogTitle>
              <p className="text-muted-foreground mt-2">Select the strict academic path before uploading.</p>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-foreground">1. Department</label>
                  <select 
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                    value={selectedDeptId} 
                    onChange={(e) => setSelectedDeptId(e.target.value)}
                  >
                    <option value="">Select Department...</option>
                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-foreground">2. Course</label>
                  <select 
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
                    value={selectedCourseId} 
                    onChange={(e) => setSelectedCourseId(e.target.value)}
                    disabled={!selectedDeptId}
                  >
                    <option value="">Select Course...</option>
                    {filteredCourses.map(c => <option key={c.id} value={c.id}>{c.code}</option>)}
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">3. Course Offering (Semester/Year)</label>
                <select 
                  className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
                  value={formData.course_offering_id} 
                  onChange={(e) => setFormData({...formData, course_offering_id: e.target.value})}
                  disabled={!selectedCourseId || offerings.length === 0}
                  required
                >
                  <option value="">{offerings.length === 0 && selectedCourseId ? "No offerings available" : "Select Offering..."}</option>
                  {offerings.map(o => <option key={o.id} value={o.id}>{o.semester} {o.year}</option>)}
                </select>
              </div>

              <div className="my-6 border-t border-border"></div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">Document Title *</label>
                <input 
                  type="text"
                  placeholder="e.g. Midterm Study Guide"
                  className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                  value={formData.title} 
                  onChange={(e) => setFormData({...formData, title: e.target.value})} 
                  required 
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-foreground">Document Type *</label>
                  <select 
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                    value={formData.doc_type} 
                    onChange={(e) => setFormData({...formData, doc_type: e.target.value})}
                    required
                  >
                    <option value="NOTES">Notes</option>
                    <option value="PYQ">PYQ (Past Year Question)</option>
                    <option value="SYLLABUS">Syllabus</option>
                    <option value="TEXTBOOK">Textbook</option>
                    <option value="ASSIGNMENT">Assignment</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-foreground">Description</label>
                  <input 
                    type="text"
                    placeholder="Brief description..."
                    className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent"
                    value={formData.description} 
                    onChange={(e) => setFormData({...formData, description: e.target.value})} 
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">AI Parsing Instructions</label>
                <textarea 
                  placeholder="e.g., Pay special attention to extracting chemical formulas."
                  className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent h-20 resize-none"
                  value={formData.parsing_instructions} 
                  onChange={(e) => setFormData({...formData, parsing_instructions: e.target.value})} 
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">Upload File</label>
                <input 
                  type="file" 
                  className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-accent file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-accent/10 file:text-accent font-medium hover:file:bg-accent/20 cursor-pointer"
                  onChange={handleFileChange} 
                  required 
                />
              </div>

              <button 
                type="submit" 
                className="w-full px-6 py-3 bg-accent text-accent-foreground font-medium rounded-lg hover:bg-opacity-90 transition-colors flex justify-center items-center gap-2 mt-4" 
                disabled={submitting}
              >
                {submitting ? <><Loader2 className="animate-spin" size={20} /> Processing...</> : "Submit to Knowledge Graph"}
              </button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="rounded-lg border-border shadow-sm overflow-hidden bg-card">
        <CardHeader className="bg-muted/30 border-b border-border/50 pb-4 pt-6 px-6">
          <CardTitle className="font-serif text-xl">Processed Knowledge Base</CardTitle>
          <CardDescription>
            {formData.course_offering_id 
              ? "Showing documents linked to the selected academic path."
              : "Select a department, course, and offering in the upload menu, or below, to view related documents."}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/20">
              <TableRow>
                <TableHead className="font-medium px-6 py-4">Title</TableHead>
                <TableHead className="font-medium py-4">Format</TableHead>
                <TableHead className="font-medium py-4">Status</TableHead>
                <TableHead className="font-medium py-4 text-right px-6">Ingested Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && formData.course_offering_id ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-16 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-accent" />
                  </TableCell>
                </TableRow>
              ) : documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-20">
                    <div className="flex flex-col items-center justify-center">
                      <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mb-4">
                        <FileText className="h-8 w-8 text-muted-foreground" />
                      </div>
                      <p className="text-lg font-medium text-foreground">No Knowledge Found</p>
                      <p className="text-muted-foreground mt-1 max-w-sm text-center">
                        Upload documents to populate the semantic graph for this path.
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => (
                  <TableRow key={doc.id} className="hover:bg-muted/30 cursor-pointer transition-colors">
                    <TableCell className="font-medium px-6 py-4">{doc.title}</TableCell>
                    <TableCell className="py-4"><span className="text-xs font-mono bg-accent/10 text-accent px-2 py-1 rounded">{doc.doc_type}</span></TableCell>
                    <TableCell className="py-4">
                      {getStatusBadge(doc.status)}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-right px-6 py-4 text-sm font-mono">
                      {new Date(doc.created_at).toLocaleDateString()}
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

export default Documents;
