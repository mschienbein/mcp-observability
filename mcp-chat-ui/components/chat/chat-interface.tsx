'use client';

import { useChat } from '@ai-sdk/react';
import { useState, useEffect } from 'react';
import { MessageList } from './message-list';
import { InputForm } from './input-form';
import { MCPServerConfig } from '@/lib/mcp/types';
import { ServerConfig } from '../mcp/server-config';
import { Button } from '../ui/button';
import { Settings } from 'lucide-react';

export function ChatInterface() {
  const [mcpServers, setMcpServers] = useState<MCPServerConfig[]>([]);
  const [showServerConfig, setShowServerConfig] = useState(false);
  const [selectedModel, setSelectedModel] = useState('anthropic.claude-3-sonnet-20240229-v1:0');

  const { messages, input, handleInputChange, handleSubmit, isLoading, error, reload } = useChat({
    api: '/api/chat',
    body: {
      mcpServers: mcpServers.filter(s => s.enabled),
      model: selectedModel,
    },
    onError: (error) => {
      console.error('Chat error:', error);
    },
  });

  // Load MCP servers on mount
  useEffect(() => {
    fetch('/api/mcp')
      .then(res => res.json())
      .then(data => {
        if (data.servers) {
          setMcpServers(data.servers);
        }
      })
      .catch(console.error);
  }, []);

  const handleServerUpdate = (servers: MCPServerConfig[]) => {
    setMcpServers(servers);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              MCP Chat UI
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Powered by AWS Bedrock & MCP
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="anthropic.claude-3-sonnet-20240229-v1:0">Claude 3 Sonnet</option>
              <option value="anthropic.claude-3-haiku-20240307-v1:0">Claude 3 Haiku</option>
              <option value="anthropic.claude-3-5-sonnet-20241022-v2:0">Claude 3.5 Sonnet</option>
              <option value="meta.llama3-1-70b-instruct-v1:0">Llama 3.1 70B</option>
              <option value="amazon.nova-pro-v1:0">Amazon Nova Pro</option>
            </select>
            
            <Button
              onClick={() => setShowServerConfig(!showServerConfig)}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              <Settings className="h-4 w-4" />
              MCP Servers
            </Button>
          </div>
        </div>
      </header>

      {/* Server Configuration Panel */}
      {showServerConfig && (
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <ServerConfig
              servers={mcpServers}
              onUpdate={handleServerUpdate}
              onClose={() => setShowServerConfig(false)}
            />
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <MessageList messages={messages} />
          
          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
              <p className="font-medium">Error</p>
              <p className="text-sm mt-1">{error.message}</p>
              <Button
                onClick={() => reload()}
                variant="outline"
                size="sm"
                className="mt-2"
              >
                Retry
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Input Form */}
      <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <InputForm
            input={input}
            handleInputChange={handleInputChange}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
}