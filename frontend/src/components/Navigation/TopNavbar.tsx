import { type FC } from 'react';
import { motion } from 'framer-motion';
import { LayoutDashboard, Calendar, Columns3, Search } from 'lucide-react';
import { cn } from '../../components/Planner/TimelineUtils'; 
import { ThemeToggle } from '../ThemeToggle';

interface TopNavbarProps {
  activeView: 'planner' | 'dashboard';
  setActiveView: (view: 'planner' | 'dashboard') => void;
}

export const TopNavbar: FC<TopNavbarProps> = ({ activeView, setActiveView }) => {
  const tabs = [
    { id: 'dailyplanner', label: 'DailyPlanner', icon: <Columns3 className="w-5 h-5 text-primary" />, disabled: true },
    { id: 'planner', label: 'Planner', icon: <Calendar className="w-5 h-5" />, disabled: false },
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, disabled: false }
  ];

  return (
    <header className="h-[60px] w-full bg-card/80 backdrop-blur-md border-b border-border shrink-0 flex items-center justify-between px-6 sticky top-0 z-50">
      <div className="flex items-center gap-2 h-full">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && tab.id !== 'dailyplanner' && setActiveView(tab.id as 'planner' | 'dashboard')}
            className={cn(
              "relative px-4 py-2 rounded-xl flex items-center gap-2 transition-all font-medium text-sm h-10",
              tab.disabled && tab.id === 'dailyplanner' ? "text-text font-bold text-lg cursor-default mr-6 p-0" : 
              activeView === tab.id ? "text-primary bg-primary/10" : "text-zinc-500 hover:text-text hover:bg-zinc-100 dark:hover:bg-zinc-800",
              tab.disabled && tab.id !== 'dailyplanner' && "opacity-50 cursor-not-allowed"
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>
      
      <div className="flex items-center gap-4">
        {/* Search Placeholder */}
        <div className="relative group hidden md:block">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-primary transition-colors" />
          <input 
            type="text" 
            placeholder="Search tasks, templates..." 
            className="w-64 h-9 pl-9 pr-4 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-text placeholder:text-zinc-400"
          />
        </div>
        
        <div className="h-6 w-px bg-border mx-2"></div>
        
        <ThemeToggle />
      </div>
    </header>
  );
};
