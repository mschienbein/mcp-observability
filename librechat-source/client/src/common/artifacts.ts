export enum ArtifactType {
  CODE = 'code',
  MERMAID = 'mermaid',
  HTML = 'html',
  MARKDOWN = 'markdown',
  MCP_UI = 'mcp_ui',
  INTERACTIVE_TOOL = 'interactive_tool'
}

export interface CodeBlock {
  id: string;
  language: string;
  content: string;
}

export interface Artifact {
  id: string;
  lastUpdateTime: number;
  index?: number;
  messageId?: string;
  identifier?: string;
  language?: string;
  content?: string;
  title?: string;
  type?: string;
  metadata?: Record<string, any>;
  mcpResource?: any; // MCP UI Resource data
}

export type ArtifactFiles =
  | {
      'App.tsx': string;
      'index.tsx': string;
      '/components/ui/MermaidDiagram.tsx': string;
    }
  | Partial<{
      [x: string]: string | undefined;
    }>;
