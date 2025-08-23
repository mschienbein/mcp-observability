import { MCPClient } from './client';
import { MCPServerConfig } from './types';
import { CoreTool } from 'ai';

export class MCPToolHandler {
  private mcpClient: MCPClient;
  private serverConfigs: MCPServerConfig[];
  private serverToolMap: Map<string, string> = new Map(); // toolName -> serverId

  constructor(servers: MCPServerConfig[]) {
    this.mcpClient = new MCPClient();
    this.serverConfigs = servers;
  }

  async initialize(): Promise<void> {
    // Connect to all enabled servers
    for (const server of this.serverConfigs) {
      if (server.enabled) {
        try {
          await this.mcpClient.connect(server);
          
          // Map tools to their server IDs
          const tools = this.mcpClient.getTools(server.id);
          for (const tool of tools) {
            this.serverToolMap.set(tool.name, server.id);
          }
        } catch (error) {
          console.error(`Failed to connect to ${server.name}:`, error);
        }
      }
    }
  }

  async cleanup(): Promise<void> {
    await this.mcpClient.disconnectAll();
  }

  getTools(): Record<string, CoreTool> {
    const tools: Record<string, CoreTool> = {};
    const allTools = this.mcpClient.getTools();

    for (const tool of allTools) {
      tools[tool.name] = {
        description: tool.description || `MCP tool: ${tool.name}`,
        parameters: tool.inputSchema || {
          type: 'object',
          properties: {},
        },
        execute: async (args: any) => {
          const serverId = this.serverToolMap.get(tool.name);
          if (!serverId) {
            throw new Error(`No server found for tool ${tool.name}`);
          }

          try {
            const result = await this.mcpClient.callTool(serverId, tool.name, args);
            
            // Check if the result contains a UI resource
            if (result?.resource?.uri?.startsWith('ui://')) {
              return {
                type: 'ui-resource',
                resource: result.resource,
              };
            }

            return result;
          } catch (error) {
            console.error(`Error executing tool ${tool.name}:`, error);
            throw error;
          }
        },
      };
    }

    return tools;
  }

  async executeTool(toolName: string, args: any): Promise<any> {
    const serverId = this.serverToolMap.get(toolName);
    if (!serverId) {
      throw new Error(`No server found for tool ${toolName}`);
    }

    return await this.mcpClient.callTool(serverId, toolName, args);
  }
}