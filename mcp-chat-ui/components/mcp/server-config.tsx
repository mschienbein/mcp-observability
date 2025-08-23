'use client';

import { useState } from 'react';
import { MCPServerConfig } from '@/lib/mcp/types';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select } from '../ui/select';
import { Switch } from '../ui/switch';
import { Plus, Trash2, X } from 'lucide-react';

interface Props {
  servers: MCPServerConfig[];
  onUpdate: (servers: MCPServerConfig[]) => void;
  onClose: () => void;
}

export function ServerConfig({ servers, onUpdate, onClose }: Props) {
  const [localServers, setLocalServers] = useState<MCPServerConfig[]>(servers);
  const [newServer, setNewServer] = useState<Partial<MCPServerConfig>>({
    transport: 'http',
    enabled: true,
  });

  const handleAddServer = () => {
    if (!newServer.name || !newServer.transport) {
      alert('Please provide a server name and transport type');
      return;
    }

    const server: MCPServerConfig = {
      id: `server-${Date.now()}`,
      name: newServer.name,
      transport: newServer.transport as 'stdio' | 'http' | 'sse',
      enabled: newServer.enabled ?? true,
      url: newServer.url,
      command: newServer.command,
      args: newServer.args,
      headers: newServer.headers,
    };

    const updatedServers = [...localServers, server];
    setLocalServers(updatedServers);
    setNewServer({ transport: 'http', enabled: true });
  };

  const handleRemoveServer = (id: string) => {
    const updatedServers = localServers.filter(s => s.id !== id);
    setLocalServers(updatedServers);
  };

  const handleToggleServer = (id: string) => {
    const updatedServers = localServers.map(s =>
      s.id === id ? { ...s, enabled: !s.enabled } : s
    );
    setLocalServers(updatedServers);
  };

  const handleSave = () => {
    onUpdate(localServers);
    
    // Save to backend
    localServers.forEach(server => {
      fetch('/api/mcp', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(server),
      });
    });
    
    onClose();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">MCP Server Configuration</h3>
        <Button onClick={onClose} variant="ghost" size="sm">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Existing Servers */}
      <div className="space-y-2">
        {localServers.map((server) => (
          <div
            key={server.id}
            className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <Switch
                checked={server.enabled}
                onCheckedChange={() => handleToggleServer(server.id)}
              />
              <div>
                <p className="font-medium">{server.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {server.transport} - {server.url || server.command || 'Not configured'}
                </p>
              </div>
            </div>
            <Button
              onClick={() => handleRemoveServer(server.id)}
              variant="ghost"
              size="sm"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      {/* Add New Server */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <h4 className="font-medium mb-3">Add New Server</h4>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="name">Server Name</Label>
            <Input
              id="name"
              value={newServer.name || ''}
              onChange={(e) => setNewServer({ ...newServer, name: e.target.value })}
              placeholder="My MCP Server"
            />
          </div>
          
          <div>
            <Label htmlFor="transport">Transport Type</Label>
            <select
              id="transport"
              value={newServer.transport}
              onChange={(e) => setNewServer({ ...newServer, transport: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
            >
              <option value="http">HTTP</option>
              <option value="sse">SSE</option>
              <option value="stdio">Stdio</option>
            </select>
          </div>

          {(newServer.transport === 'http' || newServer.transport === 'sse') && (
            <div className="col-span-2">
              <Label htmlFor="url">Server URL</Label>
              <Input
                id="url"
                value={newServer.url || ''}
                onChange={(e) => setNewServer({ ...newServer, url: e.target.value })}
                placeholder="https://example.com/mcp"
              />
            </div>
          )}

          {newServer.transport === 'stdio' && (
            <>
              <div>
                <Label htmlFor="command">Command</Label>
                <Input
                  id="command"
                  value={newServer.command || ''}
                  onChange={(e) => setNewServer({ ...newServer, command: e.target.value })}
                  placeholder="node"
                />
              </div>
              <div>
                <Label htmlFor="args">Arguments</Label>
                <Input
                  id="args"
                  value={newServer.args?.join(' ') || ''}
                  onChange={(e) => setNewServer({ ...newServer, args: e.target.value.split(' ').filter(Boolean) })}
                  placeholder="./server.js"
                />
              </div>
            </>
          )}
        </div>

        <div className="flex justify-between mt-4">
          <Button onClick={handleAddServer} variant="outline" size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Server
          </Button>
          
          <Button onClick={handleSave}>
            Save Configuration
          </Button>
        </div>
      </div>
    </div>
  );
}