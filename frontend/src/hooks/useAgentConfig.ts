/**
 * ForgeX — useAgentConfig Hook
 *
 * Manages agent configuration state with API calls.
 */

import { useState, useEffect, useCallback } from 'react';
import { agentConfigApi, toolsApi, memoryApi } from '../services/api';
import type { AgentConfig, ToolDefinition, MemoryStats, LearningStats } from '../types';

interface UseAgentConfigReturn {
  configs: any[];
  activeConfig: AgentConfig | null;
  tools: ToolDefinition[];
  memoryStats: MemoryStats | null;
  learningStats: LearningStats | null;
  loading: boolean;
  setActiveConfig: (config: AgentConfig | null) => void;
  loadConfigs: () => Promise<void>;
  createConfig: (data?: any) => Promise<AgentConfig>;
  updateConfig: (id: string, data: any) => Promise<void>;
  deleteConfig: (id: string) => Promise<void>;
  loadTools: () => Promise<void>;
  loadMemoryStats: (configId: string) => Promise<void>;
  loadLearningStats: (configId: string) => Promise<void>;
}

export function useAgentConfig(): UseAgentConfigReturn {
  const [configs, setConfigs] = useState<any[]>([]);
  const [activeConfig, setActiveConfig] = useState<AgentConfig | null>(null);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [learningStats, setLearningStats] = useState<LearningStats | null>(null);
  const [loading, setLoading] = useState(false);

  const loadConfigs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await agentConfigApi.list();
      setConfigs(data);
    } catch (err) {
      console.error('Failed to load configs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createConfig = useCallback(async (data?: any) => {
    const config = await agentConfigApi.create(data || {
      name: 'ForgeX Agent',
      system_prompt: 'You are ForgeX, a helpful AI agent with self-learning capabilities. You remember past interactions and learn from feedback.',
    });
    await loadConfigs();
    const full = await agentConfigApi.get(config.id);
    setActiveConfig(full);
    return full;
  }, [loadConfigs]);

  const updateConfig = useCallback(async (id: string, data: any) => {
    await agentConfigApi.update(id, data);
    const full = await agentConfigApi.get(id);
    setActiveConfig(full);
    await loadConfigs();
  }, [loadConfigs]);

  const deleteConfig = useCallback(async (id: string) => {
    await agentConfigApi.delete(id);
    if (activeConfig?.id === id) setActiveConfig(null);
    await loadConfigs();
  }, [activeConfig, loadConfigs]);

  const loadTools = useCallback(async () => {
    try {
      const data = await toolsApi.list();
      setTools(data);
    } catch (err) {
      console.error('Failed to load tools:', err);
    }
  }, []);

  const loadMemoryStats = useCallback(async (configId: string) => {
    try {
      const data = await memoryApi.getStats(configId);
      setMemoryStats(data);
    } catch (err) {
      console.error('Failed to load memory stats:', err);
    }
  }, []);

  const loadLearningStats = useCallback(async (configId: string) => {
    try {
      const data = await memoryApi.getLearningStats(configId);
      setLearningStats(data);
    } catch (err) {
      console.error('Failed to load learning stats:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadConfigs();
    loadTools();
  }, [loadConfigs, loadTools]);

  return {
    configs, activeConfig, tools, memoryStats, learningStats, loading,
    setActiveConfig, loadConfigs, createConfig, updateConfig, deleteConfig,
    loadTools, loadMemoryStats, loadLearningStats,
  };
}
