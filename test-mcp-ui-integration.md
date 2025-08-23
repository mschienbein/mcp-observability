# MCP-UI Integration Testing Guide

## Summary of Changes

I've successfully integrated MCP-UI support into LibreChat's artifact system. Here's what was added:

### 1. Dependencies Added
- `@mcp-ui/client`: ^5.7.0 - The official MCP UI rendering library

### 2. New Components Created

#### `/client/src/components/Artifacts/MCPUIArtifact.tsx`
- Renders MCP UI resources using the `UIResourceRenderer` from @mcp-ui/client
- Handles resource parsing and error states
- Supports UI action callbacks

#### `/client/src/components/Artifacts/MCPUIRenderer.tsx`
- Wrapper component for MCP UI artifacts
- Handles interaction callbacks
- Ready for integration with LibreChat's MCP infrastructure

### 3. Modified Components

#### `/client/src/components/Artifacts/ArtifactTabs.tsx`
- Added detection for MCP UI artifact types (`mcp_ui` and `interactive_tool`)
- Renders MCP UI resources in preview tab
- Shows JSON representation in code tab

#### `/client/src/common/artifacts.ts`
- Added `ArtifactType` enum with MCP_UI and INTERACTIVE_TOOL types
- Extended `Artifact` interface with:
  - `metadata?: Record<string, any>` - For additional artifact metadata
  - `mcpResource?: any` - For storing MCP UI resource data

### 4. Utility Functions

#### `/client/src/utils/mcpUIDetector.ts`
- `detectMCPUIResources()` - Detects MCP UI resources in message content
- `isMCPUIResource()` - Validates if an object is an MCP UI resource
- `extractMCPUIFromMessage()` - Extracts MCP UI resources from messages

## How MCP UI Resources are Rendered

1. **Detection**: When a message contains MCP UI resources (identified by `ui://` URIs), they are detected and converted to artifacts
2. **Storage**: The resources are stored as artifacts with type `mcp_ui`
3. **Rendering**: The artifact system renders them using the `UIResourceRenderer` component
4. **Interaction**: User interactions with the UI are captured and can be sent back to MCP servers

## Testing the Integration

### Prerequisites
1. Ensure LibreChat is set up and running
2. Have an MCP server that provides UI resources

### Test Steps

1. **Install Dependencies**
   ```bash
   cd librechat-source/client
   npm install
   ```

2. **Start LibreChat**
   ```bash
   npm run dev
   ```

3. **Configure an MCP Server**
   - In LibreChat settings, add an MCP server that provides UI resources
   - Example servers that might provide UI resources:
     - Tools server with form inputs
     - Data visualization servers
     - Interactive configuration servers

4. **Test UI Resource Rendering**
   - Send a message that triggers an MCP tool returning a UI resource
   - The resource should appear as an artifact in the chat
   - You should be able to:
     - View the rendered UI in the "Preview" tab
     - See the JSON representation in the "Code" tab
     - Interact with the UI elements

### Example MCP UI Resource Format

MCP UI resources that will be detected and rendered:

```json
{
  "type": "resource",
  "resource": {
    "uri": "ui://form/config",
    "name": "Configuration Form",
    "mimeType": "text/html",
    "text": "<form><input type='text' placeholder='Enter value'/></form>"
  }
}
```

Or for direct HTML rendering:

```json
{
  "uri": "ui://dashboard",
  "mimeType": "text/html",
  "text": "<div><h2>Dashboard</h2><p>Status: Active</p></div>"
}
```

## Integration with Existing MCP Infrastructure

LibreChat already has comprehensive MCP support including:
- Server connection management (`useMCPServerManager` hook)
- OAuth flow handling
- Tool execution
- Server status monitoring

The MCP-UI integration leverages this existing infrastructure and adds UI rendering capabilities to the artifact system.

## Next Steps for Full Integration

1. **Connect UI Actions to MCP Servers**
   - Currently, UI actions are logged but not executed
   - Need to integrate with LibreChat's MCP manager to execute actions

2. **Add UI Resource Detection in Message Processing**
   - Hook into LibreChat's message processing pipeline
   - Automatically detect and create artifacts for MCP UI resources

3. **Enhance UI Resource Types**
   - Add support for different content types (Remote DOM, external URLs)
   - Implement resource caching and optimization

4. **Testing with Real MCP Servers**
   - Test with various MCP servers that provide UI resources
   - Ensure compatibility with different resource formats

## Troubleshooting

### If UI resources aren't rendering:
1. Check browser console for errors
2. Verify the resource format matches expected structure
3. Ensure @mcp-ui/client is properly installed
4. Check that the artifact type is set to 'mcp_ui'

### If interactions aren't working:
1. Check that onUIAction callback is properly connected
2. Verify MCP server is connected and responding
3. Check browser console for action logs

## Technical Details

The integration follows LibreChat's existing patterns:
- Uses Recoil for state management
- Follows the artifact rendering pipeline
- Maintains compatibility with existing artifact types
- Uses TypeScript for type safety

The implementation is modular and can be extended to support additional MCP UI features as they become available.