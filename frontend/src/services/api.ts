/**
 * ForgeX — API Service Layer
 *
 * Fetch wrapper for all REST and streaming endpoints.
 */

const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.detail || error.error || `Request failed: ${response.status}`);
  }
  return response.json();
}


// ── Agent Configs ─────────────────────────────────────────────────────────

export const agentConfigApi = {
  list: () => request<any[]>('/agent-configs'),
  get: (id: string) => request<any>(`/agent-configs/${id}`),
  create: (data: any) => request<any>('/agent-configs', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request<any>(`/agent-configs/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => request<any>(`/agent-configs/${id}`, { method: 'DELETE' }),
  setTools: (id: string, tools: any[]) => request<any>(`/agent-configs/${id}/tools`, { method: 'PUT', body: JSON.stringify({ tools }) }),
  setSkills: (id: string, skillIds: string[]) => request<any>(`/agent-configs/${id}/skills`, { method: 'PUT', body: JSON.stringify({ skill_ids: skillIds }) }),
};


// ── Tools ─────────────────────────────────────────────────────────────────

export const toolsApi = {
  list: () => request<any[]>('/tools'),
  checkFeasibility: (data: any) => request<any>('/tools/feasibility', { method: 'POST', body: JSON.stringify(data) }),
  create: (data: any) => request<any>('/tools', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request<any>(`/tools/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => request<any>(`/tools/${id}`, { method: 'DELETE' }),
};


// ── Skills ────────────────────────────────────────────────────────────────

export const skillsApi = {
  list: () => request<any[]>('/skills'),
  create: (data: any) => request<any>('/skills', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request<any>(`/skills/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => request<any>(`/skills/${id}`, { method: 'DELETE' }),
};


// ── Threads ───────────────────────────────────────────────────────────────

export const threadsApi = {
  list: () => request<any[]>('/threads'),
  create: (data?: any) => request<any>('/threads', { method: 'POST', body: JSON.stringify(data || {}) }),
  update: (id: string, data: any) => request<any>(`/threads/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => request<any>(`/threads/${id}`, { method: 'DELETE' }),
  getHistory: (id: string) => request<any[]>(`/threads/${id}/history`),
  getState: (id: string) => request<any>(`/threads/${id}/state`),
  submitCommand: (threadId: string, data: any) => request<any>(`/threads/${threadId}/commands`, { method: 'POST', body: JSON.stringify(data) }),
};


// ── Memory & Learning ─────────────────────────────────────────────────────

export const memoryApi = {
  getAgentsMd: (configId: string) => request<any>(`/agent-configs/${configId}/memory`),
  updateAgentsMd: (configId: string, content: string) => request<any>(`/agent-configs/${configId}/memory`, { method: 'PUT', body: JSON.stringify({ content }) }),
  getEpisodic: (configId: string) => request<any[]>(`/agent-configs/${configId}/memories/episodic`),
  getSemantic: (configId: string, category?: string) =>
    request<any[]>(`/agent-configs/${configId}/memories/semantic${category ? `?category=${category}` : ''}`),
  getStats: (configId: string) => request<any>(`/agent-configs/${configId}/memories/stats`),
  deleteMemory: (id: string, type: string) => request<any>(`/memories/${id}?memory_type=${type}`, { method: 'DELETE' }),
  submitFeedback: (threadId: string, data: any) => request<any>(`/threads/${threadId}/feedback`, { method: 'POST', body: JSON.stringify(data) }),
  getLearningLog: (configId: string) => request<any[]>(`/agent-configs/${configId}/learning-log`),
  getLearningStats: (configId: string) => request<any>(`/agent-configs/${configId}/learning-stats`),
};


// ── SSE Stream ────────────────────────────────────────────────────────────

export function createEventStream(
  threadId: string,
  runId: string,
  fromSeq: number = 0,
  onEvent: (event: any) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void,
): () => void {
  const url = `${API_BASE}/threads/${threadId}/stream?run_id=${runId}&from_seq=${fromSeq}`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data);
      onEvent(event);
      if (event.type === 'run_end' || event.type === 'error') {
        eventSource.close();
        onComplete?.();
      }
    } catch (err) {
      console.error('Failed to parse SSE event:', err);
    }
  };

  eventSource.onerror = (e) => {
    console.error('SSE error:', e);
    eventSource.close();
    onError?.(new Error('Stream connection failed'));
  };

  // Return cleanup function
  return () => eventSource.close();
}
