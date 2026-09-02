import { type FC } from 'react';
import { Plus } from 'lucide-react';
import { MonthCalendar } from './MonthCalendar';
import { todayIso } from '../../utils/constants';

interface PlannerHeaderProps {
  plannerDate: string;
  setPlannerDate: (date: string) => void;
  minDate?: string;
  onAddTask: () => void;
  activePlannerName: string | null;
}

export const PlannerHeader: FC<PlannerHeaderProps> = ({ 
  plannerDate, 
  setPlannerDate,
  minDate,
  onAddTask,
  activePlannerName
}) => {
  const isPast = plannerDate < todayIso();
  return (
    <div className="flex flex-col gap-4 p-6 shrink-0 bg-transparent">
      <div className="flex items-start justify-between gap-4 w-full">
        <div className="flex flex-col min-w-0">
          <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">Daily Schedule</span>
          <h2 className="text-2xl font-bold text-text truncate flex items-center gap-2">
            <span>{plannerDate === todayIso() ? "Today" : new Date(plannerDate).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</span>
            {activePlannerName && (
              <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                {activePlannerName}
              </span>
            )}
          </h2>
          <button 
            onClick={onAddTask}
            disabled={isPast}
            className={`mt-4 flex items-center justify-center gap-2 w-max px-5 py-2.5 rounded-xl font-medium shadow-sm transition-all ${isPast ? 'bg-zinc-200 text-zinc-400 cursor-not-allowed' : 'bg-primary text-white hover:bg-primary-hover hover:shadow-md hover:-translate-y-0.5 active:translate-y-0'}`}
          >
            <Plus className="w-4 h-4" />
            Add Task
          </button>
        </div>
        
        <MonthCalendar plannerDate={plannerDate} setPlannerDate={setPlannerDate} minDate={minDate} />
      </div>
    </div>
  );
};
