/**
 * ForgeX — TypeScript Type Definitions
 *
 * Interfaces for all API contracts and UI state.
 */

// ── Agent Configuration ───────────────────────────────────────────────────

export interface AgentConfig {
  id: string;
  name: string;
  system_prompt: string;
  planning_enabled: boolean;
  response_format: string;
  response_schema?: Record<string, unknown>;
  backend_mode: string;
  debug_mode: boolean;
  interrupt_policy?: Record<string, unknown>;
  permissions?: Record<string, unknown>;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  tools: AgentToolAssignment[];
  skills: AgentSkillAssignment[];
  subagents: SubagentConfig[];
}

export interface AgentConfigSummary {
  id: string;
  name: string;
  version: number;
  is_active: boolean;
  planning_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentToolAssignment {
  id: string;
  tool_definition_id: string;
  tool_name: string;
  tool_description: string;
  require_approval: boolean;
  enabled: boolean;
}

export interface AgentSkillAssignment {
  id: string;
  skill_id: string;
  skill_name: string;
  enabled: boolean;
}

export interface SubagentConfig {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  enabled: boolean;
}


// ── Tools ─────────────────────────────────────────────────────────────────

export interface ToolDefinition {
  id: string;
  name: string;
  description: string;
  tool_type: string;
  is_builtin: boolean;
  is_sensitive: boolean;
  input_schema?: Record<string, unknown>;
  config?: Record<string, unknown>;
}

export interface FeasibilityResult {
  feasible: boolean;
  reasons: string[];
  warnings: string[];
}


// ── Skills ────────────────────────────────────────────────────────────────

export interface Skill {
  id: string;
  name: string;
  description?: string;
  directory_name: string;
  frontmatter?: Record<string, unknown>;
  created_at: string;
}


// ── Threads ───────────────────────────────────────────────────────────────

export interface Thread {
  id: string;
  title: string;
  agent_config_id?: string;
  status: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ThreadMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  tool_calls?: unknown;
  tool_call_id?: string;
  metadata?: Record<string, unknown>;
  seq: number;
  created_at: string;
}


// ── Streaming Events ──────────────────────────────────────────────────────

export type StreamEventType =
  | 'run_start'
  | 'run_end'
  | 'message_start'
  | 'message_chunk'
  | 'message_end'
  | 'tool_call'
  | 'tool_result'
  | 'custom'
  | 'error'
  | 'keepalive';

export interface StreamEvent {
  type: StreamEventType;
  seq: number;
  timestamp: string;
  // Message events
  message_id?: string;
  role?: string;
  content?: string;
  // Tool events
  tool_call_id?: string;
  tool_name?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  status?: string;
  // Custom state (todos, etc.)
  key?: string;
  value?: unknown;
  // Run events
  run_id?: string;
  thread_id?: string;
  // Error
  error?: string;
}


// ── Memory & Learning ─────────────────────────────────────────────────────

export interface MemoryContent {
  content: string;
  version: number;
  character_count: number;
  created_at?: string;
}

export interface EpisodicMemory {
  id: string;
  summary: string;
  context?: string;
  outcome?: string;
  importance: number;
  tags?: string[];
  access_count: number;
  created_at: string;
}

export interface SemanticMemory {
  id: string;
  category: string;
  key: string;
  value: string;
  confidence: number;
  source: string;
  reinforcement_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LearningEvent {
  id: string;
  event_type: string;
  description: string;
  memories_created?: string[];
  created_at: string;
}

export interface MemoryStats {
  episodic_count: number;
  semantic_count: number;
  agents_md_version: number;
  agents_md_characters: number;
}

export interface LearningStats {
  learning_events: Record<string, number>;
  feedback: Record<string, number>;
  memory: MemoryStats;
  total_events: number;
}


// ── Todos ─────────────────────────────────────────────────────────────────

export interface TodoItem {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed';
}


// ── UI State ──────────────────────────────────────────────────────────────

export interface ToolCallState {
  tool_call_id: string;
  tool_name: string;
  args?: Record<string, unknown>;
  result?: unknown;
  status: 'running' | 'completed' | 'error';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  toolCalls?: ToolCallState[];
  todos?: TodoItem[];
  isStreaming?: boolean;
  feedback?: 'positive' | 'negative' | null;
}
