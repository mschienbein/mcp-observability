import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
import { MCPServerConfig, MCPTool } from './types';

export class MCPClient {
  private clients: Map<string, Client> = new Map();
  private tools: Map<string, MCPTool[]> = new Map();

  async connect(server: MCPServerConfig): Promise<Client> {
    if (!server.enabled) {
      throw new Error(`Server ${server.name} is not enabled`);
    }

    try {
      const transport = await this.createTransport(server);
      const client = new Client(
        {
          name: 'mcp-chat-ui',
          version: '1.0.0',
        },
        {
          capabilities: {},
        }
      );

      await client.connect(transport);
      this.clients.set(server.id, client);

      // Fetch available tools
      const toolsResponse = await client.request(
        { method: 'tools/list' },
        { timeout: 10000 }
      );

      if (toolsResponse.tools) {
        this.tools.set(server.id, toolsResponse.tools);
      }

      return client;
    } catch (error) {
      console.error(`Failed to connect to ${server.name}:`, error);
      throw error;
    }
  }

  async disconnect(serverId: string): Promise<void> {
    const client = this.clients.get(serverId);
    if (client) {
      await client.close();
      this.clients.delete(serverId);
      this.tools.delete(serverId);
    }
  }

  async disconnectAll(): Promise<void> {
    for (const [id] of this.clients) {
      await this.disconnect(id);
    }
  }

  getClient(serverId: string): Client | undefined {
    return this.clients.get(serverId);
  }

  getTools(serverId?: string): MCPTool[] {
    if (serverId) {
      return this.tools.get(serverId) || [];
    }
    
    // Return all tools from all connected servers
    const allTools: MCPTool[] = [];
    for (const tools of this.tools.values()) {
      allTools.push(...tools);
    }
    return allTools;
  }

  private async createTransport(server: MCPServerConfig) {
    switch (server.transport) {
      case 'stdio':
        if (!server.command) {
          throw new Error('Command is required for stdio transport');
        }
        return new StdioClientTransport({
          command: server.command,
          args: server.args || [],
        });

      case 'sse':
        if (!server.url) {
          throw new Error('URL is required for SSE transport');
        }
        return new SSEClientTransport(server.url);

      case 'http':
        if (!server.url) {
          throw new Error('URL is required for HTTP transport');
        }
        // For HTTP, we'll use a custom implementation or the SSE transport
        // depending on the server's capabilities
        return new SSEClientTransport(server.url);

      default:
        throw new Error(`Unsupported transport: ${server.transport}`);
    }
  }

  async callTool(serverId: string, toolName: string, args: any): Promise<any> {
    const client = this.clients.get(serverId);
    if (!client) {
      throw new Error(`No client connected for server ${serverId}`);
    }

    try {
      const response = await client.request(
        {
          method: 'tools/call',
          params: {
            name: toolName,
            arguments: args,
          },
        },
        { timeout: 30000 }
      );

      return response;
    } catch (error) {
      console.error(`Failed to call tool ${toolName}:`, error);
      throw error;
    }
  }
}