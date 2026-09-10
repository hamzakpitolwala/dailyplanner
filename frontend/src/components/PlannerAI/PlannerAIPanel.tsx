import { type FC, useState, useEffect, useRef } from 'react';
import { Sparkles, CalendarPlus, FileText, CalendarDays, Zap, Edit2, Check, X, MessageSquare, Plus, Clock, Timer, Zap as Priority, Trash2 } from 'lucide-react';
import { ChatInput } from './ChatInput';
import { MarkdownMessage } from './MarkdownMessage';
import { aiApi } from '../../api/aiApi';
import * as templateApi from '../../api/templateApi';
import { format, subDays } from 'date-fns';

// ── Human-readable labels for tool names ──
const TOOL_LABELS: Record<string, { label: string; icon: string }> = {
  create_task: { label: 'Create Task', icon: '📋' },
  update_task: { label: 'Update Task', icon: '✏️' },
  delete_task: { label: 'Delete Task', icon: '🗑️' },
  complete_task: { label: 'Complete Task', icon: '✅' },
  move_task: { label: 'Move Task', icon: '↕️' },
  reschedule_task: { label: 'Reschedule Task', icon: '📅' },
  add_subtask: { label: 'Add Subtask', icon: '📎' },
  apply_template: { label: 'Apply Template', icon: '📄' },
  list_templates: { label: 'List Templates', icon: '📂' },
  create_template: { label: 'Create Template', icon: '🆕' },
  add_task_to_template: { label: 'Add Tasks to Template', icon: '➕' },
};

// Hidden internal fields that should not show in the card
const HIDDEN_FIELDS = new Set(['user_id']);

// ── Format a time string for display ──
function formatTimeDisplay(val: string): string {
  if (!val) return '';
  // Handle HH:MM:SS or ISO datetime
  const match = val.match(/(\d{2}):(\d{2})/);
  if (match) {
    const h = parseInt(match[1]);
    const m = match[2];
    const ampm = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    return `${h12}:${m} ${ampm}`;
  }
  return val;
}

