import { type FC } from 'react';
import { cn } from './TimelineUtils';

interface TimelineAxisProps {
  pixelsPerMinute: number;
}

export const TimelineAxis: FC<TimelineAxisProps> = ({ pixelsPerMinute }) => {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const hourHeight = 60 * pixelsPerMinute; // 120px usually

  return (
    <div className="relative w-20 flex-shrink-0 border-r border-border bg-background">
      {hours.map((hour) => (
        <div 
          key={hour} 
          className="absolute w-full flex items-center justify-end pr-2"
          style={{ top: hour * hourHeight }}
        >
          <span className="text-xs font-medium text-slate-500 mr-2 tabular-nums">
            {hour.toString().padStart(2, '0')}:00
          </span>
          <div className="w-2 h-2 rounded-full border-2 border-slate-300 bg-white z-10 mr-[-5px]" />
        </div>
      ))}
    </div>
  );
};
