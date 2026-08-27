/**
 * ForgeX — useAgentStream Hook
 *
 * Custom hook for Agent Streaming Protocol SSE consumption.
 * Replaces @langchain/react useStream for the custom FastAPI backend.
 */

import { useState, useCallback, useRef } from 'react';
import { createEventStream, threadsApi } from '../services/api';
import type { ChatMessage, ToolCallState, TodoItem, StreamEvent } from '../types';

interface UseAgentStreamReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  toolCalls: ToolCallState[];
  todos: TodoItem[];
  error: string | null;
  sendMessage: (content: string, agentConfigId?: string) => Promise<void>;
  stopStream: () => void;
  clearMessages: () => void;
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
}

export function useAgentStream(threadId: string | null): UseAgentStreamReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolCalls, setToolCalls] = useState<ToolCallState[]>([]);
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const currentMsgRef = useRef<string>('');
  const currentMsgIdRef = useRef<string>('');

  const stopStream = useCallback(() => {
    cleanupRef.current?.();
    cleanupRef.current = null;
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback(async (content: string, agentConfigId?: string) => {
    if (!threadId || !content.trim()) return;

    setError(null);
    currentMsgRef.current = '';
    currentMsgIdRef.current = '';

    // Add user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setToolCalls([]);

    try {
      // Submit command
      const { run_id } = await threadsApi.submitCommand(threadId, {
        command: 'run',
        message: content,
        agent_config_id: agentConfigId,
      });

      // Subscribe to SSE stream
      const cleanup = createEventStream(
        threadId,
        run_id,
        0,
        (event: StreamEvent) => {
          switch (event.type) {
            case 'message_start':
              currentMsgIdRef.current = event.message_id || `msg-${Date.now()}`;
              currentMsgRef.current = '';
              setMessages(prev => [...prev, {
                id: currentMsgIdRef.current,
                role: 'assistant',
                content: '',
                timestamp: event.timestamp,
                isStreaming: true,
              }]);
              break;

            case 'message_chunk':
              currentMsgRef.current += event.content || '';
              setMessages(prev => prev.map(m =>
                m.id === currentMsgIdRef.current
                  ? { ...m, content: currentMsgRef.current }
                  : m
              ));
              break;

            case 'message_end':
              setMessages(prev => prev.map(m =>
                m.id === currentMsgIdRef.current
                  ? { ...m, content: event.content || currentMsgRef.current, isStreaming: false }
                  : m
              ));
              break;

            case 'tool_call':
              setToolCalls(prev => [...prev, {
                tool_call_id: event.tool_call_id || '',
                tool_name: event.tool_name || '',
                args: event.args,
                status: 'running',
              }]);
              break;

            case 'tool_result':
              setToolCalls(prev => prev.map(tc =>
                tc.tool_call_id === event.tool_call_id
                  ? { ...tc, result: event.result, status: 'completed' }
                  : tc
              ));
              break;

            case 'custom':
              if (event.key === 'todos') {
                setTodos(event.value as TodoItem[]);
              }
              break;

            case 'error':
              setError(event.error || 'An error occurred');
              setIsStreaming(false);
              break;

            case 'run_end':
              setIsStreaming(false);
              break;
          }
        },
        (err) => {
          setError(err.message);
          setIsStreaming(false);
        },
        () => {
          setIsStreaming(false);
        }
      );

      cleanupRef.current = cleanup;
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
      setIsStreaming(false);
    }
  }, [threadId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setToolCalls([]);
    setTodos([]);
    setError(null);
  }, []);

  return { messages, isStreaming, toolCalls, todos, error, sendMessage, stopStream, clearMessages, setMessages };
}
