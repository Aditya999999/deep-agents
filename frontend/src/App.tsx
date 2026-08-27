/**
 * ForgeX Deep Agent Platform — Main Application
 *
 * Single-page application with:
 * - Left sidebar (navigation, conversation history)
 * - Main chat workspace (timeline, composer)
 * - Right config drawer (agent settings)
 * - Self-learning memory system
 */

import { useState, useEffect, useRef } from 'react';
import { useAgentStream } from './hooks/useAgentStream';
import { useAgentConfig } from './hooks/useAgentConfig';
import { useThread } from './hooks/useThread';
import { memoryApi } from './services/api';
import type { ChatMessage, ToolCallState, TodoItem, SemanticMemory, EpisodicMemory, LearningEvent } from './types';

// ═══════════════════════════════════════════════════════════════════════════
// SVG Icons (inline for zero dependencies)
// ═══════════════════════════════════════════════════════════════════════════

const Icons = {
  Home: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>,
  Settings: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  Plus: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  Send: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
  Stop: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>,
  Search: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
  Upload: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
  X: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
  ThumbsUp: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>,
  ThumbsDown: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>,
  Brain: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2z"/></svg>,
  Grid: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  Activity: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  Trash: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>,
  Edit: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
  Check: () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  ChevronDown: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>,
  Wrench: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>,
};


// ═══════════════════════════════════════════════════════════════════════════
// Main App Component
// ═══════════════════════════════════════════════════════════════════════════

