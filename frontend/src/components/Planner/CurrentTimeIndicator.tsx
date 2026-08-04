import { useState, useEffect, type FC } from 'react';
import { motion } from 'framer-motion';

interface CurrentTimeIndicatorProps {
  pixelsPerMinute: number;
}

export const CurrentTimeIndicator: FC<CurrentTimeIndicatorProps> = ({ pixelsPerMinute }) => {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(interval);
  }, []);

  const minutes = now.getHours() * 60 + now.getMinutes();
  const top = minutes * pixelsPerMinute;

  return (
    <div 
      className="absolute left-0 right-0 z-20 flex items-center pointer-events-none"
      style={{ top }}
    >
      <div className="w-20 pr-2 flex items-center justify-end">
        <span className="text-xs font-bold text-orange-500 mr-2 bg-background px-1 rounded">
          {now.getHours().toString().padStart(2, '0')}:{now.getMinutes().toString().padStart(2, '0')}
        </span>
        <motion.div 
          animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-3 h-3 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(59,130,246,0.8)] mr-[-6.5px]" 
        />
      </div>
      <div className="flex-1 h-[2px] bg-orange-500/50 shadow-[0_0_4px_rgba(59,130,246,0.5)]" />
    </div>
  );
};
