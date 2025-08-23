import { useState, useEffect, useRef } from 'react';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { WebSocketClientTransport } from '@modelcontextprotocol/sdk/client/websocket.js';
import './App.css';

// Import components
import ChatInterface from './components/ChatInterface';
import MCPServerManager from './components/MCPServerManager';
import ModelSelector from './components/ModelSelector';

function App() {
  const [messages, setMessages] = useState([]);
  const [mcpClients, setMcpClients] = useState(new Map());
  const [selectedModel, setSelectedModel] = useState(import.meta.env.VITE_DEFAULT_MODEL || 'anthropic.claude-3-haiku-20240307-v1:0');
  const [isConnecting, setIsConnecting] = useState(false);
  const [availableTools, setAvailableTools] = useState([]);

  // Connect to MCP servers
  const connectToMCPServer = async (serverUrl, serverName) => {
    if (mcpClients.has(serverName)) {
      console.log(`Already connected to ${serverName}`);
      return;
    }

    setIsConnecting(true);
    try {
      const client = new Client({
        name: 'mcp-ui-chat',
        version: '1.0.0',
      });

      // For HTTP servers, we'll use fetch instead of WebSocket
      // This is a simplified approach - in production you'd want proper HTTP transport
      const transport = {
        start: async () => {
          console.log(`Connecting to ${serverName} at ${serverUrl}`);
        },
        send: async (message) => {
          const response = await fetch(`${serverUrl}/mcp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(message)
          });
          return response.json();
        },
        close: async () => {
          console.log(`Disconnecting from ${serverName}`);
        }
      };

      await client.connect(transport);
      
      // Get available tools
      const tools = await client.listTools();
      console.log(`Available tools from ${serverName}:`, tools);
      
      setMcpClients(prev => new Map(prev).set(serverName, client));
      setAvailableTools(prev => [...prev, ...tools.tools]);
      
    } catch (error) {
      console.error(`Failed to connect to ${serverName}:`, error);
    } finally {
      setIsConnecting(false);
    }
  };

  // Handle sending messages
  const handleSendMessage = async (content) => {
    const userMessage = { role: 'user', content, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);

    // Call the API to get AI response
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          model: selectedModel,
          tools: availableTools,
        })
      });

      if (!response.ok) throw new Error('Failed to get response');

      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = { role: 'assistant', content: '', timestamp: new Date().toISOString() };
      
      setMessages(prev => [...prev, assistantMessage]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        assistantMessage.content += chunk;
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = { ...assistantMessage };
          return newMessages;
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    }
  };

  // Connect to default MCP servers on mount
  useEffect(() => {
    const toolsServer = import.meta.env.VITE_MCP_TOOLS_SERVER;
    const feedbackServer = import.meta.env.VITE_MCP_FEEDBACK_SERVER;
    
    if (toolsServer) {
      connectToMCPServer(toolsServer, 'tools-server');
    }
    if (feedbackServer) {
      connectToMCPServer(feedbackServer, 'feedback-server');
    }
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>MCP UI Chat</h1>
        <div className="header-controls">
          <ModelSelector 
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
          />
          <MCPServerManager
            mcpClients={mcpClients}
            onConnect={connectToMCPServer}
            isConnecting={isConnecting}
            availableTools={availableTools}
          />
        </div>
      </header>
      
      <main className="app-main">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          availableTools={availableTools}
        />
      </main>
    </div>
  );
}

export default App;