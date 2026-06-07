import { useState } from 'react';

export const usePdfRender = () => {
  const [pdfData, setPdfData] = useState(null);

  const loadPdf = (url) => {
    // Implementation
  };

  return { pdfData, loadPdf };
};
