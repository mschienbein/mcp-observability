# LibreChat Artifacts System & MCP-UI Integration Plan

## Table of Contents
1. [LibreChat Artifact System Overview](#librechat-artifact-system-overview)
2. [Current Architecture](#current-architecture)
3. [Adding New Artifact Types](#adding-new-artifact-types)
4. [MCP-UI Integration Strategy](#mcp-ui-integration-strategy)
5. [Implementation Plan](#implementation-plan)

## LibreChat Artifact System Overview

LibreChat implements a sophisticated artifact system that allows AI assistants to generate, display, and interact with various types of content beyond simple text responses. The system is built with React, TypeScript, and Recoil for state management.

### Key Features
- **Multi-format Support**: Code blocks, previews, Mermaid diagrams
- **Interactive UI**: Tabbed interface with preview and code views
- **State Persistence**: Artifacts stored and managed via Recoil atoms
- **Download & Copy**: Built-in functionality for exporting artifacts
- **Live Preview**: Sandboxed execution environment for web code

## Current Architecture

### Component Structure
```
client/src/components/Artifacts/
├── Artifacts.tsx           # Main container component
├── Artifact.tsx            # Individual artifact management
├── ArtifactTabs.tsx        # Tab navigation
├── ArtifactCodeEditor.tsx  # Code editing interface
├── ArtifactPreview.tsx     # Sandboxed preview
├── ArtifactButton.tsx      # Interaction controls
├── Code.tsx                # Code rendering with syntax highlighting
├── DownloadArtifact.tsx    # Export functionality
├── Mermaid.tsx             # Diagram rendering
└── Thinking.tsx            # Loading/processing states
```

### Data Model
```typescript
interface Artifact {
  id: string;                // Unique identifier
  identifier: string;         // User-facing identifier
  title: string;             // Display title
  type: string;              // Artifact type (code, mermaid, etc.)
  content: string;           // Raw content
  messageId: string;         // Associated message ID
  index: number;             // Order index
  lastUpdateTime: number;    // Timestamp
}
```

### State Management
LibreChat uses Recoil atoms for artifact state:
- `artifactsState`: Complete artifact collection (`Record<string, Artifact>`)
- `currentArtifactId`: Currently selected artifact
- `artifactsVisibility`: Global visibility toggle
- `visibleArtifacts`: Filtered subset of artifacts

### Rendering Pipeline
1. **Creation**: Artifacts generated in message context
2. **Storage**: Saved to Recoil state with throttled updates
3. **Display**: Rendered in tabbed interface
4. **Interaction**: Copy, download, preview actions available

## Adding New Artifact Types

### Step 1: Define the Artifact Type
```typescript
// In common types or artifacts store
export enum ArtifactType {
  CODE = 'code',
  MERMAID = 'mermaid',
  HTML = 'html',
  MARKDOWN = 'markdown',
  // Add new types here
  MCP_UI = 'mcp_ui',
  INTERACTIVE_TOOL = 'interactive_tool',
  DATA_VISUALIZATION = 'data_viz'
}
```

### Step 2: Create Type-Specific Component
```typescript
// client/src/components/Artifacts/MCPUIArtifact.tsx
import React from 'react';
import { MCPUIResource } from '@mcp-ui/core';

interface MCPUIArtifactProps {
  content: string;
  metadata?: Record<string, any>;
}

export const MCPUIArtifact: React.FC<MCPUIArtifactProps> = ({ 
  content, 
  metadata 
}) => {
  const resource = JSON.parse(content);
  
  return (
    <div className="mcp-ui-artifact">
      <MCPUIResource 
        resource={resource}
        onInteraction={handleInteraction}
      />
    </div>
  );
};
```

### Step 3: Update Artifact Renderer
```typescript
// In Artifacts.tsx or ArtifactPreview.tsx
const renderArtifactContent = (artifact: Artifact) => {
  switch(artifact.type) {
    case 'code':
      return <Code content={artifact.content} />;
    case 'mermaid':
      return <Mermaid content={artifact.content} />;
    case 'mcp_ui':
      return <MCPUIArtifact content={artifact.content} />;
    default:
      return <DefaultArtifact content={artifact.content} />;
  }
};
```

### Step 4: Add Type Detection Logic
```typescript
// In message processing or artifact creation
const detectArtifactType = (content: string, metadata?: any): string => {
  if (metadata?.type === 'mcp_ui_resource') {
    return 'mcp_ui';
  }
  if (content.startsWith('```mermaid')) {
    return 'mermaid';
  }
  if (content.includes('<mcp-ui>')) {
    return 'mcp_ui';
  }
  // Default fallback
  return 'code';
};
```

### Step 5: Configure Preview Actions
```typescript
// Add specific actions for new artifact type
const getArtifactActions = (type: string) => {
  const baseActions = ['copy', 'download'];
  
  switch(type) {
    case 'mcp_ui':
      return [...baseActions, 'interact', 'export_state'];
    case 'data_viz':
      return [...baseActions, 'export_csv', 'fullscreen'];
    default:
      return baseActions;
  }
};
```

## MCP-UI Integration Strategy

### Architecture Overview
```
┌─────────────────────────────────────────────┐
│              LibreChat Frontend              │
├─────────────────────────────────────────────┤
│          Artifacts System (Enhanced)         │
│  ┌─────────────┐  ┌───────────────────┐    │
│  │   Standard  │  │   MCP-UI Bridge    │    │
│  │  Artifacts  │  │  ┌──────────────┐  │    │
│  └─────────────┘  │  │ @mcp-ui/core │  │    │
│                   │  └──────────────┘  │    │
│                   └───────────────────┘    │
├─────────────────────────────────────────────┤
│           LibreChat Backend API             │
│  ┌─────────────────────────────────────┐    │
│  │         MCP Server Manager          │    │
│  │  ┌─────────┐  ┌─────────────────┐  │    │
│  │  │   MCP   │  │   MCP Protocol   │  │    │
│  │  │ Servers │←→│     Client       │  │    │
│  │  └─────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### Integration Points

#### 1. MCP Server Connection Management
```typescript
// New component: MCPServerManager.tsx
interface MCPServer {
  id: string;
  name: string;
  url: string;
  transport: 'stdio' | 'http' | 'websocket';
  status: 'connected' | 'disconnected' | 'error';
  capabilities: string[];
}

// Add to LibreChat's conversation context
interface ConversationContext {
  // Existing fields...
  mcpServers: MCPServer[];
  mcpResources: MCPUIResource[];
}
```

#### 2. Message Processing Enhancement
```typescript
// Extend message processor to handle MCP responses
const processAssistantMessage = async (message: Message) => {
  const { content, mcpResources } = message;
  
  // Check for MCP UI resources in response
  if (mcpResources && mcpResources.length > 0) {
    mcpResources.forEach(resource => {
      createArtifact({
        type: 'mcp_ui',
        content: JSON.stringify(resource),
        title: resource.title || 'MCP Resource',
        metadata: {
          serverName: resource.serverName,
          resourceType: resource.type
        }
      });
    });
  }
  
  // Continue normal message processing
  return processStandardContent(content);
};
```

#### 3. MCP Client Integration
```typescript
// services/mcpClient.ts
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { MCPUIResource } from '@mcp-ui/core';

class MCPClientManager {
  private clients: Map<string, Client> = new Map();
  
  async connectServer(config: MCPServerConfig) {
    const client = new Client({
      name: 'librechat-mcp-client',
      version: '1.0.0'
    });
    
    await client.connect(config.transport);
    this.clients.set(config.id, client);
    
    // Subscribe to UI resources
    client.on('ui_resource', (resource: MCPUIResource) => {
      this.handleUIResource(resource);
    });
  }
  
  private handleUIResource(resource: MCPUIResource) {
    // Send to artifact system
    window.dispatchEvent(new CustomEvent('mcp-ui-resource', {
      detail: resource
    }));
  }
}
```

#### 4. UI Resource Rendering
```typescript
// components/Artifacts/MCPUIRenderer.tsx
import { MCPUIProvider, MCPUIResource } from '@mcp-ui/react';
import { useMCPClient } from '~/hooks/useMCPClient';

export const MCPUIRenderer: React.FC<{ artifact: Artifact }> = ({ 
  artifact 
}) => {
  const mcpClient = useMCPClient();
  const resource = JSON.parse(artifact.content);
  
  return (
    <MCPUIProvider client={mcpClient}>
      <div className="mcp-ui-container">
        <MCPUIResource
          resource={resource}
          onAction={async (action) => {
            const result = await mcpClient.executeAction(action);
            // Handle action result
          }}
        />
      </div>
    </MCPUIProvider>
  );
};
```

### Configuration Requirements

#### Backend Configuration
```yaml
# config.yaml or environment variables
mcp:
  enabled: true
  servers:
    - name: "tools-server"
      transport: "http"
      url: "http://localhost:3002"
      capabilities: ["tools", "ui_resources"]
    - name: "feedback-server"
      transport: "http"
      url: "http://localhost:3003"
      capabilities: ["feedback", "ui_resources"]
```

#### Frontend Configuration
```typescript
// client/src/config/mcp.ts
export const MCP_CONFIG = {
  enableUIResources: true,
  autoConnect: true,
  resourceTypes: ['form', 'chart', 'table', 'interactive'],
  maxResourceSize: 1024 * 1024, // 1MB
  renderTimeout: 5000
};
```

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. **Set up MCP client infrastructure**
   - Install @modelcontextprotocol/sdk
   - Create MCPClientManager service
   - Add server configuration UI

2. **Extend artifact system**
   - Add MCP UI artifact type
   - Create base MCPUIArtifact component
   - Update artifact detection logic

### Phase 2: Core Integration (Week 2-3)
1. **Integrate @mcp-ui/core**
   - Install MCP-UI dependencies
   - Create MCPUIProvider wrapper
   - Implement resource renderer

2. **Message processing**
   - Extend message handler for MCP resources
   - Add resource extraction logic
   - Create artifact from resources

### Phase 3: Enhanced Features (Week 3-4)
1. **Interactive capabilities**
   - Implement action handling
   - Add state management for interactions
   - Create feedback loop to MCP servers

2. **Server management UI**
   - Build server connection interface
   - Add status indicators
   - Implement reconnection logic

### Phase 4: Testing & Polish (Week 4-5)
1. **Testing**
   - Unit tests for MCP components
   - Integration tests with mock servers
   - E2E tests for full workflow

2. **Documentation**
   - User guide for MCP features
   - Developer documentation
   - Configuration examples

### File Structure Changes
```
client/src/
├── components/
│   ├── Artifacts/
│   │   ├── MCPUIArtifact.tsx      # New
│   │   ├── MCPUIRenderer.tsx      # New
│   │   └── ...existing files
│   └── MCP/                       # New directory
│       ├── MCPServerManager.tsx
│       ├── MCPServerList.tsx
│       └── MCPServerConfig.tsx
├── services/
│   ├── mcpClient.ts               # New
│   └── ...existing services
├── hooks/
│   ├── useMCPClient.ts           # New
│   ├── useMCPResources.ts        # New
│   └── ...existing hooks
└── store/
    ├── mcpServers.ts              # New
    └── ...existing stores
```

### Dependencies to Add
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "@mcp-ui/core": "^5.7.0",
    "@mcp-ui/react": "^5.7.0",
    "ws": "^8.0.0"
  }
}
```

### Environment Variables
```bash
# .env additions
MCP_ENABLED=true
MCP_TOOLS_SERVER_URL=http://localhost:3002
MCP_FEEDBACK_SERVER_URL=http://localhost:3003
MCP_UI_RESOURCES_ENABLED=true
MCP_MAX_SERVERS=5
```

### API Endpoints
```typescript
// New API routes needed
POST   /api/mcp/servers/connect     # Connect to MCP server
DELETE /api/mcp/servers/:id         # Disconnect server
GET    /api/mcp/servers              # List connected servers
POST   /api/mcp/resources/:id/action # Execute resource action
GET    /api/mcp/capabilities         # Get server capabilities
```

## Risk Mitigation

### Security Considerations
1. **Sandboxing**: MCP UI resources rendered in isolated context
2. **Permission Model**: User consent for server connections
3. **Resource Validation**: Strict validation of MCP resources
4. **Rate Limiting**: Prevent resource flooding

### Performance Optimization
1. **Lazy Loading**: Load MCP components on demand
2. **Resource Caching**: Cache frequently used resources
3. **Connection Pooling**: Reuse MCP server connections
4. **Throttling**: Limit resource update frequency

### Fallback Strategies
1. **Graceful Degradation**: Show raw content if MCP UI fails
2. **Error Boundaries**: Isolate MCP component failures
3. **Offline Mode**: Cache resources for offline viewing
4. **Alternative Rendering**: Fallback to simple HTML/Markdown

## Success Metrics

### Technical Metrics
- MCP server connection success rate > 95%
- Resource rendering time < 500ms
- Zero critical security vulnerabilities
- Test coverage > 80%

### User Experience Metrics
- User engagement with MCP resources
- Error rate < 1%
- Feature adoption rate
- User satisfaction scores

## Conclusion

Integrating MCP-UI into LibreChat's artifact system is achievable through:
1. Extending the existing artifact architecture
2. Adding MCP client capabilities to the backend
3. Creating specialized UI components for MCP resources
4. Maintaining backward compatibility with existing artifacts

The modular design of LibreChat's artifact system makes it well-suited for this integration, requiring minimal changes to core functionality while adding powerful new capabilities for interactive AI-generated content.