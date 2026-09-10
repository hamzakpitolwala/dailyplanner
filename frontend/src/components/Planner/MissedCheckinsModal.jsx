import { useState, useEffect } from 'react';
import { fetchMissedReasons, fetchAlternateActivities, postTaskCheckin } from '../../api/taskApi';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle, FileText } from 'lucide-react';

export const MissedCheckinsModal = ({
  tasks,
  onComplete,
  setMessage
}) => {
  const [reasons, setReasons] = useState([]);
  const [alternates, setAlternates] = useState([]);
  
  // State maps taskId -> { missed_reason_id, alternate_activity_id, notes }
  const [checkinsData, setCheckinsData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    /**
     * Load Options.
     */
    const loadOptions = async () => {
      try {
        const fetchedReasons = await fetchMissedReasons();
        setReasons(fetchedReasons);
        const fetchedAlternates = await fetchAlternateActivities();
        setAlternates(fetchedAlternates);
        
        // Initialize state
        const initial = {};
        tasks.forEach(t => {
          initial[t.id] = { missed_reason_id: '', alternate_activity_id: '', notes: '' };
        });
        setCheckinsData(initial);
      } catch (err) {
        setMessage(err.message);
      }
    };
    loadOptions();
  }, [tasks, setMessage]);

  /**
   * Handle Change.
   */
  const handleChange = (taskId, field, value) => {
    setCheckinsData(prev => ({
      ...prev,
      [taskId]: {
        ...prev[taskId],
        [field]: value
      }
    }));
  };

  /**
   * Handle Submit.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      for (const t of tasks) {
        const data = checkinsData[t.id];
        // Validate required
        if (t.requires_reason && !data.missed_reason_id) {
          throw new Error(`Reason is required for task: ${t.title}`);
        }
        
        await postTaskCheckin(t.id, {
          status: t.status, // Preserve the auto-marked status
          missed_reason_id: data.missed_reason_id || null,
          alternate_activity_id: data.alternate_activity_id || null,
          notes: data.notes || null
        });
      }
      setMessage("Missed check-ins submitted successfully.");
      onComplete();
    } catch (err) {
      setMessage(err.message);
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-sm">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", bounce: 0, duration: 0.3 }}
          className="bg-card w-full max-w-2xl rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col max-h-[85vh]"
        >
          {/* Header */}
          <div className="px-6 py-5 border-b border-border bg-red-50/50 dark:bg-red-950/20 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-text">Review Missed Tasks</h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                These tasks from previous days weren't marked as done. Please provide context.
              </p>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="flex flex-col overflow-hidden flex-1">
            <div className="p-6 space-y-6 overflow-y-auto flex-1">
              {tasks.map((t, index) => {
                const data = checkinsData[t.id] || {};
                return (
                  <div key={t.id} className="bg-zinc-50 dark:bg-zinc-900/50 border border-border/50 rounded-xl p-5 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-red-500/50"></div>
                    
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-bold text-text text-base flex items-center gap-2">
                        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-zinc-200 dark:bg-zinc-800 text-xs font-semibold text-zinc-600 dark:text-zinc-400">
                          {index + 1}
                        </span>
                        {t.title}
                      </h4>
                      <span className="px-2.5 py-1 rounded-md text-xs font-semibold uppercase tracking-wider bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                        {t.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    
                    <div className="space-y-4">
                      {t.requires_reason && (
                        <div>
                          <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                            Reason for missing <span className="text-red-500">*</span>
                          </label>
                          <select
                            className="w-full bg-card border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all appearance-none"
                            value={data.missed_reason_id || ''}
                            onChange={(e) => handleChange(t.id, 'missed_reason_id', e.target.value)}
                            required
                          >
                            <option value="">-- Select a reason --</option>
                            {reasons.map(r => (
                              <option key={r.id} value={r.id}>{r.name}</option>
                            ))}
                          </select>
                        </div>
                      )}

                      {t.allows_alternate && (
                        <div>
                          <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                            Alternate Activity
                          </label>
                          <select
                            className="w-full bg-card border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all appearance-none"
                            value={data.alternate_activity_id || ''}
                            onChange={(e) => handleChange(t.id, 'alternate_activity_id', e.target.value)}
                          >
                            <option value="">-- Select an alternate activity --</option>
                            {alternates.map(a => (
                              <option key={a.id} value={a.id}>{a.name}</option>
                            ))}
                          </select>
                        </div>
                      )}

                      <div>
                        <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                          <FileText className="w-3 h-3" /> Notes
                        </label>
                        <input
                          className="w-full bg-card border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                          placeholder="Brief note or reflection..."
                          value={data.notes || ''}
                          onChange={(e) => handleChange(t.id, 'notes', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="px-6 py-4 border-t border-border bg-zinc-50/50 dark:bg-zinc-900/50 flex justify-end gap-3 flex-shrink-0">
              <button 
                type="button" 
                onClick={onComplete}
                disabled={isSubmitting}
                className="px-5 py-2.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-text text-sm font-semibold rounded-xl transition-colors disabled:opacity-50"
              >
                Skip for now
              </button>
              <button 
                type="submit" 
                disabled={isSubmitting}
                className="px-6 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-xl shadow-md shadow-primary/20 transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <CheckCircle className="w-4 h-4" />
                )}
                Submit All Check-ins
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
