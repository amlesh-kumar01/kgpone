import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../lib/api';
import { useToast } from "@/hooks/use-toast";

const AcademicContext = createContext(null);

export const AcademicProvider = ({ children }) => {
  const [departments, setDepartments] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const fetchAcademicData = async () => {
    setLoading(true);
    try {
      // Fetch both departments and courses concurrently
      const [deptRes, courseRes] = await Promise.all([
        api.get('/api/v1/academic/departments'),
        api.get('/api/v1/academic/')
      ]);
      setDepartments(deptRes.data.data || []);
      setCourses(courseRes.data.data || []);
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

  const addDepartment = async (departmentData) => {
    try {
      const res = await api.post('/api/v1/academic/departments', departmentData);
      if (res.data.status === 'success') {
        setDepartments(prev => [...prev, res.data.data]);
        return res.data.data;
      }
      throw new Error(res.data.message);
    } catch (err) {
      console.error("Failed to add department:", err);
      throw err;
    }
  };

  return (
    <AcademicContext.Provider value={{ departments, courses, loading, refreshAcademicData, addDepartment }}>
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
