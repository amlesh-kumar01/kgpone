import React from 'react';
import { Outlet } from 'react-router-dom';
import { AcademicProvider } from '../context/AcademicContext';

const AcademicLayout = () => {
  return (
    <AcademicProvider>
      <Outlet />
    </AcademicProvider>
  );
};

export default AcademicLayout;
