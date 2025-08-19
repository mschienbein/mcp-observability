import React, { useMemo, useRef, useEffect } from 'react';

/**
 * Detects if a tool output contains an MCP UI resource
 */
export function detectMCPUIResource(output: string | null | undefined): {
  isMCPResource: boolean;
  resource?: {
    uri: string;
    name: string;
    mimeType: string;
    text: string;
  };
} {
  if (!output) {
    console.log('detectMCPUIResource: No output provided');
    return { isMCPResource: false };
  }

  try {
    // Parse the output as JSON
    const parsed = JSON.parse(output);
    console.log('detectMCPUIResource: Parsed JSON:', {
      type: parsed?.type,
      hasResource: !!parsed?.resource,
      uri: parsed?.resource?.uri,
      mimeType: parsed?.resource?.mimeType,
      hasText: !!parsed?.resource?.text,
      textLength: parsed?.resource?.text?.length
    });
    
    // Check if it's an MCP UI resource response
    if (
      parsed?.type === 'resource' &&
      parsed?.resource?.uri?.startsWith('ui://') &&
      parsed?.resource?.mimeType === 'text/html' &&
      parsed?.resource?.text
    ) {
      console.log('detectMCPUIResource: ✅ MCP UI Resource detected!', parsed.resource.uri);
      return {
        isMCPResource: true,
        resource: parsed.resource,
      };
    }
  } catch (e) {
    console.log('detectMCPUIResource: Failed to parse as JSON', e);
  }

  return { isMCPResource: false };
}

interface MCPUIRendererProps {
  resource: {
    uri: string;
    name: string;
    mimeType: string;
    text: string;
  };
}

export function MCPUIRenderer({ resource }: MCPUIRendererProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  
  // Create the iframe content
  const iframeContent = useMemo(() => {
    // Wrap the HTML content with necessary scripts for communication
    const wrappedHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body {
              margin: 0;
              padding: 16px;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
              font-size: 14px;
              line-height: 1.5;
              color: #333;
            }
            * {
              box-sizing: border-box;
            }
          </style>
        </head>
        <body>
          ${resource.text}
          <script>
            // Listen for form submissions and button clicks
            document.addEventListener('submit', function(e) {
              if (e.target.tagName === 'FORM') {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                window.parent.postMessage({
                  type: 'mcp-ui-action',
                  action: 'form-submit',
                  data: data,
                  uri: '${resource.uri}'
                }, '*');
              }
            });
            
            // Listen for messages from buttons
            window.addEventListener('message', function(e) {
              console.log('MCP UI received message:', e.data);
            });
            
            // Auto-resize iframe based on content
            function updateHeight() {
              const height = document.body.scrollHeight;
              window.parent.postMessage({
                type: 'mcp-ui-resize',
                height: height
              }, '*');
            }
            
            // Update height on load and when content changes
            window.addEventListener('load', updateHeight);
            new ResizeObserver(updateHeight).observe(document.body);
          </script>
        </body>
      </html>
    `;
    
    // Create a blob URL for the iframe
    const blob = new Blob([wrappedHtml], { type: 'text/html' });
    return URL.createObjectURL(blob);
  }, [resource.text, resource.uri]);
  
  // Handle messages from the iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'mcp-ui-action') {
        console.log('MCP UI Action:', event.data);
        // Here you could handle the action, e.g., send it back to the server
      } else if (event.data?.type === 'mcp-ui-resize' && iframeRef.current) {
        // Auto-resize the iframe based on content
        iframeRef.current.style.height = `${event.data.height}px`;
      }
    };
    
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);
  
  // Clean up blob URL when component unmounts
  useEffect(() => {
    return () => {
      if (iframeContent.startsWith('blob:')) {
        URL.revokeObjectURL(iframeContent);
      }
    };
  }, [iframeContent]);
  
  return (
    <div className="my-4 overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-4 py-2">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {resource.name || 'Interactive Component'}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">{resource.uri}</p>
      </div>
      <iframe
        ref={iframeRef}
        src={iframeContent}
        className="w-full bg-white"
        style={{
          border: 'none',
          minHeight: '200px',
          maxHeight: '800px',
        }}
        sandbox="allow-scripts allow-forms allow-same-origin"
        title={resource.name}
      />
    </div>
  );
}