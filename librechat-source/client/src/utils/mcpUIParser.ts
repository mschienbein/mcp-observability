/**
 * Parses message text to detect and extract MCP UI resource descriptions
 * These appear in assistant messages after tool calls as markdown links
 */

export interface MCPUIResource {
  uri: string;
  title: string;
  originalText: string;
}

export function parseMCPUIResources(text: string): {
  hasResources: boolean;
  resources: MCPUIResource[];
  cleanText: string;
} {
  if (!text) {
    return { hasResources: false, resources: [], cleanText: text };
  }

  // Pattern to match markdown links with ui:// protocol
  // Format: [Title](ui://type/name)
  const uiLinkPattern = /\[([^\]]+)\]\((ui:\/\/[^)]+)\)/g;
  
  const resources: MCPUIResource[] = [];
  let cleanText = text;
  let match;

  while ((match = uiLinkPattern.exec(text)) !== null) {
    resources.push({
      title: match[1],
      uri: match[2],
      originalText: match[0]
    });
  }

  // Remove the UI resource links from the text
  if (resources.length > 0) {
    cleanText = text.replace(uiLinkPattern, '').trim();
    
    // Also remove lines that are just listing the resources
    const lines = cleanText.split('\n');
    const filteredLines = lines.filter(line => {
      // Remove numbered list items that were just describing resources
      const trimmed = line.trim();
      return !(trimmed.match(/^\d+\.\s*\*\*[^*]+\*\*:\s*$/) || 
               trimmed === '' || 
               trimmed.match(/^-\s*$/));
    });
    
    cleanText = filteredLines.join('\n').trim();
  }

  return {
    hasResources: resources.length > 0,
    resources,
    cleanText
  };
}

/**
 * Checks if a text contains the summary header that appears after tool calls
 */
export function hasMCPUISummaryHeader(text: string): boolean {
  return text.includes('Here are the interactive UIs rendered using') ||
         text.includes('Here are the outputs from each of the mcp-ui-tools');
}