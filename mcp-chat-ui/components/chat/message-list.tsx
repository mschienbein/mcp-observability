'use client';

import { Message } from 'ai';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MCPResourceDisplay } from '../mcp/ui-resource-renderer';
import { User, Bot } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface Props {
  messages: Message[];
}

export function MessageList({ messages }: Props) {
  if (messages.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          Start a conversation by typing a message below
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={cn(
            'flex gap-4',
            message.role === 'user' ? 'justify-end' : 'justify-start'
          )}
        >
          {message.role === 'assistant' && (
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
              <Bot className="h-5 w-5 text-white" />
            </div>
          )}
          
          <div
            className={cn(
              'max-w-[80%] rounded-lg px-4 py-3',
              message.role === 'user'
                ? 'bg-blue-500 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
            )}
          >
            {message.role === 'user' ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  className="prose prose-sm dark:prose-invert max-w-none"
                  components={{
                    pre: ({ children }) => (
                      <pre className="bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                        {children}
                      </pre>
                    ),
                    code: ({ className, children }) => {
                      const inline = !className;
                      return inline ? (
                        <code className="bg-gray-100 dark:bg-gray-900 px-1 py-0.5 rounded text-sm">
                          {children}
                        </code>
                      ) : (
                        <code className={className}>{children}</code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
                
                {/* Render tool calls */}
                {message.toolInvocations?.map((invocation, index) => (
                  <div key={index} className="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                      Tool: {invocation.toolName}
                    </div>
                    {invocation.result && (
                      <div className="text-sm">
                        {/* Check if result is a UI resource */}
                        {invocation.result.type === 'ui-resource' ? (
                          <MCPResourceDisplay resource={invocation.result.resource} />
                        ) : (
                          <pre className="overflow-x-auto">
                            {JSON.stringify(invocation.result, null, 2)}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </>
            )}
          </div>
          
          {message.role === 'user' && (
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
              <User className="h-5 w-5 text-white" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}