import { type FC, useEffect, useState } from 'react';
import { cn, PIXELS_PER_MINUTE } from './TimelineUtils';

interface TimelineAxisProps {
  pixelsPerMinute?: number;
}

export const TimelineAxis: FC<TimelineAxisProps> = ({ pixelsPerMinute = PIXELS_PER_MINUTE }) => {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const hourHeight = 60 * pixelsPerMinute; // 120px usually

  const [currentHour, setCurrentHour] = useState(new Date().getHours());

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentHour(new Date().getHours());
    }, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-20 flex-shrink-0 border-r border-border bg-background">
      {hours.map((hour) => (
        <div 
          key={hour} 
          className="absolute w-full flex items-center justify-end pr-2"
          style={{ top: hour * hourHeight }}
        >
          <span className="text-xs font-medium text-zinc-500 mr-2 tabular-nums">
            {hour.toString().padStart(2, '0')}:00
          </span>
          <div 
            className={cn(
              "w-2 h-2 rounded-full border-2 z-10 mr-[-5px] transition-colors duration-300",
              hour === currentHour 
                ? "border-orange-500 bg-orange-500 animate-pulse shadow-[0_0_8px_rgba(249,115,22,0.8)]" 
                : "border-zinc-300 bg-white dark:border-zinc-600 dark:bg-zinc-800"
            )} 
          />
        </div>
      ))}
    </div>
  );
};

