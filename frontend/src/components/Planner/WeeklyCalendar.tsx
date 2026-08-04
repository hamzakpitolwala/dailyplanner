import { type FC } from 'react';
import { cn } from '../../components/Planner/TimelineUtils'; 

interface WeeklyCalendarProps {
  plannerDate: string;
  setPlannerDate: (date: string) => void;
}

export const WeeklyCalendar: FC<WeeklyCalendarProps> = ({ plannerDate, setPlannerDate }) => {
  // Generate days for the week based on current plannerDate
  const current = new Date(plannerDate || new Date().toISOString().split('T')[0]);
  
  // Find Sunday of this week
  const startOfWeek = new Date(current);
  startOfWeek.setDate(current.getDate() - current.getDay());

  const days = Array.from({ length: 7 }).map((_, i) => {
    const d = new Date(startOfWeek);
    d.setDate(startOfWeek.getDate() + i);
    return {
      date: d,
      iso: d.toISOString().split('T')[0],
      dayName: ['S', 'M', 'T', 'W', 'T', 'F', 'S'][d.getDay()],
      dayNumber: d.getDate(),
      isCurrent: d.toISOString().split('T')[0] === (plannerDate || new Date().toISOString().split('T')[0])
    };
  });

  return (
    <div className="flex flex-col bg-white rounded-xl border border-border shadow-sm p-3 w-max">
      <div className="flex gap-1">
        {days.map((day) => (
          <div key={day.iso} className="flex flex-col items-center gap-1 w-8">
            <span className="text-[10px] font-semibold text-zinc-400">{day.dayName}</span>
            <button
              onClick={() => setPlannerDate(day.iso)}
              className={cn(
                "w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-all",
                day.isCurrent 
                  ? "bg-orange-600 text-white shadow-md shadow-orange-200" 
                  : "text-zinc-700 hover:bg-zinc-100"
              )}
            >
              {day.dayNumber}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
