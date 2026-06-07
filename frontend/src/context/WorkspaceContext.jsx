import { createContext, useContext } from 'react';

const WorkspaceContext = createContext(null);

export const WorkspaceProvider = ({ children }) => {
  return (
    <WorkspaceContext.Provider value={{}}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => useContext(WorkspaceContext);
