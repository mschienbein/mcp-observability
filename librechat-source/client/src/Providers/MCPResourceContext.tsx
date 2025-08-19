import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface MCPResource {
  uri: string;
  name: string;
  mimeType: string;
  text: string;
}

interface MCPResourceContextType {
  resources: Map<string, MCPResource>;
  addResource: (resource: MCPResource) => void;
  getResource: (uri: string) => MCPResource | undefined;
  clearResources: () => void;
}

const MCPResourceContext = createContext<MCPResourceContextType | undefined>(undefined);

export const MCPResourceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [resources, setResources] = useState<Map<string, MCPResource>>(new Map());

  const addResource = useCallback((resource: MCPResource) => {
    setResources(prev => {
      const newMap = new Map(prev);
      newMap.set(resource.uri, resource);
      return newMap;
    });
  }, []);

  const getResource = useCallback((uri: string) => {
    return resources.get(uri);
  }, [resources]);

  const clearResources = useCallback(() => {
    setResources(new Map());
  }, []);

  return (
    <MCPResourceContext.Provider value={{ resources, addResource, getResource, clearResources }}>
      {children}
    </MCPResourceContext.Provider>
  );
};

export const useMCPResources = () => {
  const context = useContext(MCPResourceContext);
  if (!context) {
    throw new Error('useMCPResources must be used within an MCPResourceProvider');
  }
  return context;
};