import React, { memo, useMemo, useState } from 'react';
import { useMCPResources } from '~/Providers';
import MCPUIResourceRenderer from './MCPUIResourceRenderer';

export interface MCPUILinkProps {
  href: string;
  children: React.ReactNode;
  onUIAction?: (result: any) => void;
}

const MCPUILink: React.FC<MCPUILinkProps> = memo(({ href, children, onUIAction }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { getResource } = useMCPResources();

  const resource = useMemo(() => getResource(href), [href, getResource]);

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

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsOpen((prev) => !prev);
  };

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
      {isOpen && (
        <div className="my-2">
          <MCPUIResourceRenderer
            resource={resource}
            onUIAction={onUIAction}
          />
        </div>
      )}
    </>
  );
});

export default MCPUILink;
