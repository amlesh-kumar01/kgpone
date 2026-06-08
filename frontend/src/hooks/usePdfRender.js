import { useState } from 'react';

export const usePdfRender = () => {
  const [pdfData] = useState(null);

  const loadPdf = () => {
    // Implementation
  };

  return { pdfData, loadPdf };
};
