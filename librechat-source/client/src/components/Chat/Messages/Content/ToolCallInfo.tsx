import React, { useEffect, useMemo } from 'react';
import { useLocalize } from '~/hooks';
import { useMCPResources } from '~/Providers';
import { detectMCPUIResource } from './MCPUIDetector';

function OptimizedCodeBlock({ text, maxHeight = 320 }: { text: string; maxHeight?: number }) {
  return (
    <div
      className="rounded-lg bg-surface-tertiary p-2 text-xs text-text-primary"
      style={{
        position: 'relative',
        maxHeight,
        overflow: 'auto',
      }}
    >
      <pre className="m-0 whitespace-pre-wrap break-words" style={{ overflowWrap: 'break-word' }}>
        <code>{text}</code>
      </pre>
    </div>
  );
}

export default function ToolCallInfo({
  input,
  output,
  domain,
  function_name,
  pendingAuth,
}: {
  input: string;
  function_name: string;
  output?: string | null;
  domain?: string;
  pendingAuth?: boolean;
}) {
  const localize = useLocalize();
  const { addResource, getResource } = useMCPResources();
  
  const formatText = (text: string) => {
    try {
      return JSON.stringify(JSON.parse(text), null, 2);
    } catch {
      return text;
    }
  };

  let title =
    domain != null && domain
      ? localize('com_assistants_domain_info', { 0: domain })
      : localize('com_assistants_function_use', { 0: function_name });
  if (pendingAuth === true) {
    title =
      domain != null && domain
        ? localize('com_assistants_action_attempt', { 0: domain })
        : localize('com_assistants_attempt_info');
  }

  // Check if output is an MCP UI resource (memoized to avoid new object each render)
  const mcpResource = useMemo(() => detectMCPUIResource(output), [output]);
  console.log('ToolCallInfo - Output:', output);
  console.log('ToolCallInfo - MCP Resource:', mcpResource);
  // Debug logging
  console.log('ToolCallInfo - Checking output for MCP UI:', {
    function_name,
    hasOutput: !!output,
    outputLength: output?.length,
    isMCPResource: mcpResource.isMCPResource,
    resourceUri: mcpResource.resource?.uri
  });
  
  // Store the resource if it's an MCP UI resource
  useEffect(() => {
    if (mcpResource.isMCPResource && mcpResource.resource) {
      const uri = mcpResource.resource.uri as string | undefined;
      if (!uri) {
        return;
      }
      const existing = getResource(uri);
      if (!existing) {
        console.log('ToolCallInfo - Storing MCP UI resource:', uri);
        addResource(mcpResource.resource);
      }
    }
  }, [output, mcpResource.isMCPResource, mcpResource.resource, addResource, getResource]);

  return (
    <div className="w-full p-2">
      <div style={{ opacity: 1 }}>
        <div className="mb-2 text-sm font-medium text-text-primary">{title}</div>
        <div>
          <OptimizedCodeBlock text={formatText(input)} maxHeight={250} />
        </div>
        {output && (
          <>
            <div className="my-2 text-sm font-medium text-text-primary">
              {localize('com_ui_result')}
            </div>
            <div>
              {mcpResource.isMCPResource && mcpResource.resource ? (
                // Show cleaned summary JSON of the detected MCP UI resource
                <OptimizedCodeBlock
                  text={formatText(
                    JSON.stringify(
                      {
                        kind: 'mcp_ui_resource',
                        uri: mcpResource.resource.uri,
                        title: mcpResource.resource.title,
                        description: mcpResource.resource.description,
                      },
                      null,
                      2,
                    ),
                  )}
                  maxHeight={250}
                />
              ) : (
                <OptimizedCodeBlock text={formatText(output)} maxHeight={250} />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
