import React, { useEffect, useState } from 'react';
import { UIResourceRenderer } from '@mcp-ui/client';
import { useRecoilValue } from 'recoil';
import { logger } from '~/utils';
import type { Artifact } from '~/common';

interface MCPUIArtifactProps {
  artifact: Artifact;
  onInteraction?: (action: any) => void;
}

export const MCPUIArtifact: React.FC<MCPUIArtifactProps> = ({ 
  artifact, 
  onInteraction 
}) => {
  const [resource, setResource] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      // Parse the MCP resource from the artifact content
      if (artifact.mcpResource) {
        setResource(artifact.mcpResource);
      } else if (artifact.content) {
        const parsed = JSON.parse(artifact.content);
        setResource(parsed);
      }
    } catch (err) {
      logger.error('Failed to parse MCP UI resource', err);
      setError('Failed to load MCP UI resource');
    }
  }, [artifact]);

  const handleAction = async (action: any) => {
    logger.log('mcp', 'MCP UI action triggered', action);
    
    if (onInteraction) {
      onInteraction(action);
    }

    // TODO: Send action to MCP server
    // This will be implemented when we add the MCP client infrastructure
  };

  if (error) {
    return (
      <div className="mcp-ui-error p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  if (!resource) {
    return (
      <div className="mcp-ui-loading p-4">
        <p className="text-gray-500">Loading MCP UI resource...</p>
      </div>
    );
  }

  return (
    <div className="mcp-ui-artifact p-4">
      <UIResourceRenderer
        resource={resource}
        onUIAction={handleAction}
      />
    </div>
  );
};

export default MCPUIArtifact;