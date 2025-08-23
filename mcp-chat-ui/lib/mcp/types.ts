export interface MCPServerConfig {
  id: string;
  name: string;
  transport: 'stdio' | 'http' | 'sse';
  enabled: boolean;
  // For stdio transport
  command?: string;
  args?: string[];
  // For http/sse transport
  url?: string;
  headers?: Record<string, string>;
}

export interface MCPTool {
  name: string;
  description?: string;
  inputSchema?: any;
}

export interface MCPResource {
  uri: string;
  mimeType: 'text/html' | 'text/uri-list' | 'application/vnd.mcp-ui.remote-dom';
  text?: string;
  blob?: string;
}

export interface UIAction {
  type: 'tool' | 'intent' | 'prompt' | 'notify' | 'link';
  payload: any;
  messageId?: string;
}