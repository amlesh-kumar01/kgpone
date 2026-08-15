import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { academicApi } from '../lib/academicApi';
import { Link, BookOpen, Layers, Library, Check, X, Plus, Trash2, ArrowRight } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

const AcademicManagement = () => {
  const { toast } = useToast();
  
  // State
  const [orgUnits, setOrgUnits] = useState([]);
  const [selectedOrgUnit, setSelectedOrgUnit] = useState(null);
  const [offerings, setOfferings] = useState([]);
  const [studyUnits, setStudyUnits] = useState([]);
  
  // UI State
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("org-units");
  
  // Modals
  const [isAddOrgUnitOpen, setIsAddOrgUnitOpen] = useState(false);
  const [isAddOfferingOpen, setIsAddOfferingOpen] = useState(false);
  const [isAddStudyUnitOpen, setIsAddStudyUnitOpen] = useState(false);
  const [isMappingOpen, setIsMappingOpen] = useState(false);
  const [mappingStudyUnit, setMappingStudyUnit] = useState(null);
  
  // Form States
  const [orgUnitForm, setOrgUnitForm] = useState({ code: '', name: '' });
  const [offeringForm, setOfferingForm] = useState({ code: '', name: '' });
  const [studyUnitForm, setStudyUnitForm] = useState({ code: '', name: '', description: '', credits: 0 });
  const [selectedOfferingToLink, setSelectedOfferingToLink] = useState('');

  // Fetch initial data
  useEffect(() => {
    fetchOrgUnits();
  }, []);

  // Fetch children when OrgUnit selected
  useEffect(() => {
    if (selectedOrgUnit) {
      const loadData = async () => {
        setContentLoading(true);
        await Promise.all([
          fetchOfferings(selectedOrgUnit.id),
          fetchStudyUnits(selectedOrgUnit.id)
        ]);
        setContentLoading(false);
      };
      loadData();
    } else {
      setOfferings([]);
      setStudyUnits([]);
    }
  }, [selectedOrgUnit]);

  const fetchOrgUnits = async () => {
    setLoading(true);
    try {
      const res = await academicApi.getOrgUnits();
      if (res.data?.status === 'success') {
        setOrgUnits(res.data.data);
      }
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load Organizations.' });
    }
    setLoading(false);
  };

  const fetchOfferings = async (orgId) => {
    try {
      const res = await academicApi.getOfferings(orgId);
      if (res.data?.status === 'success') {
        setOfferings(res.data.data);
      }
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load Offerings.' });
    }
  };

  const fetchStudyUnits = async (orgId) => {
    try {
      const res = await academicApi.getStudyUnits(orgId);
      if (res.data?.status === 'success') {
        setStudyUnits(res.data.data);
      }
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load Study Units.' });
    }
  };

  // Handlers
  const handleAddOrgUnit = async () => {
    try {
      const res = await academicApi.createOrgUnit(orgUnitForm);
      if (res.data?.status === 'success') {
        toast({ title: 'Success', description: 'Organization created.' });
        fetchOrgUnits();
        setIsAddOrgUnitOpen(false);
        setOrgUnitForm({ code: '', name: '' });
      }
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to create Organization.' });
    }
  };

  const handleAddOffering = async () => {
    if (!selectedOrgUnit) return;
    try {
      const res = await academicApi.createOffering(selectedOrgUnit.id, offeringForm);
      if (res.data?.status === 'success') {
        toast({ title: 'Success', description: 'Offering created.' });
        fetchOfferings(selectedOrgUnit.id);
        setIsAddOfferingOpen(false);
        setOfferingForm({ code: '', name: '' });
      }
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to create Offering.' });
    }
  };

  const handleAddStudyUnit = async () => {
    if (!selectedOrgUnit) return;
    try {
      const res = await academicApi.createStudyUnit(selectedOrgUnit.id, studyUnitForm);
      if (res.data?.status === 'success') {
        toast({ title: 'Success', description: 'Study Unit created.' });
        fetchStudyUnits(selectedOrgUnit.id);
        setIsAddStudyUnitOpen(false);
        setStudyUnitForm({ code: '', name: '', description: '', credits: 0 });
      }
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to create Study Unit.' });
    }
  };
  
  const handleLink = async () => {
    if (!mappingStudyUnit || !selectedOfferingToLink) return;
    try {
      await academicApi.linkOffering(mappingStudyUnit.id, selectedOfferingToLink);
      toast({ title: 'Success', description: 'Study Unit linked to Offering.' });
      fetchStudyUnits(selectedOrgUnit.id);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to link offering.' });
    }
  };

  const handleUnlink = async (studyUnitId, offeringId) => {
    try {
      await academicApi.unlinkOffering(studyUnitId, offeringId);
      toast({ title: 'Success', description: 'Offering unlinked.' });
      fetchStudyUnits(selectedOrgUnit.id);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to unlink offering.' });
    }
  };

  const handleDeleteStudyUnit = async (studyUnitId) => {
    try {
      await academicApi.deleteStudyUnit(studyUnitId);
      toast({ title: 'Success', description: 'Study Unit deleted.' });
      fetchStudyUnits(selectedOrgUnit.id);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to delete Study Unit.' });
    }
  };
  
  const handleDeleteOffering = async (offeringId) => {
    try {
      await academicApi.deleteOffering(offeringId);
      toast({ title: 'Success', description: 'Offering deleted.' });
      fetchOfferings(selectedOrgUnit.id);
      fetchStudyUnits(selectedOrgUnit.id);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to delete Offering.' });
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-foreground">Academic Console</h1>
          <p className="text-muted-foreground text-sm mt-1 max-w-2xl">Manage hierarchical curriculum structures.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full min-h-[600px]">
        
        {/* Left Sidebar - Organization List */}
        <Card className="col-span-1 border border-border shadow-sm bg-card overflow-hidden flex flex-col h-full">
          <CardHeader className="bg-muted/30 pb-4 border-b border-border">
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg flex items-center gap-2">
                <Library className="w-5 h-5 text-primary" /> 
                Organizations
              </CardTitle>
              <Button size="icon" variant="ghost" onClick={() => setIsAddOrgUnitOpen(true)}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0 overflow-y-auto flex-1">
            {loading ? (
              <div className="p-4 space-y-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-16 w-full bg-muted animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : orgUnits.length === 0 ? (
              <div className="p-6 text-center text-sm text-muted-foreground">
                No organizations found. Create one.
              </div>
            ) : (
              <div className="flex flex-col">
                {orgUnits.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => setSelectedOrgUnit(org)}
                    className={`text-left px-4 py-4 border-b border-border transition-colors hover:bg-accent/40 flex justify-between items-center ${
                      selectedOrgUnit?.id === org.id ? 'bg-primary/10 border-l-4 border-l-primary' : 'border-l-4 border-l-transparent'
                    }`}
                  >
                    <div>
                      <div className="font-semibold text-foreground">{org.name}</div>
                      <div className="text-xs text-muted-foreground mt-1 tracking-wider uppercase font-mono bg-muted inline-block px-1 rounded">{org.code}</div>
                    </div>
                    {selectedOrgUnit?.id === org.id && <ArrowRight className="w-4 h-4 text-primary" />}
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Main Content Area */}
        <div className="col-span-1 lg:col-span-3">
          {selectedOrgUnit ? (
            <div className="space-y-6">
              <div className="bg-primary/5 rounded-xl p-6 border border-primary/20 shadow-sm flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-foreground">{selectedOrgUnit.name}</h2>
                  <p className="text-sm text-muted-foreground mt-1">Manage Offerings and Study Units for this organization.</p>
                </div>
                <div className="bg-primary/10 text-primary font-mono text-sm px-3 py-1 rounded-full font-bold">
                  {selectedOrgUnit.code}
                </div>
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
                  <TabsTrigger value="org-units" className="flex items-center gap-2"><Layers className="w-4 h-4"/> Offerings</TabsTrigger>
                  <TabsTrigger value="study-units" className="flex items-center gap-2"><BookOpen className="w-4 h-4"/> Study Units</TabsTrigger>
                </TabsList>
                
                {contentLoading ? (
                  <div className="mt-6 space-y-4">
                    <div className="flex justify-between items-center mb-4">
                      <div className="h-8 w-40 bg-muted animate-pulse rounded"></div>
                      <div className="h-8 w-32 bg-muted animate-pulse rounded"></div>
                    </div>
                    {[1, 2].map(i => (
                      <div key={i} className="h-32 w-full bg-muted animate-pulse rounded-xl border border-border/50"></div>
                    ))}
                  </div>
                ) : (
                  <>
                    {/* Offerings Tab */}
                    <TabsContent value="org-units" className="mt-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xl font-semibold">Offerings ({offerings.length})</h3>
                    <Button onClick={() => setIsAddOfferingOpen(true)}>
                      <Plus className="w-4 h-4 mr-2" /> Add Offering
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {offerings.length === 0 ? (
                      <div className="col-span-full py-12 text-center bg-muted/20 border border-dashed rounded-lg">
                        <p className="text-muted-foreground">No Offerings mapped to this Organization.</p>
                      </div>
                    ) : (
                      offerings.map(offering => (
                        <Card key={offering.id} className="hover:border-primary/50 transition-colors shadow-sm">
                          <CardHeader className="pb-3">
                            <div className="flex justify-between items-start">
                              <CardTitle className="text-lg">{offering.name}</CardTitle>
                              <span className="text-xs font-mono bg-muted px-2 py-1 rounded">{offering.code}</span>
                            </div>
                          </CardHeader>
                          <CardFooter className="pt-2 flex justify-end">
                            <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive hover:bg-destructive/10" onClick={() => handleDeleteOffering(offering.id)}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </CardFooter>
                        </Card>
                      ))
                    )}
                  </div>
                </TabsContent>

                {/* Study Units Tab */}
                <TabsContent value="study-units" className="mt-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xl font-semibold">Study Units ({studyUnits.length})</h3>
                    <Button onClick={() => setIsAddStudyUnitOpen(true)}>
                      <Plus className="w-4 h-4 mr-2" /> Add Study Unit
                    </Button>
                  </div>
                  
                  <div className="space-y-4">
                    {studyUnits.length === 0 ? (
                      <div className="py-12 text-center bg-muted/20 border border-dashed rounded-lg">
                        <p className="text-muted-foreground">No Study Units created under this Organization.</p>
                      </div>
                    ) : (
                      studyUnits.map(unit => (
                        <Card key={unit.id} className="shadow-sm">
                          <CardHeader className="pb-2">
                            <div className="flex justify-between items-start">
                              <div>
                                <CardTitle className="text-lg text-primary">{unit.name}</CardTitle>
                                <CardDescription className="mt-1">{unit.description || 'No description provided.'}</CardDescription>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-mono bg-muted px-2 py-1 rounded font-bold">{unit.code}</span>
                                {unit.credits > 0 && <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded font-bold">{unit.credits} Cr</span>}
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent className="pt-4 border-t">
                            <div className="mb-2 flex justify-between items-center">
                              <p className="text-sm font-semibold text-foreground">Mapped Offerings:</p>
                              <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => {
                                setMappingStudyUnit(unit);
                                setIsMappingOpen(true);
                              }}>
                                <Link className="w-3 h-3 mr-1" /> Manage Links
                              </Button>
                            </div>
                            
                            {unit.offerings && unit.offerings.length > 0 ? (
                              <div className="flex flex-wrap gap-2">
                                {unit.offerings.map(off => (
                                  <div key={off.id} className="flex items-center text-xs bg-accent text-accent-foreground px-2 py-1 rounded-md border border-accent/50 shadow-sm">
                                    <span className="font-semibold">{off.name}</span>
                                    <button 
                                      onClick={() => handleUnlink(unit.id, off.id)}
                                      className="ml-2 p-0.5 rounded-full hover:bg-background/20"
                                      title="Unlink"
                                    >
                                      <X className="w-3 h-3" />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-xs text-muted-foreground italic">Not mapped to any offering.</p>
                            )}
                          </CardContent>
                          <CardFooter className="pt-0 justify-end">
                            <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive hover:bg-destructive/10" onClick={() => handleDeleteStudyUnit(unit.id)}>
                              <Trash2 className="w-4 h-4 mr-1" /> Delete
                            </Button>
                          </CardFooter>
                        </Card>
                      ))
                    )}
                  </div>
                </TabsContent>
                </>
              )}
              </Tabs>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center border border-dashed rounded-xl bg-muted/10">
              <Library className="w-16 h-16 text-muted-foreground/30 mb-4" />
              <h2 className="text-2xl font-bold text-foreground">No Organization Selected</h2>
              <p className="text-muted-foreground mt-2 max-w-sm text-center">Select an organization from the sidebar to manage its offerings and study units, or create a new one.</p>
            </div>
          )}
        </div>
      </div>

      {/* --- Modals --- */}
      
      {/* Create OrgUnit */}
      <Dialog open={isAddOrgUnitOpen} onOpenChange={setIsAddOrgUnitOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Organization</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Code</Label>
              <Input placeholder="e.g. CS" value={orgUnitForm.code} onChange={e => setOrgUnitForm({...orgUnitForm, code: e.target.value.toUpperCase()})} />
            </div>
            <div className="space-y-2">
              <Label>Name</Label>
              <Input placeholder="e.g. Computer Science Department" value={orgUnitForm.name} onChange={e => setOrgUnitForm({...orgUnitForm, name: e.target.value})} />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleAddOrgUnit} disabled={!orgUnitForm.code || !orgUnitForm.name}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Create Offering */}
      <Dialog open={isAddOfferingOpen} onOpenChange={setIsAddOfferingOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Offering in {selectedOrgUnit?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Term / Code</Label>
              <Input placeholder="e.g. FA26" value={offeringForm.code} onChange={e => setOfferingForm({...offeringForm, code: e.target.value.toUpperCase()})} />
            </div>
            <div className="space-y-2">
              <Label>Name</Label>
              <Input placeholder="e.g. Fall 2026" value={offeringForm.name} onChange={e => setOfferingForm({...offeringForm, name: e.target.value})} />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleAddOffering} disabled={!offeringForm.code || !offeringForm.name}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Study Unit */}
      <Dialog open={isAddStudyUnitOpen} onOpenChange={setIsAddStudyUnitOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Study Unit</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Code</Label>
                <Input placeholder="e.g. CS101" value={studyUnitForm.code} onChange={e => setStudyUnitForm({...studyUnitForm, code: e.target.value.toUpperCase()})} />
              </div>
              <div className="space-y-2">
                <Label>Credits</Label>
                <Input type="number" value={studyUnitForm.credits} onChange={e => setStudyUnitForm({...studyUnitForm, credits: parseInt(e.target.value) || 0})} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Name</Label>
              <Input placeholder="e.g. Intro to Computer Science" value={studyUnitForm.name} onChange={e => setStudyUnitForm({...studyUnitForm, name: e.target.value})} />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Input placeholder="Brief description..." value={studyUnitForm.description} onChange={e => setStudyUnitForm({...studyUnitForm, description: e.target.value})} />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleAddStudyUnit} disabled={!studyUnitForm.code || !studyUnitForm.name}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Link Offering Modal */}
      <Dialog open={isMappingOpen} onOpenChange={setIsMappingOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Link {mappingStudyUnit?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Select Offering to Link</Label>
              <Select value={selectedOfferingToLink} onValueChange={setSelectedOfferingToLink}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose an offering..." />
                </SelectTrigger>
                <SelectContent>
                  {offerings.filter(off => !mappingStudyUnit?.offerings?.some(mo => mo.id === off.id)).length === 0 ? (
                     <SelectItem value="none" disabled>All offerings are already linked</SelectItem>
                  ) : (
                    offerings
                      .filter(off => !mappingStudyUnit?.offerings?.some(mo => mo.id === off.id))
                      .map(off => (
                        <SelectItem key={off.id} value={off.id}>{off.name} ({off.code})</SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsMappingOpen(false)}>Cancel</Button>
            <Button onClick={handleLink} disabled={!selectedOfferingToLink || selectedOfferingToLink === 'none'}>Link Offering</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
    </div>
  );
};

export default AcademicManagement;
