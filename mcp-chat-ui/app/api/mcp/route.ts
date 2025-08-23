import { NextResponse } from 'next/server';
import { MCPClient } from '@/lib/mcp/client';
import { MCPServerConfig } from '@/lib/mcp/types';

// In-memory storage for demo (replace with database in production)
const serverConfigs: Map<string, MCPServerConfig> = new Map();

// Initialize with servers from environment or defaults
function initializeServers() {
  const envServers = process.env.MCP_SERVERS;
  if (envServers) {
    try {
      const servers = JSON.parse(envServers) as MCPServerConfig[];
      servers.forEach(server => {
        serverConfigs.set(server.id, server);
      });
      return;
    } catch (e) {
      console.error('Failed to parse MCP_SERVERS:', e);
    }
  }
  
  // Add default servers if none configured
  serverConfigs.set('agentcore', {
    id: 'agentcore',
    name: 'AgentCore Experiment',
    transport: 'http',
    url: process.env.MCP_AGENTCORE_URL || '',
    headers: {
      'authorization': `Bearer ${process.env.MCP_AGENTCORE_TOKEN || ''}`,
      'Content-Type': 'application/json'
    },
    enabled: false,
  });
  
  serverConfigs.set('local-tools', {
    id: 'local-tools',
    name: 'Local Tools Server',
    transport: 'http',
    url: 'http://localhost:3002',
    enabled: false,
  });
  
  serverConfigs.set('local-feedback', {
    id: 'local-feedback',
    name: 'Local Feedback Server',
    transport: 'http',
    url: 'http://localhost:3003',
    enabled: false,
  });
}

// Initialize on module load
initializeServers();

export async function GET() {
  // Return all server configurations
  const servers = Array.from(serverConfigs.values());
  return NextResponse.json({ servers });
}

export async function POST(req: Request) {
  try {
    const server: MCPServerConfig = await req.json();
    
    // Validate server config
    if (!server.id || !server.name || !server.transport) {
      return NextResponse.json(
        { error: 'Invalid server configuration' },
        { status: 400 }
      );
    }

    // Test connection
    const client = new MCPClient();
    try {
      await client.connect(server);
      await client.disconnect(server.id);
    } catch (error) {
      return NextResponse.json(
        { 
          error: 'Failed to connect to server',
          details: error instanceof Error ? error.message : 'Unknown error'
        },
        { status: 400 }
      );
    }

    // Save server config
    serverConfigs.set(server.id, server);
    
    return NextResponse.json({ 
      message: 'Server added successfully',
      server 
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to add server' },
      { status: 500 }
    );
  }
}

export async function PUT(req: Request) {
  try {
    const { id, ...updates }: Partial<MCPServerConfig> = await req.json();
    
    if (!id) {
      return NextResponse.json(
        { error: 'Server ID is required' },
        { status: 400 }
      );
    }

    const existingServer = serverConfigs.get(id);
    if (!existingServer) {
      return NextResponse.json(
        { error: 'Server not found' },
        { status: 404 }
      );
    }

    // Update server config
    const updatedServer = { ...existingServer, ...updates };
    serverConfigs.set(id, updatedServer);
    
    return NextResponse.json({ 
      message: 'Server updated successfully',
      server: updatedServer 
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update server' },
      { status: 500 }
    );
  }
}

export async function DELETE(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    
    if (!id) {
      return NextResponse.json(
        { error: 'Server ID is required' },
        { status: 400 }
      );
    }

    if (!serverConfigs.has(id)) {
      return NextResponse.json(
        { error: 'Server not found' },
        { status: 404 }
      );
    }

    serverConfigs.delete(id);
    
    return NextResponse.json({ 
      message: 'Server deleted successfully' 
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to delete server' },
      { status: 500 }
    );
  }
}