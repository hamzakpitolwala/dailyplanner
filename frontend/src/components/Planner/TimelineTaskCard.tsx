import { useState, type FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Edit2, Trash2, MoreVertical, Plus, BookmarkPlus } from 'lucide-react';
import { cn, getStatusColor, getPriorityLabel, timeToPixels, calculateDurationPixels } from './TimelineUtils';
import { TaskCheckinModal } from './TaskCheckinModal';
import { TASK_STATUSES } from '../../utils/constants';

interface Task {
  id: string;
  title: string;
  description?: string;
  priority: number;
  status: string;
  start_time?: string;
  due_date?: string;
  requires_reason?: number;
  allows_alternate?: number;
  missed_reason?: string;
  alternate_activity?: string;
  source_template_name?: string;
  source_template_task_id?: string;
  subtasks?: { id: string; title: string; is_completed: boolean }[];
}

interface TimelineTaskCardProps {
  task: Task;
  pixelsPerMinute: number;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onCheckin: (taskId: string, data: any) => void;
  onAddToTemplate?: (task: Task) => void;
  isSubtask?: boolean;
  tasks?: Task[];
  plannerDate?: string;
  setMessage?: (msg: string) => void;
  layout?: { left: number; width: number };
}

export const TimelineTaskCard: FC<TimelineTaskCardProps> = ({ 
  task, 
  pixelsPerMinute,
  onEdit,
  onDelete,
  onCheckin,
  onAddToTemplate,
  isSubtask = false,
  tasks = [],
  plannerDate = '',
  setMessage = () => {},
  layout = { left: 0, width: 1 }
}) => {
  const top = timeToPixels(task.start_time, pixelsPerMinute);
  const height = Math.max(
    30, // Minimum height so it's clickable
    calculateDurationPixels(task.start_time || '', task.due_date || '', pixelsPerMinute)
  );

  const [isHovered, setIsHovered] = useState(false);

  const formatTime = (isoString?: string) => {
    if (!isoString) return '';
    if (isoString.includes('T')) {
      return isoString.split('T')[1].substring(0, 5);
    }
    return isoString.substring(0, 5);
  };

  const [activeCheckinStatus, setActiveCheckinStatus] = useState<string | null>(null);
  const [isAddingSubtask, setIsAddingSubtask] = useState(false);

  const localToday = new Date().toLocaleDateString('en-CA');
  const taskDate = task.due_date ? task.due_date.split('T')[0] : '';
  const isPastDate = taskDate && taskDate < localToday;
  const isTerminalState = isPastDate || task.status === 'completed' || task.status === 'not_done' || task.status === 'pending_not_done' || task.status === 'partial_not_done';
  const isRescheduleDisabled = task.due_date ? new Date(task.due_date) < new Date() : false;

  const handleStatusClick = (newStatus: string) => {
    if (isTerminalState) return;
    
    if (newStatus === 'rescheduled') {
      if (isRescheduleDisabled) return;
      setActiveCheckinStatus(newStatus);
    } else if (newStatus === 'not_done' && (task.requires_reason === 1 || task.allows_alternate === 1)) {
      setActiveCheckinStatus(newStatus);
    } else {
      onCheckin(task.id, { status: newStatus });
    }
  };

  const submitCheckinModal = (checkinData: any) => {
    onCheckin(task.id, checkinData);
    setActiveCheckinStatus(null);
  };

  const baseLeftOffset = isSubtask ? 60 : 16; // px
  const rightOffset = 16; // px

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, zIndex: 50 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className={cn(
        "absolute rounded-xl border border-border/50 shadow-sm transition-shadow",
        "bg-card p-3 flex flex-col overflow-hidden hover:shadow-lg hover:border-zinc-300"
      )}
      style={{ 
        top, 
        height, 
        minHeight: isHovered ? 'max-content' : Math.max(80, height),
        zIndex: isHovered ? 50 : 10,
        left: `calc(${baseLeftOffset}px + ${layout.left} * (100% - ${baseLeftOffset + rightOffset}px))`,
        width: `calc(${layout.width} * (100% - ${baseLeftOffset + rightOffset}px))`
      }}
    >
      <div className="flex justify-between items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-zinc-800 dark:text-zinc-100 truncate">{task.title}</h4>
            <span className="text-xs shrink-0" title={`Priority ${task.priority}`}>
              {getPriorityLabel(task.priority)}
            </span>
          </div>
          {height > 60 && task.description && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 line-clamp-2">{task.description}</p>
          )}
          {task.status === 'not_done' && (task.requires_reason === 1 || task.allows_alternate === 1) && (
            <div className="flex flex-col gap-1 mt-1">
              {task.requires_reason === 1 && (
                <span className="text-[10px] text-red-700 dark:text-red-300 bg-red-100/50 dark:bg-red-900/30 px-1.5 py-0.5 rounded border border-red-200 dark:border-red-800">
                  Required Reason: {task.missed_reason || 'Pending...'}
                </span>
              )}
              {task.allows_alternate === 1 && (
                <span className="text-[10px] text-purple-700 dark:text-purple-300 bg-purple-100/50 dark:bg-purple-900/30 px-1.5 py-0.5 rounded border border-purple-200 dark:border-purple-800">
                  Alternate: {task.alternate_activity || 'None'}
                </span>
              )}
            </div>
          )}
          {((task.subtasks && task.subtasks.length > 0) || isAddingSubtask) && (
            <div className="mt-2 flex flex-col gap-1 w-full max-w-[200px]" onClick={e => e.stopPropagation()}>
              <div className="flex justify-between items-center text-[10px] text-zinc-500 dark:text-zinc-400 font-medium mb-1">
                <span>Sub-tasks</span>
                {task.subtasks && task.subtasks.length > 0 && (
                  <span>{task.subtasks.filter(s => s.is_completed).length}/{task.subtasks.length}</span>
                )}
              </div>
              <div className="flex flex-col gap-1">
                {task.subtasks?.map((sub, index) => (
                  <div key={sub.id || index} className="flex items-center gap-1 group/sub">
                    <input 
                      type="checkbox" 
                      className="w-3 h-3 text-orange-500 rounded border-zinc-300"
                      checked={sub.is_completed}
                      disabled={isTerminalState}
                      onChange={async (e) => {
                        if (isTerminalState) return;
                        const checked = e.target.checked;
                        if (!isSubtask && task.id && sub.id) {
                          const { updateSubtask } = await import('../../api/taskApi');
                          try {
                            await updateSubtask(task.id, sub.id, { is_completed: checked });
                            // Notify parent to reload tasks, or rely on parent timer. 
                            // Since we have no direct refresh prop, we just rely on loadTasks from PlannerPage if possible
                            // Or better: trigger a custom event
                            window.dispatchEvent(new Event('refresh-tasks'));
                          } catch (err) {
                            console.error(err);
                          }
                        }
                      }}
                    />
                    <span className={cn(
                      "text-[10px] flex-1 truncate transition-colors",
                      sub.is_completed ? "text-zinc-400 line-through" : "text-zinc-600"
                    )}>
                      {sub.title}
                    </span>
                    {!isTerminalState && (
                      <button
                        className="opacity-0 group-hover/sub:opacity-100 p-0.5 hover:bg-zinc-200 rounded text-red-500 transition-opacity"
                        onClick={async () => {
                          if (!window.confirm('Delete sub-task?')) return;
                          if (!isSubtask && task.id && sub.id) {
                            const { deleteSubtask } = await import('../../api/taskApi');
                            try {
                              await deleteSubtask(task.id, sub.id);
                              window.dispatchEvent(new Event('refresh-tasks'));
                            } catch (err) {
                              console.error(err);
                            }
                          }
                        }}
                        title="Delete sub-task"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                ))}
                {isAddingSubtask && !isTerminalState && (
                  <div className="flex items-center gap-1 mt-1">
                    <input 
                      type="text" 
                      autoFocus
                      className="text-[10px] w-full px-1 py-0.5 border border-orange-300 rounded focus:outline-none focus:ring-1 focus:ring-orange-500"
                      placeholder="New subtask... (Enter to save)"
                      onKeyDown={async (e) => {
                        if (e.key === 'Enter') {
                          const title = e.currentTarget.value.trim();
                          if (title && task.id) {
                            const { createSubtask } = await import('../../api/taskApi');
                            try {
                              await createSubtask(task.id, title);
                              setIsAddingSubtask(false);
                              window.dispatchEvent(new Event('refresh-tasks'));
                            } catch (err) {
                              console.error(err);
                            }
                          } else if (!title) {
                            setIsAddingSubtask(false);
                          }
                        } else if (e.key === 'Escape') {
                          setIsAddingSubtask(false);
                        }
                      }}
                      onBlur={(e) => {
                        // Delay closing slightly so clicking save (if we had a button) wouldn't get preempted
                        setTimeout(() => setIsAddingSubtask(false), 150);
                      }}
                    />
                  </div>
                )}
              </div>
              {task.subtasks && task.subtasks.length > 0 && (
                <div className="w-full bg-zinc-100 rounded-full h-1 mt-1 overflow-hidden border border-zinc-200">
                  <div 
                    className="bg-orange-500 h-full transition-all duration-300"
                    style={{ width: `${(task.subtasks.filter(s => s.is_completed).length / task.subtasks.length) * 100}%` }}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <AnimatePresence>
            {isHovered && (
              <motion.div 
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex items-center gap-1 bg-white/90 backdrop-blur rounded-lg p-1 shadow-sm border border-zinc-100"
              >
                {!isTerminalState && (
                  <button 
                    onClick={(e) => { e.stopPropagation(); setIsAddingSubtask(true); }}
                    className="p-1 hover:bg-zinc-100 rounded text-orange-600 transition-colors"
                    title="Add Subtask"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                )}
                {(!task.source_template_name && !task.source_template_task_id) && (
                  <>
                    {onAddToTemplate && (
                      <button 
                        onClick={() => onAddToTemplate(task)}
                        className="p-1 hover:bg-zinc-100 rounded text-amber-600 transition-colors"
                        title="Add to Active Template"
                      >
                        <BookmarkPlus className="w-4 h-4" />
                      </button>
                    )}
                    <button 
                      onClick={() => onEdit(task)}
                      className="p-1 hover:bg-zinc-100 rounded text-zinc-600 transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => onDelete(task.id)}
                      className="p-1 hover:bg-zinc-100 rounded text-black transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
          {!isHovered && !isTerminalState && (
             <button className="p-1 text-zinc-400 lg:hidden">
               <MoreVertical className="w-4 h-4" />
             </button>
          )}
        </div>
      </div>

      {isHovered && !isTerminalState && (
        <motion.div 
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 flex flex-wrap gap-1.5"
        >
          {TASK_STATUSES.map((s) => {
            const disabled = s.value === 'rescheduled' && isRescheduleDisabled;
            return (
              <button
                key={s.value}
                onClick={() => handleStatusClick(s.value)}
                disabled={disabled}
                className={cn(
                  "px-2 py-1 text-[10px] font-medium rounded border transition-colors",
                  task.status === s.value 
                    ? "bg-zinc-800 text-white border-zinc-800"
                    : disabled 
                      ? "bg-zinc-50 text-zinc-400 border-zinc-200 cursor-not-allowed"
                      : "bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50"
                )}
                style={task.status === s.value ? { backgroundColor: s.color, borderColor: s.color } : {}}
              >
                {s.label}
              </button>
            );
          })}
        </motion.div>
      )}

      <div className="mt-auto pt-2 flex items-center justify-between text-xs">
        <span className="text-zinc-500 font-medium bg-zinc-50 px-2 py-0.5 rounded-md">
          {formatTime(task.start_time)} - {formatTime(task.due_date)}
        </span>
        <span className={cn("px-2 py-0.5 rounded-full font-medium border", getStatusColor(task.status))}>
          {task.status?.replace(/_/g, ' ') || 'Pending'}
        </span>
      </div>

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
    </motion.div>
  );
};