// ── Priority badge ──
function PriorityBadge({ value }: { value: number }) {
  const colors: Record<number, string> = {
    1: 'bg-red-100 text-red-700 border-red-200',
    2: 'bg-orange-100 text-orange-700 border-orange-200',
    3: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    4: 'bg-blue-100 text-blue-700 border-blue-200',
    5: 'bg-zinc-100 text-zinc-600 border-zinc-200',
  };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${colors[value] || colors[5]}`}>
      P{value}
    </span>
  );
}

// ── Task Card within the approval block ──
const TaskCard: FC<{
  task: any;
  index: number;
  onChange: (index: number, updated: any) => void;
  onRemove: (index: number) => void;
}> = ({ task, index, onChange, onRemove }) => {
  return (
    <div className="bg-white border border-zinc-200 rounded-lg p-2.5 flex flex-col gap-1.5 group relative">
      <button
        onClick={() => onRemove(index)}
        className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-red-500 transition-all"
        title="Remove task"
      >
        <Trash2 className="w-3 h-3" />
      </button>
      <input
        className="text-sm font-medium text-zinc-800 bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-orange-400 focus:outline-none px-0 py-0.5 transition-colors w-[calc(100%-20px)]"
        value={task.title || ''}
        onChange={e => onChange(index, { ...task, title: e.target.value })}
      />
      {task.description !== undefined && (
        <input
          className="text-xs text-zinc-500 bg-transparent border-b border-transparent hover:border-zinc-200 focus:border-orange-300 focus:outline-none px-0 py-0.5 transition-colors"
          value={task.description || ''}
          placeholder="Description (optional)"
          onChange={e => onChange(index, { ...task, description: e.target.value })}
        />
      )}
      <div className="flex items-center gap-3 flex-wrap">
        {task.target_time !== undefined && (
          <div className="flex items-center gap-1 text-xs text-zinc-500">
            <Clock className="w-3 h-3" />
            <input
              type="time"
              className="bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-orange-400 focus:outline-none text-xs px-0 py-0.5 transition-colors"
              value={task.target_time ? task.target_time.substring(0, 5) : ''}
              onChange={e => onChange(index, { ...task, target_time: e.target.value + ':00' })}
            />
          </div>
        )}
        {(task.start_time !== undefined || task.new_start_time !== undefined) && (
          <div className="flex items-center gap-1 text-xs text-zinc-500">
            <Clock className="w-3 h-3" />
            <input
              type="datetime-local"
              className="bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-orange-400 focus:outline-none text-xs px-0 py-0.5 transition-colors"
              value={(task.start_time || task.new_start_time || '').substring(0, 16)}
              onChange={e => {
                const key = task.new_start_time !== undefined ? 'new_start_time' : 'start_time';
                onChange(index, { ...task, [key]: e.target.value });
              }}
            />
          </div>
        )}
        {task.duration_minutes !== undefined && (
          <div className="flex items-center gap-1 text-xs text-zinc-500">
            <Timer className="w-3 h-3" />
            <input
              type="number"
              className="bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-orange-400 focus:outline-none text-xs w-10 px-0 py-0.5 transition-colors"
              value={task.duration_minutes}
              min={5}
              onChange={e => onChange(index, { ...task, duration_minutes: parseInt(e.target.value) || 60 })}
            />
            <span>min</span>
          </div>
        )}
        {task.priority !== undefined && (
          <select
            className="bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-orange-400 focus:outline-none text-xs px-0 py-0.5 transition-colors"
            value={task.priority}
            onChange={e => onChange(index, { ...task, priority: parseInt(e.target.value) })}
          >
            <option value={1}>🔥🔥🔥 P1</option>
            <option value={2}>🔥🔥 P2</option>
            <option value={3}>🔴 P3</option>
            <option value={4}>🟡 P4</option>
            <option value={5}>🟢 P5</option>
          </select>
        )}
      </div>
    </div>
  );
};

// ── Render simple key-value fields (non-task, non-hidden) ──
function renderField(key: string, value: any, onChange: (val: any) => void) {
  if (HIDDEN_FIELDS.has(key)) return null;
  if (key === 'tasks' || key === 'task_id') return null; // handled separately

  const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  if (typeof value === 'boolean') {
    return (
      <div key={key} className="flex items-center justify-between py-1">
        <span className="text-xs text-zinc-500">{label}</span>
        <input type="checkbox" checked={value} onChange={e => onChange(e.target.checked)} className="accent-orange-500" />
      </div>
    );
  }

  if (typeof value === 'number') {
    return (
      <div key={key} className="flex items-center justify-between py-1">
        <span className="text-xs text-zinc-500">{label}</span>
        <input
          type="number"
          value={value}
          onChange={e => onChange(parseInt(e.target.value) || 0)}
          className="text-xs text-right bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-orange-400 focus:outline-none w-20 py-0.5 transition-colors"
        />
      </div>
    );
  }

  // String fields
  const isTimeField = key.includes('time') || key.includes('date');
  return (
    <div key={key} className="flex items-center justify-between py-1 gap-2">
      <span className="text-xs text-zinc-500 shrink-0">{label}</span>
      <input
        type={isTimeField ? 'datetime-local' : 'text'}
        value={isTimeField ? String(value || '').substring(0, 16) : (value || '')}
        onChange={e => onChange(e.target.value)}
        className="text-xs text-right bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-orange-400 focus:outline-none flex-1 min-w-0 py-0.5 transition-colors"
      />
    </div>
  );
}

// ── ProposedAction: the main approval card ──
const ProposedAction: FC<{
  workflowId: string;
  msgId: string;
  toolCalls: any[];
  onApprove: (workflowId: string, msgId: string, overrides?: any) => void;
  onReject: (workflowId: string, msgId: string) => void;
}> = ({ workflowId, msgId, toolCalls, onApprove, onReject }) => {
  const tc = toolCalls[0];
  if (!tc) return null;

  const toolInfo = TOOL_LABELS[tc.tool_name] || { label: tc.tool_name, icon: '🔧' };
  const [args, setArgs] = useState<any>({ ...tc.arguments });

  const hasTasks = Array.isArray(args.tasks);

  /**
   * Update Field.
   */
  const updateField = (key: string, value: any) => {
    setArgs((prev: any) => ({ ...prev, [key]: value }));
  };

  /**
   * Update Task.
   */
  const updateTask = (index: number, updated: any) => {
    setArgs((prev: any) => {
      const tasks = [...(prev.tasks || [])];
      tasks[index] = updated;
      return { ...prev, tasks };
    });
  };

  /**
   * Remove Task.
   */
  const removeTask = (index: number) => {
    setArgs((prev: any) => {
      const tasks = [...(prev.tasks || [])];
      tasks.splice(index, 1);
      return { ...prev, tasks };
    });
  };

  // Get non-hidden, non-task fields to render
  const fieldKeys = Object.keys(args).filter(k => !HIDDEN_FIELDS.has(k) && k !== 'tasks');

  return (
    <div className="mt-2 flex flex-col gap-3 border border-orange-200 rounded-xl p-4 bg-gradient-to-b from-orange-50 to-white w-full max-w-[420px] shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-lg">{toolInfo.icon}</span>
        <div className="flex-1">
          <div className="text-sm font-semibold text-zinc-800">{toolInfo.label}</div>
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider">Review & Edit</div>
        </div>
      </div>

      {/* Simple fields */}
      {fieldKeys.length > 0 && (
        <div className="flex flex-col divide-y divide-zinc-100">
          {fieldKeys.map(key => {
            // For task_id, show as read-only short ID
            if (key === 'task_id') {
              return (
                <div key={key} className="flex items-center justify-between py-1">
                  <span className="text-xs text-zinc-500">Task</span>
                  <span className="text-xs text-zinc-400 font-mono">{String(args[key]).substring(0, 8)}…</span>
                </div>
              );
            }
            return renderField(key, args[key], (val) => updateField(key, val));
          })}
        </div>
      )}

      {/* Tasks list (for create_template, add_task_to_template) */}
      {hasTasks && args.tasks.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <div className="text-xs font-semibold text-zinc-600 flex items-center gap-1">
            📋 Tasks ({args.tasks.length})
          </div>
          <div className="flex flex-col gap-1.5 max-h-[280px] overflow-y-auto pr-1">
            {args.tasks.map((task: any, idx: number) => (
              <TaskCard key={idx} task={task} index={idx} onChange={updateTask} onRemove={removeTask} />
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 mt-1">
        <button
          onClick={() => onApprove(workflowId, msgId, args)}
          className="flex-1 flex items-center justify-center gap-1.5 bg-orange-600 hover:bg-orange-700 text-white text-sm py-2 rounded-lg transition-colors font-medium shadow-sm"
        >
          <Check className="w-4 h-4" /> Approve
        </button>
        <button
          onClick={() => onReject(workflowId, msgId)}
          className="flex-1 flex items-center justify-center gap-1.5 bg-white border border-zinc-300 hover:bg-zinc-50 text-zinc-700 text-sm py-2 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" /> Reject
        </button>
      </div>
    </div>
  );
};

export const PlannerAIPanel: FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [resultType, setResultType] = useState<'starter' | 'summary' | 'recommendations' | 'chat' | null>(null);
  const [messages, setMessages] = useState<{
    id?: string;
    role: 'user' | 'assistant';
    content: string;
    structuredType?: string;
    structuredData?: any;
    status?: string;
    workflowId?: string;
    toolCalls?: any[];
  }[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load recent conversation + recommendations on mount
  useEffect(() => {
    loadChatHistory();
    fetchRecommendations();
  }, []);

  /**
   * Load Chat History.
   */
  const loadChatHistory = async () => {
    try {
      const data = await aiApi.getRecentConversation();
      if (data?.conversation && data.messages?.length > 0) {
        setConversationId(data.conversation.id);
        const restored = data.messages.map((m: any) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content?.text || '',
          status: m.content?.tool_call ? 'completed' : 'completed',
          workflowId: undefined,
          toolCalls: m.content?.tool_call ? [m.content.tool_call] : undefined,
        }));
        setMessages(restored);
        setResultType('chat');
      }
    } catch (err) {
      // Silently fail — history is a nice-to-have, not critical
      console.error('Failed to load chat history:', err);
    } finally {
      setHistoryLoaded(true);
    }
  };

  /**
   * Handle New Conversation.
   */
  const handleNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setResultType(null);
    setResult(null);
  };

  /**
   * Fetch Recommendations.
   */
  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const data = await aiApi.getRecommendations('pending');
      if (data && data.length > 0) {
        setResult(data);
        setResultType('recommendations');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Generate Recommendations.
   */
  const handleGenerateRecommendations = async () => {
    try {
      setLoading(true);
      setResult(null);
      const data = await aiApi.generateRecommendations(7);
      setResult(data);
      setResultType('recommendations');
    } catch (err) {
      console.error(err);
      alert('Failed to generate recommendations.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Process Decision.
   */
  const handleProcessDecision = async (recId: string, decision: 'accepted' | 'rejected' | 'ignored', payloadOverride?: any) => {
    try {
      setLoading(true);
      await aiApi.processRecommendationDecision(recId, { decision, payload: payloadOverride });
      // Remove from list
      setResult((prev: any) => prev?.filter((r: any) => r.id !== recId) || null);
    } catch (err) {
      console.error(err);
      alert('Failed to process decision.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Generate Starter.
   */
  const handleGenerateStarter = async (extra_prompt = '') => {
    try {
      setLoading(true);
      setResult(null);
      const data = await aiApi.generateStarterPlan({ day_type: 'generic', extra_prompt });
      setResult(data);
      setResultType('starter');
    } catch (err) {
      console.error(err);
      alert('Failed to generate plan.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Summarize.
   */
  const handleSummarize = async (period: 'day' | 'week', extra_prompt = '') => {
    try {
      setLoading(true);
      setResult(null);
      const today = new Date();
      const start = period === 'week' ? subDays(today, 7) : today;
      const data = await aiApi.generateSummary({
        period_type: period,
        period_start: format(start, 'yyyy-MM-dd'),
        period_end: format(today, 'yyyy-MM-dd'),
        extra_prompt
      });
      setResult(data);
      setResultType('summary');
    } catch (err) {
      console.error(err);
      alert('Failed to generate summary.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Save Template.
   */
  const handleSaveTemplate = async (templateName: string, description: string, activities: any[]) => {
    try {
      const templateData = {
        name: templateName,
        description: description || '',
        template_tasks: activities.map((a: any) => ({
          title: a.title,
          category_id: null,
          priority: a.priority === 'high' ? 3 : a.priority === 'medium' ? 2 : 1,
          target_time: a.start_time,
          duration_minutes: 60, // Simplify for now
          requires_reason: false,
          allows_alternate: false,
          subtasks: []
        }))
      };
      await templateApi.createTemplate(templateData);
      alert('Template saved successfully!');
    } catch (err) {
      console.error(err);
      alert('Failed to save template.');
    }
  };

  /**
   * Handle Chat.
   */
  const handleChat = async (text: string) => {
    try {
      setLoading(true);
      setResultType('chat');

      const newMsgId = Date.now().toString();
      const newMessages = [...messages, { id: newMsgId, role: 'user' as const, content: text }];
      setMessages(newMessages);

      const response = await aiApi.agentChat(text, conversationId);

      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.message,
        status: response.status,
        workflowId: response.workflow_id,
        toolCalls: response.tool_calls
      }]);
    } catch (err) {
      console.error(err);
      alert('Failed to send message.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Approve.
   */
  const handleApprove = async (workflowId: string, msgId: string, editedArgs?: any) => {
    try {
      setLoading(true);

      // If the user edited the arguments, we should send that back to be executed.
      // For now, our backend agentApprove doesn't take overridden arguments natively in the endpoint
      // So we'd need to either update the backend or just approve. 
      // Wait, the prompt says "Add edit button to edit the model answer and auto-approve".
      // Let's modify aiApi.agentApprove to accept overriding arguments
      const response = await aiApi.agentApprove(workflowId, true, editedArgs);

      // Update the message status
      setMessages(prev => prev.map(m => m.id === msgId ? { ...m, status: 'completed' } : m));

      // Add success response
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.message,
        status: 'completed'
      }]);
      
      // Dispatch UI action if requested
      if (response.extra_data?.ui_action === 'highlight_template_task' && response.extra_data?.highlight_task_id) {
        window.dispatchEvent(new CustomEvent('HIGHLIGHT_TEMPLATE_TASK', { 
            detail: { taskId: response.extra_data.highlight_task_id } 
        }));
      }
    } catch (err) {
      console.error(err);
      alert('Failed to approve action.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Reject.
   */
  const handleReject = async (workflowId: string, msgId: string) => {
    try {
      setLoading(true);
      const response = await aiApi.agentApprove(workflowId, false);

      // Update the message status
      setMessages(prev => prev.map(m => m.id === msgId ? { ...m, status: 'rejected' } : m));

      // Add rejection response
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.message,
        status: 'completed'
      }]);
    } catch (err) {
      console.error(err);
      alert('Failed to reject action.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Submit.
   */
  const handleSubmit = (text: string) => {
    handleChat(text);
  };

  return (
    <div className="flex flex-col h-full bg-transparent w-full">
      {/* Header */}
      <div className="h-[72px] shrink-0 border-b border-border flex items-center justify-between px-6">
        <div className="flex items-center gap-2 text-zinc-800 font-semibold">
          <Sparkles className="w-5 h-5 text-orange-500" />
          <h3 className="text-sm font-semibold text-text truncate">Planner AI</h3>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleNewConversation}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-zinc-600 bg-white border border-zinc-200 rounded-lg hover:border-orange-300 hover:bg-orange-50 transition-colors"
            title="Start a new conversation"
          >
            <Plus className="w-3.5 h-3.5" />
            New Chat
          </button>
        )}
      </div>

      {/* Body */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto">
        {!loading && !resultType && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center text-center mt-10">
            <div className="text-4xl mb-4">👋</div>
            <h3 className="text-lg font-medium text-zinc-800 mb-2">Ask Planner AI anything.</h3>

            <div className="flex flex-col gap-3 mt-4 w-full max-w-sm">
              <button onClick={() => handleChat("Generate a starter plan for today")} className="flex items-center gap-3 p-3 text-sm text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:border-orange-300 hover:bg-orange-50 transition-colors">
                <CalendarPlus className="w-4 h-4 text-orange-500" />
                Generate Starter Plan
              </button>
              <button onClick={() => handleChat("Summarize my tasks and progress for today")} className="flex items-center gap-3 p-3 text-sm text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:border-orange-300 hover:bg-orange-50 transition-colors">
                <FileText className="w-4 h-4 text-orange-500" />
                Summarize Today
              </button>
              <button onClick={() => handleChat("Provide a summary of my schedule for this week")} className="flex items-center gap-3 p-3 text-sm text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:border-orange-300 hover:bg-orange-50 transition-colors">
                <CalendarDays className="w-4 h-4 text-orange-500" />
                Summarize This Week
              </button>
              <button onClick={() => handleGenerateRecommendations()} className="flex items-center gap-3 p-3 text-sm text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:border-orange-300 hover:bg-orange-50 transition-colors">
                <Zap className="w-4 h-4 text-orange-500" />
                Get Improvement Suggestions
              </button>
            </div>
          </div>
        )}

        {messages.length > 0 && resultType === 'chat' && (
          <div className="flex flex-col gap-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'self-end items-end' : 'self-start items-start'}`}>
                {msg.content && (
                  <div className={`p-3 rounded-lg text-sm ${msg.role === 'user' ? 'bg-orange-500 text-white whitespace-pre-wrap' : 'bg-white border border-zinc-200 text-zinc-800'}`}>
                    {msg.role === 'assistant' ? <MarkdownMessage content={msg.content} /> : msg.content}
                  </div>
                )}

                {msg.structuredType === 'starter' && msg.structuredData && (
                  <div className="mt-2 flex flex-col gap-4 border border-zinc-200 rounded-lg p-4 bg-white w-full max-w-[400px]">
                    <h3 className="font-medium text-zinc-800">{msg.structuredData.template_name}</h3>
                    <p className="text-sm text-zinc-600">{msg.structuredData.description}</p>
                    <div className="space-y-2 mt-2">
                      {msg.structuredData.activities.map((act: any, actIdx: number) => (
                        <div key={actIdx} className="text-sm border border-zinc-200 p-2 rounded bg-white">
                          <div className="font-medium">{act.title}</div>
                          <div className="text-zinc-500 text-xs">{act.start_time} - {act.end_time}</div>
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-2 mt-4">
                      <button onClick={() => handleSaveTemplate(msg.structuredData.template_name, msg.structuredData.description, msg.structuredData.activities)} className="px-4 py-2 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 flex-1">
                        Save as Template
                      </button>
                    </div>
                  </div>
                )}

                {msg.structuredType === 'summary' && msg.structuredData && (
                  <div className="mt-2 flex flex-col gap-4 border border-zinc-200 rounded-lg p-4 bg-white w-full max-w-[400px]">
                    <h3 className="font-medium text-zinc-800">Summary</h3>
                    <p className="text-sm text-zinc-600">{msg.structuredData.summary_text}</p>

                    {msg.structuredData.wins && msg.structuredData.wins.length > 0 && (
                      <div className="mt-2">
                        <h4 className="text-sm font-medium text-green-700 mb-1">Wins</h4>
                        <ul className="text-sm space-y-1">
                          {msg.structuredData.wins.map((w: any, actIdx: number) => (
                            <li key={actIdx} className="flex gap-2"><span className="text-green-500">•</span> <div><strong>{w.title}</strong>: {w.detail}</div></li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {msg.structuredData.issues && msg.structuredData.issues.length > 0 && (
                      <div className="mt-2">
                        <h4 className="text-sm font-medium text-red-700 mb-1">Issues</h4>
                        <ul className="text-sm space-y-1">
                          {msg.structuredData.issues.map((iss: any, actIdx: number) => (
                            <li key={actIdx} className="flex gap-2"><span className="text-red-500">•</span> <div><strong>{iss.title}</strong>: {iss.detail}</div></li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {msg.structuredData.suggestions && msg.structuredData.suggestions.length > 0 && (
                      <div className="mt-2">
                        <h4 className="text-sm font-medium text-orange-700 mb-1">Suggestions</h4>
                        <ul className="text-sm space-y-1">
                          {msg.structuredData.suggestions.map((s: any, actIdx: number) => (
                            <li key={actIdx} className="flex gap-2"><span className="text-orange-500">•</span> <div><strong>{s.title}</strong>: {s.description}</div></li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {msg.structuredType === 'recommendations' && msg.structuredData && Array.isArray(msg.structuredData) && (
                  <div className="mt-2 flex flex-col gap-4 w-full max-w-[400px]">
                    {msg.structuredData.length === 0 ? (
                      <div className="border border-zinc-200 rounded-lg p-4 bg-white"><p className="text-sm text-zinc-500">No pending recommendations.</p></div>
                    ) : (
                      <div className="space-y-4">
                        {msg.structuredData.map((rec: any) => (
                          <div key={rec.id} className="border border-zinc-200 rounded-lg p-4 bg-white shadow-sm">
                            <h4 className="font-semibold text-zinc-800 mb-1">{rec.title}</h4>
                            <p className="text-sm text-zinc-600 mb-3">{rec.explanation}</p>

                            {rec.kind === 'move_activity_time' && (
                              <div className="bg-orange-50 p-3 rounded text-sm mb-3 border border-orange-100 flex flex-col gap-2">
                                <div className="font-medium text-orange-800">Suggested Time Change:</div>
                                <div className="flex items-center gap-2">
                                  <label className="text-xs text-zinc-500">From:</label>
                                  <input type="time" defaultValue={rec.payload?.from_time || ''}
                                    onChange={(e) => rec.payload = { ...rec.payload, from_time: e.target.value }}
                                    className="border rounded px-2 py-1 bg-white text-xs" />
                                  <label className="text-xs text-zinc-500 ml-2">To:</label>
                                  <input type="time" defaultValue={rec.payload?.to_time || ''}
                                    onChange={(e) => rec.payload = { ...rec.payload, to_time: e.target.value }}
                                    className="border rounded px-2 py-1 bg-white text-xs" />
                                </div>
                              </div>
                            )}

                            <div className="flex gap-2">
                              <button onClick={() => handleProcessDecision(rec.id, 'accepted', rec.payload)} className="flex-1 bg-orange-600 hover:bg-orange-700 text-white text-sm py-1.5 rounded transition-colors">
                                Accept
                              </button>
                              <button onClick={() => handleProcessDecision(rec.id, 'rejected')} className="flex-1 bg-zinc-200 hover:bg-zinc-300 text-zinc-700 text-sm py-1.5 rounded transition-colors">
                                Reject
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {msg.status === 'proposed' && msg.workflowId && (
                  <ProposedAction
                    workflowId={msg.workflowId}
                    msgId={msg.id!}
                    toolCalls={msg.toolCalls || []}
                    onApprove={handleApprove}
                    onReject={handleReject}
                  />
                )}

              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center text-center mt-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mb-4"></div>
            <p className="text-zinc-500 text-sm">Thinking...</p>
          </div>
        )}


      </div>

      {/* Input */}
      <ChatInput onSubmit={handleSubmit} disabled={loading} />
    </div>
  );
};

