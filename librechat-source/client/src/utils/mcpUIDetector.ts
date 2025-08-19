import type { Artifact, ArtifactType } from '~/common';
import { logger } from '~/utils';

/**
 * Detects MCP UI resources in message content and creates artifacts for them
 */
export function detectMCPUIResources(content: string, messageId: string): Artifact[] {
  const artifacts: Artifact[] = [];
  
  try {
    // Check if content contains MCP UI resource markers
    // These could be in various formats depending on how the server sends them
    
    // Pattern 1: JSON block with ui:// URI
    const uiResourcePattern = /```json\s*\n({[\s\S]*?"uri"\s*:\s*"ui:\/\/[^"]+[\s\S]*?})\s*\n```/g;
    let match;
    
    while ((match = uiResourcePattern.exec(content)) !== null) {
      try {
        const resourceData = JSON.parse(match[1]);
        if (resourceData.uri?.startsWith('ui://')) {
          const artifact: Artifact = {
            id: `mcp-ui-${messageId}-${artifacts.length}`,
            type: 'mcp_ui' as any,
            title: resourceData.title || 'MCP UI Resource',
            content: JSON.stringify(resourceData),
            mcpResource: resourceData,
            messageId,
            lastUpdateTime: Date.now(),
            index: artifacts.length,
          };
          artifacts.push(artifact);
          logger.log('mcp', 'Detected MCP UI resource', resourceData);
        }
      } catch (err) {
        logger.error('Failed to parse potential MCP UI resource', err);
      }
    }
    
    // Pattern 2: Direct MCP UI resource tags (if server sends them this way)
    const mcpUITagPattern = /<mcp-ui-resource[^>]*>([\s\S]*?)<\/mcp-ui-resource>/g;
    
    while ((match = mcpUITagPattern.exec(content)) !== null) {
      try {
        const resourceContent = match[1].trim();
        const resourceData = JSON.parse(resourceContent);
        
        const artifact: Artifact = {
          id: `mcp-ui-${messageId}-${artifacts.length}`,
          type: 'mcp_ui' as any,
          title: resourceData.title || 'MCP UI Resource',
          content: resourceContent,
          mcpResource: resourceData,
          messageId,
          lastUpdateTime: Date.now(),
          index: artifacts.length,
        };
        artifacts.push(artifact);
        logger.log('mcp', 'Detected MCP UI resource tag', resourceData);
      } catch (err) {
        logger.error('Failed to parse MCP UI resource tag', err);
      }
    }
    
    // Pattern 3: Check for tool responses that might contain UI resources
    const toolResponsePattern = /tool_response:?\s*({[\s\S]*?"type"\s*:\s*"resource"[\s\S]*?})/g;
    
    while ((match = toolResponsePattern.exec(content)) !== null) {
      try {
        const responseData = JSON.parse(match[1]);
        if (responseData.type === 'resource' && responseData.resource?.uri?.startsWith('ui://')) {
          const artifact: Artifact = {
            id: `mcp-ui-${messageId}-${artifacts.length}`,
            type: 'mcp_ui' as any,
            title: responseData.resource.name || 'MCP Tool Response',
            content: JSON.stringify(responseData.resource),
            mcpResource: responseData.resource,
            messageId,
            lastUpdateTime: Date.now(),
            index: artifacts.length,
          };
          artifacts.push(artifact);
          logger.log('mcp', 'Detected MCP UI resource in tool response', responseData);
        }
      } catch (err) {
        logger.error('Failed to parse tool response', err);
      }
    }
    
  } catch (error) {
    logger.error('Error detecting MCP UI resources', error);
  }
  
  return artifacts;
}

/**
 * Checks if a given object is an MCP UI resource
 */
export function isMCPUIResource(obj: any): boolean {
  if (!obj || typeof obj !== 'object') {
    return false;
  }
  
  // Check for UI resource URI
  if (obj.uri?.startsWith('ui://')) {
    return true;
  }
  
  // Check for resource type with UI URI
  if (obj.type === 'resource' && obj.resource?.uri?.startsWith('ui://')) {
    return true;
  }
  
  // Check for MCP UI specific properties
  if (obj.mimeType && (obj.text || obj.blob || obj.url)) {
    return true;
  }
  
  return false;
}

/**
 * Extracts MCP UI resources from a message's tool calls or content
 */
export function extractMCPUIFromMessage(message: any): Artifact[] {
  const artifacts: Artifact[] = [];
  
  // Check tool calls
  if (message.toolCalls && Array.isArray(message.toolCalls)) {
    message.toolCalls.forEach((toolCall: any, index: number) => {
      if (toolCall.result && isMCPUIResource(toolCall.result)) {
        const artifact: Artifact = {
          id: `mcp-ui-tool-${message.messageId}-${index}`,
          type: 'mcp_ui' as any,
          title: toolCall.name || 'MCP Tool Result',
          content: JSON.stringify(toolCall.result),
          mcpResource: toolCall.result,
          messageId: message.messageId,
          lastUpdateTime: Date.now(),
          index,
        };
        artifacts.push(artifact);
      }
    });
  }
  
  // Check message content for embedded resources
  if (message.text || message.content) {
    const contentArtifacts = detectMCPUIResources(
      message.text || message.content,
      message.messageId
    );
    artifacts.push(...contentArtifacts);
  }
  
  return artifacts;
}