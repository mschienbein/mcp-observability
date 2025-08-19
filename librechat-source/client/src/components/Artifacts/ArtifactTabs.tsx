import { useRef, useEffect } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import type { SandpackPreviewRef, CodeEditorRef } from '@codesandbox/sandpack-react';
import type { Artifact, ArtifactType } from '~/common';
import { useEditorContext, useArtifactsContext } from '~/Providers';
import useArtifactProps from '~/hooks/Artifacts/useArtifactProps';
import { useAutoScroll } from '~/hooks/Artifacts/useAutoScroll';
import { ArtifactCodeEditor } from './ArtifactCodeEditor';
import { useGetStartupConfig } from '~/data-provider';
import { ArtifactPreview } from './ArtifactPreview';
import { MCPUIRenderer } from './MCPUIRenderer';
import { cn } from '~/utils';

export default function ArtifactTabs({
  artifact,
  isMermaid,
  editorRef,
  previewRef,
}: {
  artifact: Artifact;
  isMermaid: boolean;
  editorRef: React.MutableRefObject<CodeEditorRef>;
  previewRef: React.MutableRefObject<SandpackPreviewRef>;
}) {
  const { isSubmitting } = useArtifactsContext();
  const { currentCode, setCurrentCode } = useEditorContext();
  const { data: startupConfig } = useGetStartupConfig();
  const lastIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (artifact.id !== lastIdRef.current) {
      setCurrentCode(undefined);
    }
    lastIdRef.current = artifact.id;
  }, [setCurrentCode, artifact.id]);

  const content = artifact.content ?? '';
  const contentRef = useRef<HTMLDivElement>(null);
  useAutoScroll({ ref: contentRef, content, isSubmitting });
  const { files, fileKey, template, sharedProps } = useArtifactProps({ artifact });
  
  // Check if this is an MCP UI artifact
  const isMCPUI = artifact.type === 'mcp_ui' || artifact.type === 'interactive_tool';
  
  // If it's an MCP UI artifact, render the MCP UI component
  if (isMCPUI) {
    return (
      <>
        <Tabs.Content
          ref={contentRef}
          value="code"
          id="artifacts-code"
          className={cn('flex-grow overflow-auto')}
        >
          <div className="p-4">
            <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-auto">
              <code>{JSON.stringify(artifact.mcpResource || JSON.parse(artifact.content || '{}'), null, 2)}</code>
            </pre>
          </div>
        </Tabs.Content>
        <Tabs.Content
          value="preview"
          className={cn('flex-grow overflow-auto bg-white dark:bg-gray-900')}
        >
          <MCPUIRenderer artifact={artifact} />
        </Tabs.Content>
      </>
    );
  }
  
  // Default rendering for non-MCP artifacts
  return (
    <>
      <Tabs.Content
        ref={contentRef}
        value="code"
        id="artifacts-code"
        className={cn('flex-grow overflow-auto')}
      >
        <ArtifactCodeEditor
          files={files}
          fileKey={fileKey}
          template={template}
          artifact={artifact}
          editorRef={editorRef}
          sharedProps={sharedProps}
        />
      </Tabs.Content>
      <Tabs.Content
        value="preview"
        className={cn('flex-grow overflow-auto', isMermaid ? 'bg-[#282C34]' : 'bg-white')}
      >
        <ArtifactPreview
          files={files}
          fileKey={fileKey}
          template={template}
          previewRef={previewRef}
          sharedProps={sharedProps}
          currentCode={currentCode}
          startupConfig={startupConfig}
        />
      </Tabs.Content>
    </>
  );
}