export default function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState('basic');
  const [searchQuery, setSearchQuery] = useState('');

  const { configs, activeConfig, tools, memoryStats, learningStats, createConfig, updateConfig, loadMemoryStats, loadLearningStats, setActiveConfig } = useAgentConfig();
  const { threads, activeThread, createThread, selectThread, renameThread, deleteThread } = useThread();
  const { messages, isStreaming, toolCalls, todos, error, sendMessage, stopStream, clearMessages, setMessages } = useAgentStream(activeThread?.id || null);

  // Load history when thread changes
  useEffect(() => {
    if (activeThread?.id) {
      clearMessages();
    }
  }, [activeThread?.id, clearMessages]);

  // Auto-create config on first load
  useEffect(() => {
    if (configs.length === 0) {
      createConfig().then(config => setActiveConfig(config));
    } else if (!activeConfig) {
      setActiveConfig(configs[0]);
    }
  }, [configs, activeConfig, createConfig, setActiveConfig]);

  // Load memory stats when config changes
  useEffect(() => {
    if (activeConfig?.id) {
      loadMemoryStats(activeConfig.id);
      loadLearningStats(activeConfig.id);
    }
  }, [activeConfig?.id, loadMemoryStats, loadLearningStats]);

  const handleNewConversation = async () => {
    await createThread(activeConfig?.id);
    clearMessages();
  };

  const handleSend = async (content: string) => {
    if (!activeThread) {
      await createThread(activeConfig?.id);
      setTimeout(() => sendMessage(content, activeConfig?.id), 100);
    } else {
      sendMessage(content, activeConfig?.id);
    }
  };

  const handleFeedback = async (messageId: string, rating: 'positive' | 'negative') => {
    if (!activeThread?.id || !activeConfig?.id) return;
    const msg = messages.find(m => m.id === messageId);
    try {
      await memoryApi.submitFeedback(activeThread.id, {
        message_id: messageId,
        rating,
        original_response: msg?.content,
        agent_config_id: activeConfig.id,
      });
      setMessages(prev => prev.map(m => m.id === messageId ? { ...m, feedback: rating } : m));
      // Refresh learning stats
      loadLearningStats(activeConfig.id);
    } catch (err) {
      console.error('Feedback failed:', err);
    }
  };

  const filteredThreads = threads.filter(t =>
    !searchQuery || t.title?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">ForgeX</span>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-nav-item active"><Icons.Home /><span>Home</span></div>
          <div className="sidebar-nav-item" onClick={() => setDrawerOpen(true)}><Icons.Settings /><span>Agent Settings</span></div>
          <div className="sidebar-nav-item" onClick={() => { setDrawerOpen(true); setDrawerTab('memory'); }}><Icons.Brain /><span>Memory & Learning</span></div>
          <div className="sidebar-nav-item"><Icons.Grid /><span>Skills</span></div>
          <div className="sidebar-nav-item"><Icons.Activity /><span>Activity</span></div>
        </nav>

        <button className="btn btn-primary" style={{ margin: '0 12px', marginBottom: '8px' }} onClick={handleNewConversation}>
          <Icons.Plus /> New Conversation
        </button>

        <div className="sidebar-section-title">Conversation History</div>

        <div className="sidebar-search">
          <Icons.Search />
          <input
            type="text"
            placeholder="Search conversations"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="sidebar-conversations">
          {filteredThreads.map(thread => (
            <div
              key={thread.id}
              className={`conversation-item ${activeThread?.id === thread.id ? 'active' : ''}`}
              onClick={() => selectThread(thread)}
            >
              <span className="conversation-item-title">{thread.title}</span>
              <span className="conversation-item-time">
                {new Date(thread.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <div className="conversation-item-actions">
                <button className="btn-ghost" style={{ padding: 2 }} onClick={e => { e.stopPropagation(); const name = prompt('Rename:', thread.title); if (name) renameThread(thread.id, name); }}>
                  <Icons.Edit />
                </button>
                <button className="btn-ghost" style={{ padding: 2 }} onClick={e => { e.stopPropagation(); deleteThread(thread.id); }}>
                  <Icons.Trash />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Memory Stats in Sidebar */}
        {memoryStats && (
          <div style={{ padding: '12px', borderTop: '1px solid var(--color-border)', marginTop: 'auto' }}>
            <div className="sidebar-section-title" style={{ padding: '0 0 8px' }}>Agent Memory</div>
            <div className="learning-stat"><span>📝 Episodic</span><span className="learning-stat-value">{memoryStats.episodic_count}</span></div>
            <div className="learning-stat"><span>🧠 Learned</span><span className="learning-stat-value">{memoryStats.semantic_count}</span></div>
            <div className="learning-stat"><span>📄 AGENTS.md</span><span className="learning-stat-value">v{memoryStats.agents_md_version}</span></div>
          </div>
        )}
      </aside>

      {/* ── Main Content ── */}
      <main className="app-main">
        {/* Top Bar */}
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-brand">ForgeX</span>
            <div className="topbar-breadcrumb">
              <span>›</span>
              <span>{activeConfig?.name || 'Agent'}</span>
              {activeThread && <><span>›</span><span>{activeThread.title}</span></>}
            </div>
          </div>
          <div className="topbar-right">
            {learningStats && (
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>
                🧠 {learningStats.total_events} learnings
              </span>
            )}
            <button className="btn-icon" title="Agent Settings" onClick={() => setDrawerOpen(true)}>
              <Icons.Settings />
            </button>
          </div>
        </header>

        {/* Chat Area */}
        <div className="chat-area">
          {!activeThread || messages.length === 0 ? (
            <WelcomeScreen onSend={handleSend} onNewConversation={handleNewConversation} agentName={activeConfig?.name} />
          ) : (
            <ChatTimeline
              messages={messages}
              toolCalls={toolCalls}
              todos={todos}
              onFeedback={handleFeedback}
            />
          )}

          {/* Composer */}
          <Composer
            onSend={handleSend}
            isStreaming={isStreaming}
            onStop={stopStream}
          />
        </div>
      </main>

      {/* ── Config Drawer ── */}
      {drawerOpen && (
        <ConfigDrawer
          config={activeConfig}
          tools={tools}
          memoryStats={memoryStats}
          activeTab={drawerTab}
          onTabChange={setDrawerTab}
          onClose={() => setDrawerOpen(false)}
          onUpdate={(data) => activeConfig && updateConfig(activeConfig.id, data)}
          configId={activeConfig?.id}
        />
      )}

      {/* Error Toast */}
      {error && (
        <div style={{
          position: 'fixed', bottom: 20, right: 20, padding: '12px 20px',
          background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--color-error)',
          borderRadius: 'var(--radius-md)', color: 'var(--color-error)',
          fontSize: 'var(--font-size-sm)', zIndex: 50, animation: 'slideUp 0.3s ease-out',
        }}>
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// Welcome Screen
// ═══════════════════════════════════════════════════════════════════════════

function WelcomeScreen({ onSend, onNewConversation, agentName }: { onSend: (msg: string) => void; onNewConversation: () => void; agentName?: string }) {
  const suggestions = [
    '🔢 Calculate 15% of 2500',
    '🔍 Search for latest AI trends',
    '🌐 Fetch https://example.com',
    '📝 Help me write a project plan',
  ];

  return (
    <div className="chat-welcome">
      <h1>Hello, great to see you!</h1>
      <p>
        I'm <strong>{agentName || 'ForgeX'}</strong>, your AI agent with self-learning capabilities.
        I remember past interactions and learn from your feedback.
        Enter a task or try one of these:
      </p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginTop: '8px' }}>
        {suggestions.map((s, i) => (
          <button
            key={i}
            className="btn btn-secondary"
            onClick={() => { onNewConversation(); setTimeout(() => onSend(s), 200); }}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// Chat Timeline
// ═══════════════════════════════════════════════════════════════════════════

function ChatTimeline({ messages, toolCalls, todos, onFeedback }: {
  messages: ChatMessage[];
  toolCalls: ToolCallState[];
  todos: TodoItem[];
  onFeedback: (msgId: string, rating: 'positive' | 'negative') => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, toolCalls, todos]);

  return (
    <div className="chat-timeline">
      {/* Todos */}
      {todos.length > 0 && <TodoPanel todos={todos} />}

      {messages.map((msg, i) => (
        <div key={msg.id}>
          {msg.role === 'user' ? (
            <div className="message message-user">
              <div className="message-bubble">{msg.content}</div>
            </div>
          ) : (
            <div className="message message-assistant">
              <div className="message-avatar">F</div>
              <div className="message-content">
                {/* Show tool calls before the message */}
                {i === messages.length - 1 && toolCalls.map(tc => (
                  <ToolCallCard key={tc.tool_call_id} toolCall={tc} />
                ))}
                <div className="message-bubble">
                  <MessageContent content={msg.content} />
                  {msg.isStreaming && <span className="loading-spinner" style={{ display: 'inline-block', marginLeft: 8, verticalAlign: 'middle' }} />}
                </div>
                {/* Feedback buttons */}
                {!msg.isStreaming && (
                  <div className="message-feedback">
                    <button
                      className={`feedback-btn ${msg.feedback === 'positive' ? 'active-positive' : ''}`}
                      onClick={() => onFeedback(msg.id, 'positive')}
                      title="Good response — I'll learn from this"
                    >
                      <Icons.ThumbsUp />
                    </button>
                    <button
                      className={`feedback-btn ${msg.feedback === 'negative' ? 'active-negative' : ''}`}
                      onClick={() => onFeedback(msg.id, 'negative')}
                      title="Bad response — I'll improve"
                    >
                      <Icons.ThumbsDown />
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}

      <div ref={bottomRef} />
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// Message Content (simple markdown-like rendering)
// ═══════════════════════════════════════════════════════════════════════════

function MessageContent({ content }: { content: string }) {
  if (!content) return null;

  // Simple markdown: bold, code, lists, line breaks
  const parts = content.split('\n').map((line, i) => {
    // Bold
    let processed = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Inline code
    processed = processed.replace(/`(.*?)`/g, '<code>$1</code>');
    // List items
    if (processed.startsWith('- ')) {
      processed = '• ' + processed.slice(2);
    }

    return <span key={i} dangerouslySetInnerHTML={{ __html: processed + (i < content.split('\n').length - 1 ? '<br/>' : '') }} />;
  });

  return <>{parts}</>;
}


// ═══════════════════════════════════════════════════════════════════════════
// Tool Call Card
// ═══════════════════════════════════════════════════════════════════════════

function ToolCallCard({ toolCall }: { toolCall: ToolCallState }) {
  const [expanded, setExpanded] = useState(false);

  const toolIcons: Record<string, string> = {
    calculator: '🔢',
    web_search: '🔍',
    http_fetch: '🌐',
    document_inspector: '📄',
  };

  const formattedResult =
    typeof toolCall.result === 'string'
      ? toolCall.result
      : toolCall.result
      ? JSON.stringify(toolCall.result, null, 2)
      : '';

  return (
    <div className="tool-card">
      <div className="tool-card-header" onClick={() => setExpanded(!expanded)} style={{ cursor: 'pointer' }}>
        <div className={`tool-card-icon ${toolCall.status}`}>
          {toolCall.status === 'running' ? <span className="loading-spinner" /> : <Icons.Wrench />}
        </div>
        <span className="tool-card-name">
          {toolIcons[toolCall.tool_name] || '🔧'} {toolCall.tool_name}
        </span>
        <span className={`tool-card-status ${toolCall.status}`}>
          {toolCall.status === 'running' ? 'Running...' : 'Completed'}
        </span>
        <Icons.ChevronDown />
      </div>
      {(expanded || toolCall.status === 'running') && (
        <div className="tool-card-body">
          {toolCall.args && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>Input:</span>
              <pre>{JSON.stringify(toolCall.args, null, 2)}</pre>
            </div>
          )}
          {formattedResult && (
            <div>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>Result:</span>
              <pre>{formattedResult}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// Todo Panel
// ═══════════════════════════════════════════════════════════════════════════

function TodoPanel({ todos }: { todos: TodoItem[] }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="todo-panel">
      <div className="todo-panel-header" onClick={() => setCollapsed(!collapsed)}>
        <span className="todo-panel-title">📋 Task Plan ({todos.filter(t => t.status === 'completed').length}/{todos.length})</span>
        <Icons.ChevronDown />
      </div>
      {!collapsed && (
        <div className="todo-list">
          {todos.map(todo => (
            <div key={todo.id} className="todo-item">
              <div className={`todo-item-check ${todo.status}`}>
                {todo.status === 'completed' && <Icons.Check />}
                {todo.status === 'in_progress' && <span className="loading-spinner" style={{ width: 10, height: 10 }} />}
              </div>
              <span className={`todo-item-text ${todo.status}`}>{todo.title}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// Composer
// ═══════════════════════════════════════════════════════════════════════════

function Composer({ onSend, isStreaming, onStop }: {
  onSend: (content: string) => void;
  isStreaming: boolean;
  onStop: () => void;
}) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    onSend(input.trim());
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
  };

  return (
    <div className="composer">
      <div className="composer-inner">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Enter a task or message — I learn from every interaction..."
          rows={1}
        />
        <div className="composer-actions">
          <button className="btn-icon" title="Upload file">
            <Icons.Upload />
          </button>
          {isStreaming ? (
            <button className="btn-send" onClick={onStop} title="Stop">
              <Icons.Stop />
            </button>
          ) : (
            <button className="btn-send" onClick={handleSend} disabled={!input.trim()} title="Send">
              <Icons.Send />
            </button>
          )}
        </div>
      </div>
      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', textAlign: 'center', marginTop: 6 }}>
        ForgeX learns from your feedback. Use 👍👎 to help me improve.
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════
// Config Drawer
// ═══════════════════════════════════════════════════════════════════════════

function ConfigDrawer({ config, tools, memoryStats, activeTab, onTabChange, onClose, onUpdate, configId }: {
  config: any;
  tools: any[];
  memoryStats: any;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onClose: () => void;
  onUpdate: (data: any) => void;
  configId?: string;
}) {
  const [localPrompt, setLocalPrompt] = useState(config?.system_prompt || '');
  const [localName, setLocalName] = useState(config?.name || '');
  const [planningEnabled, setPlanningEnabled] = useState(config?.planning_enabled || false);
  const [semanticMemories, setSemanticMemories] = useState<SemanticMemory[]>([]);
  const [episodicMemories, setEpisodicMemories] = useState<EpisodicMemory[]>([]);
  const [learningLog, setLearningLog] = useState<LearningEvent[]>([]);
  const [agentsMd, setAgentsMd] = useState('');

  useEffect(() => {
    setLocalPrompt(config?.system_prompt || '');
    setLocalName(config?.name || '');
    setPlanningEnabled(config?.planning_enabled || false);
  }, [config]);

  useEffect(() => {
    if (configId && activeTab === 'memory') {
      memoryApi.getSemantic(configId).then(setSemanticMemories).catch(console.error);
      memoryApi.getEpisodic(configId).then(setEpisodicMemories).catch(console.error);
      memoryApi.getLearningLog(configId).then(setLearningLog).catch(console.error);
      memoryApi.getAgentsMd(configId).then(d => setAgentsMd(d.content || '')).catch(console.error);
    }
  }, [configId, activeTab]);

  const handleSave = () => {
    onUpdate({
      name: localName,
      system_prompt: localPrompt,
      planning_enabled: planningEnabled,
    });
  };

  const handleSaveMemory = async () => {
    if (configId) {
      await memoryApi.updateAgentsMd(configId, agentsMd);
    }
  };

  const tabs = ['basic', 'tools', 'memory', 'behavior', 'advanced'];

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="drawer-header">
          <span className="drawer-title">⚙️ Agent Settings</span>
          <button className="btn-icon" onClick={onClose}><Icons.X /></button>
        </div>

        <div className="drawer-tabs">
          {tabs.map(tab => (
            <div key={tab} className={`drawer-tab ${activeTab === tab ? 'active' : ''}`} onClick={() => onTabChange(tab)}>
              {tab === 'basic' && '📝 Basic'}
              {tab === 'tools' && '🔧 Tools'}
              {tab === 'memory' && '🧠 Memory'}
              {tab === 'behavior' && '⚡ Behavior'}
              {tab === 'advanced' && '🔬 Advanced'}
            </div>
          ))}
        </div>

        <div className="drawer-body">
          {activeTab === 'basic' && (
            <>
              <div className="form-group">
                <label className="form-label">Agent Name</label>
                <input className="form-input" value={localName} onChange={e => setLocalName(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">System Prompt</label>
                <textarea className="form-textarea" value={localPrompt} onChange={e => setLocalPrompt(e.target.value)} rows={8} />
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>
                  {localPrompt.length} characters
                </span>
              </div>
              <div className="form-group">
                <div className="form-toggle" onClick={() => setPlanningEnabled(!planningEnabled)}>
                  <div className={`toggle-switch ${planningEnabled ? 'active' : ''}`} />
                  <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Enable task planning</span>
                </div>
              </div>
              <button className="btn btn-primary" onClick={handleSave}>Save Changes</button>
            </>
          )}

          {activeTab === 'tools' && (
            <>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 16 }}>
                Built-in tools are created with the <code>@tool</code> decorator and can be toggled per agent.
              </p>
              {tools.map(tool => (
                <div key={tool.id} className="form-checkbox">
                  <div className={`checkbox-box checked`}><Icons.Check /></div>
                  <div>
                    <div style={{ fontWeight: 500, color: 'var(--color-text-primary)' }}>
                      {tool.name} {tool.is_builtin && <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-accent)' }}>built-in</span>}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>{tool.description}</div>
                  </div>
                </div>
              ))}
            </>
          )}

          {activeTab === 'memory' && (
            <>
              {/* Memory Stats */}
              {memoryStats && (
                <div className="memory-panel" style={{ marginBottom: 16 }}>
                  <div className="memory-panel-header">
                    <Icons.Brain /> <strong style={{ fontSize: 'var(--font-size-sm)' }}>Memory Overview</strong>
                  </div>
                  <div className="learning-stat"><span>Episodic Memories</span><span className="learning-stat-value">{memoryStats.episodic_count}</span></div>
                  <div className="learning-stat"><span>Learned Knowledge</span><span className="learning-stat-value">{memoryStats.semantic_count}</span></div>
                  <div className="learning-stat"><span>AGENTS.md Version</span><span className="learning-stat-value">v{memoryStats.agents_md_version}</span></div>
                </div>
              )}

              {/* Semantic Memories */}
              <div style={{ marginBottom: 16 }}>
                <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 8 }}>🧠 Learned Knowledge</h4>
                {semanticMemories.length === 0 ? (
                  <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-tertiary)' }}>
                    No learned knowledge yet. The agent learns from interactions and feedback.
                  </p>
                ) : (
                  semanticMemories.map(m => (
                    <div key={m.id} className="memory-item">
                      <span className={`memory-badge ${m.category}`}>{m.category}</span>
                      <span style={{ flex: 1, color: 'var(--color-text-secondary)' }}>{m.value}</span>
                      <span className="memory-confidence">{m.confidence}%</span>
                    </div>
                  ))
                )}
              </div>

              {/* Episodic Memories */}
              <div style={{ marginBottom: 16 }}>
                <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 8 }}>📖 Key Interactions</h4>
                {episodicMemories.length === 0 ? (
                  <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-tertiary)' }}>
                    No episodic memories yet. They'll be created from conversations.
                  </p>
                ) : (
                  episodicMemories.map(m => (
                    <div key={m.id} className="memory-item">
                      <span style={{ color: 'var(--color-text-secondary)' }}>{m.summary}</span>
                      <span className="memory-confidence">⭐ {m.importance}</span>
                    </div>
                  ))
                )}
              </div>

              {/* AGENTS.md Editor */}
              <div style={{ marginBottom: 16 }}>
                <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 8 }}>📄 AGENTS.md</h4>
                <textarea
                  className="form-textarea"
                  value={agentsMd}
                  onChange={e => setAgentsMd(e.target.value)}
                  rows={6}
                  placeholder="Write persistent memory notes here. This content is always loaded by the agent."
                />
                <button className="btn btn-secondary" onClick={handleSaveMemory} style={{ marginTop: 8 }}>
                  Save Memory
                </button>
              </div>

              {/* Learning Log */}
              <div>
                <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 8 }}>📊 Learning Log</h4>
                {learningLog.length === 0 ? (
                  <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-tertiary)' }}>
                    No learning events yet.
                  </p>
                ) : (
                  learningLog.slice(0, 10).map(e => (
                    <div key={e.id} style={{ fontSize: 'var(--font-size-xs)', padding: '6px 0', borderBottom: '1px solid var(--color-border-subtle)', color: 'var(--color-text-tertiary)' }}>
                      <span style={{ color: 'var(--color-accent)' }}>{e.event_type}</span> — {e.description}
                    </div>
                  ))
                )}
              </div>
            </>
          )}

          {activeTab === 'behavior' && (
            <>
              <div className="form-group">
                <label className="form-label">Response Format</label>
                <select className="form-input" defaultValue={config?.response_format || 'plain_text'}>
                  <option value="plain_text">Plain Text</option>
                  <option value="markdown">Markdown</option>
                  <option value="summary">Summary Schema</option>
                  <option value="requirements">Requirements Schema</option>
                  <option value="json_schema">Custom JSON Schema</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Subagents</label>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', marginBottom: 8 }}>
                  ⚠️ Custom subagents are isolated workers that return a report to the coordinator.
                </p>
                <button className="btn btn-secondary"><Icons.Plus /> Add Subagent</button>
              </div>
              <div className="form-group">
                <label className="form-label">Interrupt Policy</label>
                <div className="form-checkbox">
                  <div className="checkbox-box checked"><Icons.Check /></div>
                  <span>Require approval for write_file / edit_file</span>
                </div>
                <div className="form-checkbox">
                  <div className="checkbox-box checked"><Icons.Check /></div>
                  <span>Require approval for delete operations</span>
                </div>
              </div>
            </>
          )}

          {activeTab === 'advanced' && (
            <>
              <div className="form-group">
                <label className="form-label">Backend Mode</label>
                <select className="form-input" defaultValue={config?.backend_mode || 'state'}>
                  <option value="state">StateBackend (ephemeral filesystem)</option>
                  <option value="persistent">PersistentBackend</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Model</label>
                <input className="form-input" value="Azure Claude (claude-sonnet-4-5)" disabled style={{ opacity: 0.6 }} />
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>Model is server-managed</span>
              </div>
              <div className="form-group">
                <div className="form-toggle">
                  <div className={`toggle-switch ${config?.debug_mode ? 'active' : ''}`} />
                  <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Debug Mode</span>
                </div>
              </div>
              <div style={{ padding: 12, background: 'rgba(249, 115, 22, 0.05)', border: '1px solid rgba(249, 115, 22, 0.15)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>
                🧪 <strong>Experimental:</strong> State/context schema configuration is backend-owned in v1.
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
