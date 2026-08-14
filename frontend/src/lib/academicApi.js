import api from './api';

export const academicApi = {
  // Organizational Units
  getOrgUnits: () => api.get('/api/v1/academic/org-units'),
  createOrgUnit: (data) => api.post('/api/v1/academic/org-units', data),
  
  // Offerings
  getOfferings: (orgUnitId) => api.get(`/api/v1/academic/org-units/${orgUnitId}/offerings`),
  createOffering: (orgUnitId, data) => api.post(`/api/v1/academic/org-units/${orgUnitId}/offerings`, data),
  deleteOffering: (offeringId) => api.delete(`/api/v1/academic/offerings/${offeringId}`),
  
  // Study Units
  getAllStudyUnits: () => api.get('/api/v1/academic/study-units'),
  getStudyUnits: (orgUnitId) => api.get(`/api/v1/academic/org-units/${orgUnitId}/study-units`),
  createStudyUnit: (orgUnitId, data) => api.post(`/api/v1/academic/org-units/${orgUnitId}/study-units`, data),
  deleteStudyUnit: (studyUnitId) => api.delete(`/api/v1/academic/study-units/${studyUnitId}`),
  
  // Map StudyUnit <-> Offering
  linkOffering: (studyUnitId, offeringId) => api.post(`/api/v1/academic/study-units/${studyUnitId}/offerings`, { offering_id: offeringId }),
  unlinkOffering: (studyUnitId, offeringId) => api.delete(`/api/v1/academic/study-units/${studyUnitId}/offerings/${offeringId}`),
};
