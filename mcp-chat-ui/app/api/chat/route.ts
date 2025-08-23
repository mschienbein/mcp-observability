import { streamText } from 'ai';
import { bedrock } from '@ai-sdk/amazon-bedrock';
import { MCPToolHandler } from '@/lib/mcp/handler';
import { MCPServerConfig } from '@/lib/mcp/types';

// No need to pre-configure Bedrock client in v3

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { messages = [], mcpServers = [], model = 'anthropic.claude-3-sonnet-20240229-v1:0' } = body;

    // Validate messages
    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid request',
          details: 'Messages array is required'
        }),
        { 
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }

    // Initialize MCP handler if servers are provided
    let mcpHandler: MCPToolHandler | null = null;
    let tools = {};

    if (mcpServers && mcpServers.length > 0) {
      mcpHandler = new MCPToolHandler(mcpServers as MCPServerConfig[]);
      await mcpHandler.initialize();
      tools = mcpHandler.getTools();
    }

    // Stream response from Bedrock
    const result = streamText({
      model: bedrock(model, {
        region: process.env.AWS_REGION || 'us-east-1',
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      }),
      messages: messages,
      tools: Object.keys(tools).length > 0 ? tools : undefined,
      system: 'You are a helpful assistant with access to various tools through MCP (Model Context Protocol). When you receive UI resources (starting with ui://), describe what you would display to the user.',
      maxTokens: 4096,
      temperature: 0.7,
      onFinish: async () => {
        // Cleanup MCP connections
        if (mcpHandler) {
          await mcpHandler.cleanup();
        }
      },
    });

    return result.toTextStreamResponse();
  } catch (error) {
    console.error('Chat API error:', error);
    
    // Return a proper error response
    return new Response(
      JSON.stringify({ 
        error: 'An error occurred while processing your request',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle OPTIONS for CORS
export async function OPTIONS(req: Request) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}