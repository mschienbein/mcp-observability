'use client';

import { UIResourceRenderer } from '@mcp-ui/client';
import { MCPResource, UIAction } from '@/lib/mcp/types';

interface Props {
  resource: MCPResource;
  onAction?: (action: UIAction) => void;
}

export function MCPResourceDisplay({ resource, onAction }: Props) {
  if (!resource?.uri?.startsWith('ui://')) {
    return null;
  }

  const handleUIAction = (action: UIAction) => {
    console.log('UI Action received:', action);
    onAction?.(action);
    
    // Handle different action types
    switch (action.type) {
      case 'tool':
        // Tool execution request
        console.log('Tool requested:', action.payload.toolName);
        break;
      case 'prompt':
        // User prompt
        console.log('Prompt:', action.payload.prompt);
        break;
      case 'notify':
        // Notification
        console.log('Notification:', action.payload.message);
        break;
      case 'link':
        // External link
        if (action.payload.url) {
          window.open(action.payload.url, '_blank');
        }
        break;
    }
  };

  return (
    <div className="my-4 rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
      <div className="mb-2 text-sm text-gray-500 dark:text-gray-400">
        MCP UI Resource
      </div>
      <UIResourceRenderer
        resource={resource}
        onUIAction={handleUIAction}
        htmlProps={{
          autoResizeIframe: true,
          style: {
            maxHeight: '500px',
            width: '100%',
            borderRadius: '0.5rem',
            overflow: 'hidden',
          },
          iframeProps: {
            sandbox: 'allow-scripts allow-same-origin allow-forms',
            className: 'rounded-md w-full',
          },
        }}
        supportedContentTypes={['rawHtml', 'externalUrl', 'remoteDom']}
      />
    </div>
  );
}