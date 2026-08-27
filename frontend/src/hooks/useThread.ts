/**
 * ForgeX — useThread Hook
 *
 * Thread lifecycle management.
 */

import { useState, useCallback, useEffect } from 'react';
import { threadsApi } from '../services/api';
import type { Thread } from '../types';

interface UseThreadReturn {
  threads: Thread[];
  activeThread: Thread | null;
  loading: boolean;
  loadThreads: () => Promise<void>;
  createThread: (agentConfigId?: string) => Promise<Thread>;
  selectThread: (thread: Thread) => void;
  renameThread: (id: string, title: string) => Promise<void>;
  deleteThread: (id: string) => Promise<void>;
}

export function useThread(): UseThreadReturn {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThread, setActiveThread] = useState<Thread | null>(null);
  const [loading, setLoading] = useState(false);

  const loadThreads = useCallback(async () => {
    try {
      setLoading(true);
      const data = await threadsApi.list();
      setThreads(data);
    } catch (err) {
      console.error('Failed to load threads:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createThread = useCallback(async (agentConfigId?: string) => {
    const thread = await threadsApi.create({ agent_config_id: agentConfigId });
    await loadThreads();
    setActiveThread(thread);
    return thread;
  }, [loadThreads]);

  const selectThread = useCallback((thread: Thread) => {
    setActiveThread(thread);
  }, []);

  const renameThread = useCallback(async (id: string, title: string) => {
    await threadsApi.update(id, { title });
    await loadThreads();
    if (activeThread?.id === id) {
      setActiveThread(prev => prev ? { ...prev, title } : null);
    }
  }, [activeThread, loadThreads]);

  const deleteThread = useCallback(async (id: string) => {
    await threadsApi.delete(id);
    if (activeThread?.id === id) setActiveThread(null);
    await loadThreads();
  }, [activeThread, loadThreads]);

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  return {
    threads, activeThread, loading,
    loadThreads, createThread, selectThread, renameThread, deleteThread,
  };
}
