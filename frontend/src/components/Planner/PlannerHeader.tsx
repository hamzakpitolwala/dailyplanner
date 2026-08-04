import { type FC } from 'react';
import { Plus } from 'lucide-react';
import { MonthCalendar } from './MonthCalendar';

interface PlannerHeaderProps {
  plannerDate: string;
  setPlannerDate: (date: string) => void;
  onAddTask: () => void;
  activePlannerName: string | null;
}

export const PlannerHeader: FC<PlannerHeaderProps> = ({ 
  plannerDate, 
  setPlannerDate, 
  onAddTask,
  activePlannerName
}) => {
  return (
    <div className="flex flex-col gap-4 p-6 shrink-0 bg-transparent">
      <div className="flex items-start justify-between gap-4 w-full">
        <div className="flex flex-col min-w-0">
          <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">Active Template</span>
          <h2 className="text-2xl font-bold text-text truncate">
            {activePlannerName || 'No active template'}
          </h2>
          <button 
            onClick={onAddTask}
            className="mt-4 flex items-center justify-center gap-2 w-max px-5 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-hover transition-all font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0"
          >
            <Plus className="w-4 h-4" />
            Add Task
          </button>
        </div>
        
        <MonthCalendar plannerDate={plannerDate} setPlannerDate={setPlannerDate} />
      </div>
    </div>
  );
};
