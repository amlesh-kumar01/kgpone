import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../lib/api';
import { useToast } from "@/hooks/use-toast";

import { academicApi } from '../lib/academicApi';

const AcademicContext = createContext(null);

export const AcademicProvider = ({ children }) => {
  const [orgUnits, setOrgUnits] = useState([]);
  const [studyUnits, setStudyUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const fetchAcademicData = async () => {
    setLoading(true);
    try {
      // Fetch both orgUnits and studyUnits concurrently
      const [deptRes, study_unitRes] = await Promise.all([
        academicApi.getOrgUnits(),
        academicApi.getAllStudyUnits()
      ]);
      setOrgUnits(deptRes.data.data || []);
      setStudyUnits(study_unitRes.data.data || []);
    } catch (err) {
      console.error("Failed to fetch academic data:", err);
      toast({
        variant: "destructive",
        title: "Data Sync Failed",
        description: "Could not load academic catalog. Please refresh.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAcademicData();
  }, []);

  const refreshAcademicData = async () => {
    await fetchAcademicData();
  };

  const addOrgUnit = async (org_unitData) => {
    try {
      const res = await academicApi.createOrgUnit(org_unitData);
      if (res.data.status === 'success') {
        setOrgUnits(prev => [...prev, res.data.data]);
        return res.data.data;
      }
      throw new Error(res.data.message);
    } catch (err) {
      console.error("Failed to add org_unit:", err);
      throw err;
    }
  };

  return (
    <AcademicContext.Provider value={{ orgUnits, studyUnits, loading, refreshAcademicData, addOrgUnit }}>
      {children}
    </AcademicContext.Provider>
  );
};

export const useAcademic = () => {
  const context = useContext(AcademicContext);
  if (!context) {
    throw new Error("useAcademic must be used within an AcademicProvider");
  }
  return context;
};
