import { useState } from 'react';
import './MCPServerManager.css';

function MCPServerManager({ mcpClients, onConnect, isConnecting, availableTools }) {
  const [showPanel, setShowPanel] = useState(false);
  const [serverUrl, setServerUrl] = useState('');
  const [serverName, setServerName] = useState('');

  const handleConnect = (e) => {
    e.preventDefault();
    if (serverUrl && serverName) {
      onConnect(serverUrl, serverName);
      setServerUrl('');
      setServerName('');
    }
  };

  const connectedServers = Array.from(mcpClients.keys());

  return (
    <div className="mcp-server-manager">
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="toggle-button"
      >
        🔧 MCP Servers ({connectedServers.length})
      </button>

      {showPanel && (
        <div className="server-panel">
          <div className="panel-header">
            <h3>MCP Server Connections</h3>
            <button onClick={() => setShowPanel(false)} className="close-button">×</button>
          </div>

          <div className="connected-servers">
            <h4>Connected Servers:</h4>
            {connectedServers.length > 0 ? (
              <ul>
                {connectedServers.map(server => (
                  <li key={server}>
                    <span className="server-status">✅</span> {server}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="no-servers">No servers connected</p>
            )}
          </div>

          <div className="add-server">
            <h4>Add New Server:</h4>
            <form onSubmit={handleConnect}>
              <input
                type="text"
                placeholder="Server Name"
                value={serverName}
                onChange={(e) => setServerName(e.target.value)}
                disabled={isConnecting}
              />
              <input
                type="url"
                placeholder="Server URL (e.g., http://localhost:3002)"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                disabled={isConnecting}
              />
              <button type="submit" disabled={isConnecting || !serverUrl || !serverName}>
                {isConnecting ? 'Connecting...' : 'Connect'}
              </button>
            </form>
          </div>

          {availableTools.length > 0 && (
            <div className="tools-summary">
              <h4>Available Tools: {availableTools.length}</h4>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MCPServerManager;