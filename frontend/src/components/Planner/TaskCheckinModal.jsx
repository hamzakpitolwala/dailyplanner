import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { fetchMissedReasons, fetchAlternateActivities } from '../../api/taskApi';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, XCircle, Clock, Calendar, AlertTriangle, FileText } from 'lucide-react';

export const TaskCheckinModal = ({
  task,
  plannerDate,
  initialStatus,
  onSubmit,
  onCancel,
  setMessage
}) => {
  const [reasons, setReasons] = useState([]);
  const [alternates, setAlternates] = useState([]);
  
  const [status, setStatus] = useState(initialStatus);
  const [missedReasonId, setMissedReasonId] = useState('');
  const [alternateActivityId, setAlternateActivityId] = useState('');
  const [notes, setNotes] = useState('');
  
  /**
   * Get Local Time.
   */
  const getLocalTime = (isoString) => {
    if (!isoString) return '';
    return new Date(isoString).toTimeString().substring(0, 5);
  };
  const initialStart = getLocalTime(task.start_time);
  const initialEnd = getLocalTime(task.due_date);
  const [rescheduleStart, setRescheduleStart] = useState(initialStart);
  const [rescheduleEnd, setRescheduleEnd] = useState(initialEnd);
  const [error, setError] = useState('');

  useEffect(() => {
    /**
     * Load Options.
     */
    const loadOptions = async () => {
      try {
        if (task.requires_reason) {
          const fetchedReasons = await fetchMissedReasons();
          setReasons(fetchedReasons);
        }
        if (task.allows_alternate) {
          const fetchedAlternates = await fetchAlternateActivities();
          setAlternates(fetchedAlternates);
        }
      } catch (err) {
        setMessage(err.message);
      }
    };
    loadOptions();
  }, [task, setMessage]);

  /**
   * Handle Submit.
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    let new_start_time = undefined;
    let new_due_date = undefined;
    if (status === 'rescheduled') {
      if (!rescheduleStart || !rescheduleEnd) {
        setError('Please select start and end times for rescheduling.');
        return;
      }
      if (rescheduleStart >= rescheduleEnd) {
        setError('End time must be after start time.');
        return;
      }
      const proposedStartIso = new Date(`${plannerDate}T${rescheduleStart}:00`).toISOString();
      const proposedEndIso = new Date(`${plannerDate}T${rescheduleEnd}:00`).toISOString();
      
      new_start_time = proposedStartIso;
      new_due_date = proposedEndIso;
    }

    onSubmit({
      status,
      missed_reason_id: missedReasonId || null,
      alternate_activity_id: alternateActivityId || null,
      notes: notes || null,
      start_time: new_start_time,
      due_date: new_due_date
    });
  };

  const showReason = status === 'not_done' && task.requires_reason;
  const showAlternate = status === 'not_done' && task.allows_alternate;

  return createPortal(
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-sm" onClick={onCancel}>
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", bounce: 0, duration: 0.3 }}
          className="bg-card w-full max-w-lg rounded-2xl shadow-2xl border border-border overflow-hidden" 
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-zinc-50/50 dark:bg-zinc-900/50">
            <h2 className="text-xl font-bold text-text truncate pr-4">
              Check-in: <span className="font-medium text-zinc-500 dark:text-zinc-400">{task.title}</span>
            </h2>
            <button 
              onClick={onCancel}
              className="p-2 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-500 rounded-full transition-colors flex-shrink-0"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-5 overflow-y-auto max-h-[80vh]">
            
            {/* Status Selection */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                Current Status
              </label>
              <select
                className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium appearance-none"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="completed">✅ Done</option>
                <option value="not_done">❌ Not Done</option>
                <option value="partial">🌓 Partial</option>
                <option value="rescheduled">📅 Rescheduled</option>
                <option value="in_progress">🔄 In Progress</option>
                <option value="pending">⏳ Pending</option>
              </select>
            </div>

            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg border border-red-100 dark:border-red-900/30 text-sm">
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}

            {/* Conditional Reschedule Times */}
            <AnimatePresence>
              {status === 'rescheduled' && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="grid grid-cols-2 gap-4"
                >
                  <div>
                    <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Start Time
                    </label>
                    <input
                      className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                      type="time"
                      value={rescheduleStart}
                      onChange={(e) => setRescheduleStart(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> End Time
                    </label>
                    <input
                      className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                      type="time"
                      value={rescheduleEnd}
                      onChange={(e) => setRescheduleEnd(e.target.value)}
                      required
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Conditional Reason / Alternate */}
            <AnimatePresence>
              {(showReason || showAlternate) && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-5 pt-2 border-t border-border/50"
                >
                  {showReason && (
                    <div>
                      <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                        Reason for missing
                      </label>
                      <select
                        className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all appearance-none"
                        value={missedReasonId}
                        onChange={(e) => setMissedReasonId(e.target.value)}
                        required={task.requires_reason}
                      >
                        <option value="">-- Select a reason --</option>
                        {reasons.map(r => (
                          <option key={r.id} value={r.id}>{r.name}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {showAlternate && (
                    <div>
                      <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                        Alternate Activity
                      </label>
                      <select
                        className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all appearance-none"
                        value={alternateActivityId}
                        onChange={(e) => setAlternateActivityId(e.target.value)}
                      >
                        <option value="">-- Select an alternate activity --</option>
                        {alternates.map(a => (
                          <option key={a.id} value={a.id}>{a.name}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Notes */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <FileText className="w-3 h-3" /> Notes
              </label>
              <textarea
                className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all min-h-[100px] resize-y"
                placeholder="Add any context or reflection..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-6 border-t border-border mt-6">
              <button 
                type="button" 
                onClick={onCancel}
                className="px-5 py-2.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-text text-sm font-semibold rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button 
                type="submit"
                className="px-6 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-xl shadow-md shadow-primary/20 transition-all flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Submit Check-in
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>,
    document.body
  );
};
