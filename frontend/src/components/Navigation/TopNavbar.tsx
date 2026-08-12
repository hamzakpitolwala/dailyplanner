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
    { id: 'dailyplanner', label: 'DailyPlanner', icon: <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 shadow-[0_4px_12px_rgba(249,115,22,0.4)] border border-orange-300/30 overflow-hidden relative group-hover:shadow-[0_4px_16px_rgba(249,115,22,0.6)] transition-all duration-300"><div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div><img src="/logo.png" alt="DailyPlanner Logo" className="w-7 h-7 object-contain drop-shadow-md z-10 transform group-hover:scale-105 transition-transform duration-300 relative" /></div>, disabled: false },
    { id: 'planner', label: 'Planner', icon: <Calendar className="w-5 h-5" />, disabled: false },
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, disabled: false }
  ];

  return (
    <header className="h-[60px] w-full bg-card/80 backdrop-blur-md border-b border-border shrink-0 flex items-center justify-between px-6 sticky top-0 z-50">
      <div className="flex items-center gap-2 h-full">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              if (tab.disabled) return;
              if (tab.id === 'dailyplanner') {
                setActiveView('planner');
              } else {
                setActiveView(tab.id as 'planner' | 'dashboard');
              }
            }}
            className={cn(
              "relative px-4 py-2 rounded-xl flex items-center gap-2 transition-all font-medium text-sm h-10",
              tab.id === 'dailyplanner' ? "text-text font-bold text-lg mr-6 p-0 hover:opacity-90 group" :
                activeView === tab.id ? "text-primary bg-primary/10" : "text-zinc-500 hover:text-text hover:bg-zinc-100 dark:hover:bg-zinc-800",
              tab.disabled && "opacity-50 cursor-not-allowed"
            )}
          >
            {tab.icon}
            {tab.id === 'dailyplanner' ? (
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-orange-400 via-orange-500 to-orange-600">
                {tab.label}
              </span>
            ) : (
              tab.label
            )}
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
