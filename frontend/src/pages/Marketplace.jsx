import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchX, Building2, Layers } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../lib/api';

import MarketplaceSearch from '../components/marketplace/MarketplaceSearch';
import StudyUnitCard from '../components/marketplace/StudyUnitCard';
import { useThrottle } from '../hooks/useThrottle';

const Marketplace = () => {
  const navigate = useNavigate();

  const [studyUnits, setStudyUnits] = useState([]);
  const [orgUnits, setOrgUnits] = useState([]);
  const [offerings, setOfferings] = useState([]);
  const [loadingStudyUnits, setLoadingStudyUnits] = useState(false);
  
  const [selectedOrgUnit, setSelectedOrgUnit] = useState('');
  const [selectedOffering, setSelectedOffering] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const throttledSearch = useThrottle(searchTerm, 100);

  // Fetch orgUnits on mount
  useEffect(() => {
    const fetchOrgUnits = async () => {
      try {
        const res = await api.get('/api/v1/academic/org-units');
        setOrgUnits(res.data.data || []);
      } catch (err) {
        console.error("Failed to load orgUnits", err);
      }
    };
    fetchOrgUnits();
  }, []);

  // Fetch offerings when orgUnit changes
  useEffect(() => {
    const fetchOfferings = async () => {
      if (!selectedOrgUnit) {
        setOfferings([]);
        setSelectedOffering('');
        return;
      }
      try {
        const res = await api.get(`/api/v1/academic/org-units/${selectedOrgUnit}/offerings`);
        setOfferings(res.data.data || []);
      } catch (err) {
        console.error("Failed to load offerings", err);
      }
    };
    fetchOfferings();
  }, [selectedOrgUnit]);

  // Fetch studyUnits (default fetches all, or filtered by orgUnit/offering)
  useEffect(() => {
    const fetchStudyUnits = async () => {
      setLoadingStudyUnits(true);
      try {
        let url = `/api/v1/academic/study-units`;
        if (selectedOffering) {
          url = `/api/v1/academic/offerings/${selectedOffering}/study-units`;
        } else if (selectedOrgUnit) {
          url = `/api/v1/academic/org-units/${selectedOrgUnit}/study-units`;
        }
        
        const res = await api.get(url);
        setStudyUnits(res.data.data || []);
      } catch (err) {
        console.error("Failed to load studyUnits", err);
      } finally {
        setLoadingStudyUnits(false);
      }
    };

    fetchStudyUnits();
  }, [selectedOrgUnit, selectedOffering]);

  const getDeptName = (deptId) => {
    return orgUnits.find(d => String(d.id) === String(deptId))?.name || 'Unknown OrgUnit';
  };

  const filteredStudyUnits = studyUnits.filter(study_unit => {
    if (!throttledSearch) return true;
    const lowerSearch = throttledSearch.toLowerCase();
    return study_unit.title.toLowerCase().includes(lowerSearch) ||
      study_unit.code.toLowerCase().includes(lowerSearch);
  });

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-foreground mb-1">
            Study Area
          </h1>
          <p className="text-muted-foreground text-sm max-w-2xl">
            Select a course to access the AI Tutor, formulas, quizzes, and documents.
          </p>
        </div>
        
        {/* Compact Filters */}
        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
          <div className="relative w-full sm:w-64">
            <Building2 className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <select
              value={selectedOrgUnit}
              onChange={(e) => {
                setSelectedOrgUnit(e.target.value);
                setSelectedOffering('');
              }}
              className="w-full pl-9 pr-8 py-2 text-sm bg-card border border-border rounded-lg appearance-none focus:outline-none focus:ring-1 focus:ring-accent transition-all cursor-pointer"
            >
              <option value="">All Organizations</option>
              {orgUnits.map(dept => (
                <option key={dept.id} value={dept.id}>{dept.name}</option>
              ))}
            </select>
          </div>
          <div className="relative w-full sm:w-64">
            <Layers className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <select
              value={selectedOffering}
              onChange={(e) => setSelectedOffering(e.target.value)}
              disabled={!selectedOrgUnit}
              className="w-full pl-9 pr-8 py-2 text-sm bg-card border border-border rounded-lg appearance-none focus:outline-none focus:ring-1 focus:ring-accent transition-all cursor-pointer disabled:opacity-50"
            >
              <option value="">All Offerings</option>
              {offerings.map(off => (
                <option key={off.id} value={off.id}>{off.name}</option>
              ))}
            </select>
          </div>
          <div className="w-full sm:w-64">
            <MarketplaceSearch
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              orgUnits={orgUnits}
              studyUnits={studyUnits}
              onStudyUnitSelect={(id) => navigate(`/study-units/${id}/analyze`)}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {loadingStudyUnits ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-48 bg-muted/50 rounded-xl animate-pulse border border-border/50" />
            ))}
          </div>
        ) : filteredStudyUnits.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4 flex items-center justify-center">
              <SearchX size={40} />
            </div>
            <h3 className="text-lg font-serif font-semibold text-foreground mb-1">No courses found</h3>
            <p className="text-sm text-muted-foreground">Try adjusting your search criteria or selecting a different organization.</p>
            <button
              onClick={() => { setSearchTerm(''); setSelectedOrgUnit(''); setSelectedOffering(''); }}
              className="mt-4 px-4 py-2 border border-border text-xs text-foreground font-medium rounded-lg hover:bg-muted transition-colors"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredStudyUnits.map((study_unit) => (
              <StudyUnitCard
                key={study_unit.id}
                study_unit={study_unit}
                org_unitName={getDeptName(study_unit.org_unit_id)}
              />
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Marketplace;

