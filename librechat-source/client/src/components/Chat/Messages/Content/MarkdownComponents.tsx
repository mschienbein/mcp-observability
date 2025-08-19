import React, { memo, useMemo, useRef, useEffect, useState } from 'react';
import { useRecoilValue } from 'recoil';
import { useToastContext } from '@librechat/client';
import { PermissionTypes, Permissions } from 'librechat-data-provider';
import { UIResourceRenderer } from '@mcp-ui/client';
import CodeBlock from '~/components/Messages/Content/CodeBlock';
import useHasAccess from '~/hooks/Roles/useHasAccess';
import { useFileDownload } from '~/data-provider';
import { useCodeBlockContext, useMCPResources } from '~/Providers';
import { handleDoubleClick } from '~/utils';
import { useLocalize } from '~/hooks';
import store from '~/store';

type TCodeProps = {
  inline?: boolean;
  className?: string;
  children: React.ReactNode;
};

export const code: React.ElementType = memo(({ className, children }: TCodeProps) => {
  const canRunCode = useHasAccess({
    permissionType: PermissionTypes.RUN_CODE,
    permission: Permissions.USE,
  });
  const match = /language-(\w+)/.exec(className ?? '');
  const lang = match && match[1];
  const isMath = lang === 'math';
  const isSingleLine = typeof children === 'string' && children.split('\n').length === 1;
  
  // Debug logging for HTML code blocks
  if (lang === 'html') {
    console.log('HTML Code Block Detected:', {
      lang,
      className,
      childrenType: typeof children,
      childrenLength: typeof children === 'string' ? children.length : 'not string',
      preview: typeof children === 'string' ? children.substring(0, 200) : children
    });
  }

  const { getNextIndex, resetCounter } = useCodeBlockContext();
  const blockIndex = useRef(getNextIndex(isMath || isSingleLine)).current;

  useEffect(() => {
    resetCounter();
  }, [children, resetCounter]);

  // Check if this is an MCP UI HTML code block
  if (lang === 'html' && typeof children === 'string') {
    const htmlContent = children.toString();
    // Check for MCP UI markers - dashboard, forms, charts, etc
    const isMCPUI = htmlContent.includes('System Dashboard') ||
                    htmlContent.includes('User Registration Form') ||
                    htmlContent.includes('Data Table') ||
                    htmlContent.includes('Settings Panel') ||
                    htmlContent.includes('Bar Chart') ||
                    htmlContent.includes('Pie Chart') ||
                    htmlContent.includes('Line Chart') ||
                    htmlContent.includes('window.parent.postMessage');
    
    if (isMCPUI) {
      console.log('MCP UI Component Detected! Rendering with UIResourceRenderer');
      
      // Create a resource object for the MCP UI SDK
      const resource = {
        uri: 'ui://inline/html-block',
        name: 'Interactive Component',
        mimeType: 'text/html',
        text: htmlContent
      };
      
      return (
        <div className="my-4">
          <UIResourceRenderer
            resource={resource}
            onUIAction={(result: any) => {
              console.log('MCP UI Action from HTML block:', result);
            }}
          />
        </div>
      );
    }
  }

  if (isMath) {
    return <>{children}</>;
  } else if (isSingleLine) {
    return (
      <code onDoubleClick={handleDoubleClick} className={className}>
        {children}
      </code>
    );
  } else {
    return (
      <CodeBlock
        lang={lang ?? 'text'}
        codeChildren={children}
        blockIndex={blockIndex}
        allowExecution={canRunCode}
      />
    );
  }
});

export const codeNoExecution: React.ElementType = memo(({ className, children }: TCodeProps) => {
  const match = /language-(\w+)/.exec(className ?? '');
  const lang = match && match[1];

  if (lang === 'math') {
    return children;
  } else if (typeof children === 'string' && children.split('\n').length === 1) {
    return (
      <code onDoubleClick={handleDoubleClick} className={className}>
        {children}
      </code>
    );
  } else {
    return <CodeBlock lang={lang ?? 'text'} codeChildren={children} allowExecution={false} />;
  }
});

type TAnchorProps = {
  href: string;
  children: React.ReactNode;
};

// Component to render MCP UI resources from ui:// links
const MCPUILink: React.FC<{ href: string; children: React.ReactNode }> = memo(({ href, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { getResource } = useMCPResources();
  
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsOpen(!isOpen);
  };
  
  // Get the resource from the store
  const resource = useMemo(() => {
    return getResource(href);
  }, [href, getResource]);
  
  // If no resource is stored, render as a regular link
  if (!resource) {
    return (
      <a 
        href={href} 
        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline"
        title={`MCP UI Resource: ${href}`}
      >
        {children}
      </a>
    );
  }
  
  return (
    <>
      <a 
        href={href} 
        onClick={handleClick}
        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline cursor-pointer inline-flex items-center gap-1"
      >
        <span>{children}</span>
        <span className="text-xs">{isOpen ? '▼' : '▶'}</span>
      </a>
      {isOpen && resource && (
        <div className="my-2">
          <UIResourceRenderer
            resource={resource}
            onUIAction={(result: any) => {
              console.log('MCP UI Action from link:', result);
            }}
          />
        </div>
      )}
    </>
  );
});

export const a: React.ElementType = memo(({ href, children }: TAnchorProps) => {
  const user = useRecoilValue(store.user);
  const { showToast } = useToastContext();
  const localize = useLocalize();

  // Check if this is a ui:// protocol link
  if (href?.startsWith('ui://')) {
    return <MCPUILink href={href}>{children}</MCPUILink>;
  }

  const {
    file_id = '',
    filename = '',
    filepath,
  } = useMemo(() => {
    const pattern = new RegExp(`(?:files|outputs)/${user?.id}/([^\\s]+)`);
    const match = href.match(pattern);
    if (match && match[0]) {
      const path = match[0];
      const parts = path.split('/');
      const name = parts.pop();
      const file_id = parts.pop();
      return { file_id, filename: name, filepath: path };
    }
    return { file_id: '', filename: '', filepath: '' };
  }, [user?.id, href]);

  const { refetch: downloadFile } = useFileDownload(user?.id ?? '', file_id);
  const props: { target?: string; onClick?: React.MouseEventHandler } = { target: '_new' };

  if (!file_id || !filename) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  }

  const handleDownload = async (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    try {
      const stream = await downloadFile();
      if (stream.data == null || stream.data === '') {
        console.error('Error downloading file: No data found');
        showToast({
          status: 'error',
          message: localize('com_ui_download_error'),
        });
        return;
      }
      const link = document.createElement('a');
      link.href = stream.data;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(stream.data);
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  props.onClick = handleDownload;
  props.target = '_blank';

  return (
    <a
      href={filepath?.startsWith('files/') ? `/api/${filepath}` : `/api/files/${filepath}`}
      {...props}
    >
      {children}
    </a>
  );
});

type TParagraphProps = {
  children: React.ReactNode;
};

export const p: React.ElementType = memo(({ children }: TParagraphProps) => {
  return <p className="mb-2 whitespace-pre-wrap">{children}</p>;
});
