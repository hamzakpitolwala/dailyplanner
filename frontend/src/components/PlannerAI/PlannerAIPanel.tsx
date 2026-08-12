import { type FC, useState, useEffect } from 'react';
import { Sparkles, CalendarPlus, FileText, CalendarDays, Zap } from 'lucide-react';
import { ChatInput } from './ChatInput';
import { aiApi } from '../../api/aiApi';
import * as templateApi from '../../api/templateApi';
import { format, subDays } from 'date-fns';

export const PlannerAIPanel: FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [resultType, setResultType] = useState<'starter' | 'summary' | 'recommendations' | 'chat' | null>(null);
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string, structuredType?: string, structuredData?: any }[]>([]);

  useEffect(() => {
    fetchRecommendations();
  }, []);

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

  const handleChat = async (text: string) => {
    try {
      setLoading(true);
      setResultType('chat');
      const newMessages = [...messages, { role: 'user' as const, content: text }];
      setMessages(newMessages);

      const response = await aiApi.chat(newMessages);

      setMessages([...newMessages, {
        role: 'assistant',
        content: response.reply,
        structuredType: response.structuredType,
        structuredData: response.structuredData
      }]);
    } catch (err) {
      console.error(err);
      alert('Failed to send message.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (text: string) => {
    handleChat(text);
  };

  return (
    <div className="flex flex-col h-full bg-transparent w-full">
      {/* Header */}
      <div className="h-[72px] shrink-0 border-b border-border flex items-center px-6">
        <div className="flex items-center gap-2 text-zinc-800 font-semibold">
          <Sparkles className="w-5 h-5 text-orange-500" />
          Planner AI
        </div>
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
                  <div className={`p-3 rounded-lg text-sm whitespace-pre-wrap ${msg.role === 'user' ? 'bg-orange-500 text-white' : 'bg-white border border-zinc-200 text-zinc-800'}`}>
                    {msg.content}
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
              </div>
            ))}
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

