import React, { useCallback } from 'react';
import { useRecoilValue } from 'recoil';
import { logger } from '~/utils';
import MCPUIArtifact from './MCPUIArtifact';
import type { Artifact } from '~/common';

interface MCPUIRendererProps {
  artifact: Artifact;
}

export const MCPUIRenderer: React.FC<MCPUIRendererProps> = ({ artifact }) => {
  
  const handleInteraction = useCallback(async (action: any) => {
    try {
      logger.log('mcp', 'Processing MCP UI interaction', action);
      
      // Here we would integrate with LibreChat's existing MCP infrastructure
      // For now, just log the action
      // TODO: Integrate with LibreChat's MCP manager to execute actions
      
      logger.log('mcp', 'Action to be executed:', action);
      
    } catch (error) {
      logger.error('Failed to process MCP action', error);
    }
  }, []);

  return (
    <MCPUIArtifact 
      artifact={artifact}
      onInteraction={handleInteraction}
    />
  );
};

export default MCPUIRenderer;