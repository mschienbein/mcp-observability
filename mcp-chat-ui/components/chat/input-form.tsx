'use client';

import { FormEvent, ChangeEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';

interface Props {
  input: string;
  handleInputChange: (e: ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
}

export function InputForm({ input, handleInputChange, handleSubmit, isLoading }: Props) {
  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (handleSubmit) {
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={onSubmit} className="flex gap-2">
      <textarea
        value={input}
        onChange={handleInputChange}
        placeholder="Type your message..."
        className="flex-1 min-h-[60px] max-h-[200px] px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 resize-y"
        disabled={isLoading}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            // Create a synthetic form event
            const form = e.currentTarget.closest('form');
            if (form && handleSubmit) {
              const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
              form.dispatchEvent(submitEvent);
            }
          }
        }}
      />
      <Button
        type="submit"
        disabled={isLoading || !input?.trim()}
        className="self-end"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </form>
  );
}