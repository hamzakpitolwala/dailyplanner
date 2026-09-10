import { type FC } from 'react';
import { CheckCircle2, Circle, Clock, Info, Trash2 } from 'lucide-react';
import { cn } from './TimelineUtils';

interface Task {
  id: string;
  title: string;
  description?: string;
  start_time?: string;
  due_date?: string;
  status: string;
  subtasks?: any[];
  checkins?: any[];
}

interface PastTaskCardProps {
  task: Task;
  onDelete?: (id: string) => void;
}

export const PastTaskCard: FC<PastTaskCardProps> = ({ task, onDelete }) => {
  /**
   * Format Time.
   */
  const formatTime = (isoString?: string) => {
    if (!isoString) return '';
    return new Date(isoString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  };

  const isCompleted = task.status === 'completed';
  const hasSubtasks = task.subtasks && task.subtasks.length > 0;
  
  let checkinStatus = "Pending";
  let missedReason = null;
  let alternateActivity = null;

  if (task.checkins && task.checkins.length > 0) {
    const latestCheckin = task.checkins[task.checkins.length - 1];
    checkinStatus = latestCheckin.status;
    missedReason = latestCheckin.missed_reason?.name;
    alternateActivity = latestCheckin.alternate_activity?.name;
  } else {
    checkinStatus = isCompleted ? "completed" : task.status;
  }

  /**
   * Format Status.
   */
  const formatStatus = (status: string) => {
    return status.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  return (
    <div className="bg-white border border-zinc-100 shadow-sm rounded-xl p-4 flex flex-col gap-3 relative overflow-hidden opacity-90">
      <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-zinc-300"></div>
      
      <div className="flex items-start justify-between gap-4 pl-2">
        <div className="flex-1 min-w-0">
          <h4 className={cn("text-base font-semibold text-zinc-800 break-words", isCompleted && "line-through text-zinc-500")}>
            {task.title}
          </h4>
          {task.description && (
            <p className="text-sm text-zinc-600 mt-2 bg-zinc-50 p-2 rounded-md border border-zinc-100 whitespace-pre-wrap">{task.description}</p>
          )}
        </div>
        
        <div className="flex flex-col items-end shrink-0 gap-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn(
              "text-xs font-semibold px-2 py-1 rounded-md uppercase tracking-wider",
              isCompleted || checkinStatus === 'completed' || checkinStatus === 'done' ? "bg-green-100 text-green-700" :
              checkinStatus.includes('not_done') ? "bg-red-100 text-red-700" :
              checkinStatus.includes('partial') ? "bg-yellow-100 text-yellow-700" :
              "bg-zinc-100 text-zinc-600"
            )}>
              {formatStatus(checkinStatus)}
            </span>
            {onDelete && (
              <button 
                onClick={() => onDelete(task.id)}
                className="p-1 hover:bg-zinc-100 rounded text-zinc-400 hover:text-black transition-colors"
                title="Delete Task"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
          <div className="flex items-center gap-1.5 text-xs font-medium text-zinc-500">
            <Clock className="w-3.5 h-3.5" />
            {formatTime(task.start_time)} - {formatTime(task.due_date)}
          </div>
        </div>
      </div>

      {(missedReason || alternateActivity) && (
        <div className="pl-2 flex flex-col gap-1 mt-1">
          {missedReason && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 font-medium bg-red-50 p-2 rounded-lg">
              <Info className="w-3.5 h-3.5 shrink-0" />
              Missed Reason: {missedReason}
            </div>
          )}
          {alternateActivity && (
            <div className="flex items-center gap-1.5 text-xs text-blue-600 font-medium bg-blue-50 p-2 rounded-lg">
              <Info className="w-3.5 h-3.5 shrink-0" />
              Alternate Activity: {alternateActivity}
            </div>
          )}
        </div>
      )}

      {hasSubtasks && (
        <div className="pl-2 mt-2 flex flex-col gap-1.5 border-t border-zinc-100 pt-3">
          <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">Subtasks</span>
          {task.subtasks!.map(st => (
            <div key={st.id} className="flex items-start gap-2">
              {st.is_completed ? (
                <CheckCircle2 className="w-4 h-4 text-zinc-400 mt-0.5 shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-zinc-300 mt-0.5 shrink-0" />
              )}
              <span className={cn("text-sm text-zinc-600 break-words", st.is_completed && "line-through text-zinc-400")}>
                {st.title}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
