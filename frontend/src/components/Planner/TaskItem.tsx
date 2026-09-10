import { useState } from 'react';
import React from 'react';
import { Badge } from '../ui/Badge';
import { TASK_STATUSES } from '../../utils/constants';
import { TaskCheckinModal } from './TaskCheckinModal';
import { Edit2, Trash2, Clock, CheckCircle2, ChevronRight, FileText, CalendarClock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { Task } from '../../types';

interface TaskItemProps {
  task: Task;
  tasks: Task[];
  plannerDate: string;
  editTask: (task: Task) => void;
  deleteTask: (id: string) => void;
  onCheckin: (id: string, checkinData: any) => void;
  setMessage: (msg: string) => void;
}

const TaskItemComponent: React.FC<TaskItemProps> = ({
  task,
  tasks,
  plannerDate,
  editTask,
  deleteTask,
  onCheckin,
  setMessage
}) => {
  const [activeCheckinStatus, setActiveCheckinStatus] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const localToday = new Date().toLocaleDateString('en-CA');
  const taskDate = task.due_date ? task.due_date.split('T')[0] : '';
  const isPastDate = taskDate && taskDate < localToday;

  const isCompleted = task.status === 'completed';
  const isTerminalState = isPastDate || task.status === 'completed' || task.status === 'not_done' || task.status === 'pending_not_done' || task.status === 'partial_not_done';
  const isRescheduleDisabled = task.due_date && new Date(task.due_date) < new Date();

  /**
   * Handle Status Click.
   */
  const handleStatusClick = (newStatus: string) => {
    if (isTerminalState) return;
    
    if (newStatus === 'rescheduled') {
      if (isRescheduleDisabled) return;
      setActiveCheckinStatus(newStatus);
    } else if (newStatus === 'not_done' && (task.requires_reason || task.allows_alternate)) {
      setActiveCheckinStatus(newStatus);
    } else {
      // Direct update
      onCheckin(task.id, { status: newStatus });
    }
  };

  /**
   * Submit Checkin Modal.
   */
  const submitCheckinModal = (checkinData: any) => {
    onCheckin(task.id, checkinData);
    setActiveCheckinStatus(null);
  };

  // Utility to determine button styles based on state
  const getStatusButtonClass = (s: any) => {
    const isCurrentStatus = task.status === s.value;
    const isDisabled = s.value === 'rescheduled' && isRescheduleDisabled;
    
    if (isDisabled) return 'opacity-50 cursor-not-allowed bg-zinc-100 text-zinc-400 border-zinc-200 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-500';
    
    if (isCurrentStatus) {
      // Inline styles for dynamic colors since s.color is hex (e.g. #10b981)
      // We will apply border and text using Tailwind, but background using inline style if needed, 
      // or we can use opacity utilities on the inline style
      return 'text-white border-transparent shadow-sm';
    }
    
    return 'bg-card hover:bg-zinc-50 dark:hover:bg-zinc-800/50 border-border text-zinc-600 dark:text-zinc-300';
  };

  return (
    <motion.article 
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-card border border-border rounded-xl shadow-sm overflow-hidden transition-all duration-200 hover:shadow-md ${isCompleted ? 'opacity-70 grayscale-[0.2]' : ''}`}
    >
      {/* Header section - clickable to expand */}
      <div 
        className="p-4 sm:p-5 flex items-start gap-3 cursor-pointer select-none relative"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Status Indicator Bar */}
        <div 
          className="absolute left-0 top-0 bottom-0 w-1.5"
          style={{ backgroundColor: TASK_STATUSES.find(s => s.value === task.status)?.color || '#94a3b8' }}
        />

        <div className="flex-1 min-w-0 pl-1">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className={`font-semibold text-lg truncate ${isCompleted ? 'line-through text-zinc-500' : 'text-text'}`}>
              {task.title}
            </h3>
            <Badge status={task.status} />
            {task.priority && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400">
                P{task.priority}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-4 text-xs font-medium text-zinc-500 dark:text-zinc-400 mt-2">
            {task.due_date && (
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>Due: {new Date(task.due_date).toTimeString().substring(0, 5)}</span>
              </div>
            )}
            
            {task.checkins && task.checkins.length > 0 && (
              <div className="flex items-center gap-1.5 text-primary">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Checked In</span>
              </div>
            )}
          </div>
        </div>

        <motion.div 
          animate={{ rotate: expanded ? 90 : 0 }} 
          className="w-8 h-8 flex items-center justify-center rounded-full bg-zinc-50 dark:bg-zinc-900 text-zinc-400 flex-shrink-0"
        >
          <ChevronRight className="w-5 h-5" />
        </motion.div>
      </div>

      {/* Expandable Content */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 sm:px-5 sm:pb-5 pt-0 pl-5 sm:pl-6 border-t border-border/50 mt-1">
              
              {task.description && (
                <div className="mt-4 mb-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-1.5 flex items-center gap-1">
                    <FileText className="w-3 h-3" /> Description
                  </h4>
                  <p className="text-sm text-zinc-600 dark:text-zinc-300 bg-zinc-50 dark:bg-zinc-900/40 p-3 rounded-lg border border-border/50 whitespace-pre-wrap">
                    {task.description}
                  </p>
                </div>
              )}

              {/* Status toggles */}
              {!isTerminalState && (
                <div className="mt-5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-2">Update Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {TASK_STATUSES.map((s) => {
                      const isCurrentStatus = task.status === s.value;
                      return (
                        <button
                          key={s.value}
                          className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all duration-200 ${getStatusButtonClass(s)}`}
                          style={isCurrentStatus ? { backgroundColor: s.color } : {}}
                          disabled={Boolean(s.value === 'rescheduled' && isRescheduleDisabled)}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStatusClick(s.value);
                          }}
                        >
                          {s.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
              
              {/* Render Checkin Reason if available */}
              {isTerminalState && task.checkins && task.checkins.length > 0 && (
                <div className="mt-4 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30 p-3 rounded-lg text-sm text-blue-900 dark:text-blue-200">
                  <h4 className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Check-in Details
                  </h4>
                  <div className="space-y-1.5">
                    {task.checkins[task.checkins.length - 1].missed_reason && (
                      <p><strong className="font-semibold text-blue-950 dark:text-blue-100">Reason:</strong> {task.checkins[task.checkins.length - 1].missed_reason.name}</p>
                    )}
                    {task.checkins[task.checkins.length - 1].alternate_activity && (
                      <p><strong className="font-semibold text-blue-950 dark:text-blue-100">Alternate:</strong> {task.checkins[task.checkins.length - 1].alternate_activity.name}</p>
                    )}
                    {task.checkins[task.checkins.length - 1].notes && (
                      <p className="mt-2"><strong className="font-semibold text-blue-950 dark:text-blue-100">Notes:</strong> {task.checkins[task.checkins.length - 1].notes}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              {!isPastDate && (
                <div className="flex gap-2 justify-end mt-5 pt-4 border-t border-border/50">
                  <button 
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-zinc-600 dark:text-zinc-300 hover:text-primary hover:bg-primary/10 rounded-md transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      editTask(task);
                    }}
                  >
                    <Edit2 className="w-4 h-4" /> Edit
                  </button>
                  <button 
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-md transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteTask(task.id);
                    }}
                  >
                    <Trash2 className="w-4 h-4" /> Delete
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {activeCheckinStatus && (
          <TaskCheckinModal
            task={task}
            plannerDate={plannerDate}
            initialStatus={activeCheckinStatus}
            onSubmit={submitCheckinModal}
            onCancel={() => setActiveCheckinStatus(null)}
            setMessage={setMessage}
          />
        )}
      </AnimatePresence>
    </motion.article>
  );
};
export const TaskItem = React.memo(TaskItemComponent);
