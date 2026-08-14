import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BookOpen, SearchX } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../lib/api';

import MarketplaceSearch from '../components/marketplace/MarketplaceSearch';
import StudyUnitCard from '../components/marketplace/StudyUnitCard';
import OrgUnitSidebar from '../components/marketplace/OrgUnitSidebar';
import { useThrottle } from '../hooks/useThrottle';

const Marketplace = () => {
  const { org_unitId } = useParams();
  const navigate = useNavigate();

  const [studyUnits, setStudyUnits] = useState([]);
  const [orgUnits, setOrgUnits] = useState([]);
  const [loadingStudyUnits, setLoadingStudyUnits] = useState(false);

  const [searchTerm, setSearchTerm] = useState('');
  const throttledSearch = useThrottle(searchTerm, 100);

  // Fetch orgUnits on mount
  useEffect(() => {
    const fetchOrgUnits = async () => {
      try {
        const res = await api.get('/api/v1/academic/orgUnits');
        setOrgUnits(res.data.data || []);
      } catch (err) {
        console.error("Failed to load orgUnits", err);
      }
    };
    fetchOrgUnits();
  }, []);

  // Fetch studyUnits only when org_unit is selected or search term is present
  useEffect(() => {
    const fetchStudyUnits = async () => {
      // "will not fetch all studyUnits by default"
      // Only fetch if a org_unit is selected or user has typed a search term
      if (!org_unitId && !throttledSearch) {
        setStudyUnits([]);
        return;
      }

      setLoadingStudyUnits(true);
      try {
        // If org_unitId exists, fetch for that dept. Else fetch all studyUnits to filter locally
        const params = org_unitId ? { org_unit_id: org_unitId } : {};
        const res = await api.get('/api/v1/academic/', { params });
        setStudyUnits(res.data.data || []);
      } catch (err) {
        console.error("Failed to load studyUnits", err);
      } finally {
        setLoadingStudyUnits(false);
      }
    };

    fetchStudyUnits();
  }, [org_unitId, throttledSearch]);

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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row gap-8">
      {/* Sidebar: Lists orgUnits */}
      <OrgUnitSidebar orgUnits={orgUnits} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="mb-8">
          <h1 className="text-4xl font-serif font-bold text-foreground mb-3">
            StudyUnit Catalog
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl">
            Discover and explore all academic programs available on the platform.
          </p>
        </div>

        <MarketplaceSearch
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
        />

        {loadingStudyUnits ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-64 bg-muted rounded-lg animate-pulse" />
            ))}
          </div>
        ) : !org_unitId && !throttledSearch ? (
          <div className="bg-card border border-border rounded-lg p-16 text-center shadow-sm">
            <div className="mx-auto h-12 w-12 text-accent/50 mb-4 flex items-center justify-center">
              <BookOpen size={48} />
            </div>
            <h3 className="text-xl font-serif font-semibold text-foreground mb-2">Welcome to Marketplace</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              Select a org_unit from the sidebar to view its studyUnits, or search for a specific study_unit by title or code.
            </p>
          </div>
        ) : filteredStudyUnits.length === 0 ? (
          <div className="bg-card border border-border rounded-lg p-16 text-center">
            <div className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4 flex items-center justify-center">
              <SearchX size={48} />
            </div>
            <h3 className="text-xl font-serif font-semibold text-foreground mb-2">No studyUnits found</h3>
            <p className="text-muted-foreground">Try adjusting your search criteria or selecting a different org_unit.</p>
            <button
              onClick={() => { setSearchTerm(''); navigate('/marketplace'); }}
              className="mt-6 px-6 py-3 border border-border text-foreground font-medium rounded-lg hover:bg-muted transition-colors"
            >
              Clear all filters
            </button>
          </div>
        ) : (
          <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 xl:grid-cols-2 gap-6">
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
