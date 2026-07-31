import { useState, type FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Edit2, Trash2, MoreVertical } from 'lucide-react';
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
}

interface TimelineTaskCardProps {
  task: Task;
  pixelsPerMinute: number;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onCheckin: (taskId: string, data: any) => void;
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
        "bg-card p-3 flex flex-col overflow-hidden hover:shadow-lg hover:border-slate-300"
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
            <h4 className="text-sm font-semibold text-slate-800 truncate">{task.title}</h4>
            <span className="text-xs shrink-0" title={`Priority ${task.priority}`}>
              {getPriorityLabel(task.priority)}
            </span>
          </div>
          {height > 60 && task.description && (
            <p className="text-xs text-slate-500 mt-1 line-clamp-2">{task.description}</p>
          )}
          {task.status === 'not_done' && (task.requires_reason === 1 || task.allows_alternate === 1) && (
            <div className="flex flex-col gap-1 mt-1">
              {task.requires_reason === 1 && (
                <span className="text-[10px] text-red-700 bg-red-100/50 px-1.5 py-0.5 rounded border border-red-200">
                  Required Reason: {task.missed_reason || 'Pending...'}
                </span>
              )}
              {task.allows_alternate === 1 && (
                <span className="text-[10px] text-purple-700 bg-purple-100/50 px-1.5 py-0.5 rounded border border-purple-200">
                  Alternate: {task.alternate_activity || 'None'}
                </span>
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
                className="flex items-center gap-1 bg-white/90 backdrop-blur rounded-lg p-1 shadow-sm border border-slate-100"
              >
                <button 
                  onClick={() => onEdit(task)}
                  className="p-1 hover:bg-slate-100 rounded text-slate-600 transition-colors"
                  title="Edit"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => onDelete(task.id)}
                  className="p-1 hover:bg-slate-100 rounded text-black transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
          {!isHovered && !isTerminalState && (
             <button className="p-1 text-slate-400 lg:hidden">
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
                    ? "bg-slate-800 text-white border-slate-800"
                    : disabled 
                      ? "bg-slate-50 text-slate-400 border-slate-200 cursor-not-allowed"
                      : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
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
        <span className="text-slate-500 font-medium bg-slate-50 px-2 py-0.5 rounded-md">
          {formatTime(task.start_time)} - {formatTime(task.due_date)}
        </span>
        <span className={cn("px-2 py-0.5 rounded-full font-medium border", getStatusColor(task.status))}>
          {task.status?.replace(/_/g, ' ') || 'Pending'}
        </span>
      </div>

      {activeCheckinStatus && (
        <TaskCheckinModal
          task={task}
          tasks={tasks}
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
