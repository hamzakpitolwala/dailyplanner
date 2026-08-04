import { type FC, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '../../components/Planner/TimelineUtils';

interface MonthCalendarProps {
  plannerDate: string;
  setPlannerDate: (date: string) => void;
}

export const MonthCalendar: FC<MonthCalendarProps> = ({ plannerDate, setPlannerDate }) => {
  const currentSelectedDate = new Date(plannerDate || new Date().toISOString().split('T')[0]);
  const [currentMonth, setCurrentMonth] = useState(new Date(currentSelectedDate.getFullYear(), currentSelectedDate.getMonth(), 1));

  const daysInMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = currentMonth.getDay();

  const days = [];
  
  // Previous month padding
  const prevMonthDays = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 0).getDate();
  for (let i = firstDayOfMonth - 1; i >= 0; i--) {
    days.push({
      dayNumber: prevMonthDays - i,
      isCurrentMonth: false,
      date: new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, prevMonthDays - i)
    });
  }

  // Current month
  for (let i = 1; i <= daysInMonth; i++) {
    days.push({
      dayNumber: i,
      isCurrentMonth: true,
      date: new Date(currentMonth.getFullYear(), currentMonth.getMonth(), i)
    });
  }

  // Next month padding
  const remainingDays = 42 - days.length; // 6 rows of 7 days
  for (let i = 1; i <= remainingDays; i++) {
    days.push({
      dayNumber: i,
      isCurrentMonth: false,
      date: new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, i)
    });
  }

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  return (
    <div className="flex flex-col bg-white rounded-xl border border-border shadow-sm p-2 w-[220px]">
      {/* Calendar Header */}
      <div className="flex items-center justify-between mb-2 px-1">
        <button onClick={handlePrevMonth} className="p-1 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-md transition-colors">
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
        <span className="text-xs font-semibold text-zinc-700">
          {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
        </span>
        <button onClick={handleNextMonth} className="p-1 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-md transition-colors">
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Days of week */}
      <div className="grid grid-cols-7 mb-1">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
          <div key={i} className="text-[9px] font-bold text-zinc-400 text-center uppercase">
            {day}
          </div>
        ))}
      </div>

      {/* Days grid */}
      <div className="grid grid-cols-7 gap-y-0.5">
        {days.map((day, idx) => {
          // Add timezone offset safety
          const pad = (n: number) => n.toString().padStart(2, '0');
          const dayIso = `${day.date.getFullYear()}-${pad(day.date.getMonth() + 1)}-${pad(day.date.getDate())}`;
          const selectedIso = `${currentSelectedDate.getFullYear()}-${pad(currentSelectedDate.getMonth() + 1)}-${pad(currentSelectedDate.getDate())}`;
          const todayIso = new Date().toISOString().split('T')[0];

          const isSelected = dayIso === selectedIso;
          const isToday = dayIso === todayIso;

          return (
            <button
              key={idx}
              onClick={() => setPlannerDate(dayIso)}
              className={cn(
                "w-7 h-7 mx-auto rounded-full flex items-center justify-center text-[11px] font-medium transition-all",
                !day.isCurrentMonth && "text-zinc-300",
                day.isCurrentMonth && !isSelected && !isToday && "text-zinc-700 hover:bg-zinc-100",
                day.isCurrentMonth && isToday && !isSelected && "text-orange-600 bg-orange-50 font-bold",
                isSelected && "bg-orange-600 text-white shadow-md shadow-orange-200"
              )}
            >
              {day.dayNumber}
            </button>
          );
        })}
      </div>
    </div>
  );
};
