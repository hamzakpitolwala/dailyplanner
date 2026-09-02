import { type FC, type ReactNode, useState } from 'react';
import { TopNavbar } from '../Navigation/TopNavbar';
import { UserProfileCard } from '../Sidebar/UserProfileCard';
import { TemplateList } from '../Sidebar/TemplateList';
import { PlannerAIPanel } from '../PlannerAI/PlannerAIPanel';
import { useAuth } from '../../contexts/AuthContext';
import { LogOut, Bot, ChevronRight, ChevronLeft, Menu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MainLayoutProps {
  children: ReactNode;
  activeView: 'planner' | 'dashboard' | 'history';
  setActiveView: (view: 'planner' | 'dashboard' | 'history') => void;
  profile: any;
  setProfile: (p: any) => void;
  setAppView: (view: string) => void;
}

export const MainLayout: FC<MainLayoutProps> = ({ 
  children, 
  activeView, 
  setActiveView,
  profile,
  setProfile,
  setAppView
}) => {
  const { logout } = useAuth();
  const [isAiOpen, setIsAiOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="h-screen w-full bg-transparent flex flex-col overflow-hidden text-text transition-colors duration-300">
      <TopNavbar activeView={activeView} setActiveView={setActiveView} />
      
      <div className="flex-1 w-full max-w-[1920px] mx-auto flex overflow-hidden relative">
        
        {/* Left Planner AI Panel (Collapsible) */}
        <AnimatePresence initial={false}>
          {isAiOpen && (
            <motion.aside 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 360, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: "spring", bounce: 0, duration: 0.4 }}
              className="shrink-0 border-r border-border bg-zinc-50/50 dark:bg-zinc-900/50 h-full flex flex-col relative z-20 shadow-[10px_0_20px_-5px_rgba(0,0,0,0.05)]"
            >
              <div className="absolute top-4 -right-4 z-30">
                <button
                  onClick={() => setIsAiOpen(false)}
                  className="bg-card border border-border rounded-full p-1.5 shadow-md hover:bg-sidebar-hover text-text transition-colors"
                  aria-label="Close AI Assistant"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              </div>
              <div className="h-full overflow-hidden w-[360px]">
                <PlannerAIPanel />
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Floating AI Button (Visible when closed) */}
        <AnimatePresence>
          {!isAiOpen && (
            <motion.button
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsAiOpen(true)}
              className="absolute bottom-6 left-6 z-30 flex items-center justify-center p-4 bg-primary text-white rounded-2xl shadow-lg hover:bg-primary-hover hover:shadow-xl transition-all"
              aria-label="Open AI Assistant"
            >
              <Bot className="w-6 h-6" />
            </motion.button>
          )}
        </AnimatePresence>

        {/* Center Workspace */}
        <main className="flex-1 flex flex-col h-full overflow-hidden bg-transparent relative z-10 shadow-[0_0_15px_-3px_rgba(0,0,0,0.02)]">
          {children}
        </main>

        {/* Right Sidebar (Collapsible) */}
        <AnimatePresence initial={false}>
          {isSidebarOpen && (
            <motion.aside 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: "spring", bounce: 0, duration: 0.4 }}
              className="shrink-0 border-l border-border bg-zinc-50/50 dark:bg-zinc-900/50 h-full flex flex-col relative z-20 shadow-[-10px_0_20px_-5px_rgba(0,0,0,0.05)]"
            >
              <div className="absolute top-4 -left-4 z-30">
                <button
                  onClick={() => setIsSidebarOpen(false)}
                  className="bg-card border border-border rounded-full p-1.5 shadow-md hover:bg-sidebar-hover text-text transition-colors"
                  aria-label="Close Sidebar"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              
              <div className="h-full overflow-y-auto w-[320px] p-4 flex flex-col">
                {profile && <UserProfileCard profile={profile} setAppView={setAppView} />}
                <div className="mt-6 flex-1 flex flex-col">
                  <TemplateList profile={profile} setProfile={setProfile} setAppView={setAppView} />
                </div>
                <button 
                  onClick={logout}
                  className="mt-6 flex items-center justify-center gap-2 w-full py-3 px-4 bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 rounded-xl transition-colors font-medium shadow-sm border border-red-100 dark:border-red-900/50 hover:shadow"
                >
                  <LogOut className="w-5 h-5" />
                  Sign Out
                </button>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
        
        {/* Floating Sidebar Open Button (Visible when closed) */}
        <AnimatePresence>
          {!isSidebarOpen && (
            <motion.button
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsSidebarOpen(true)}
              className="absolute top-4 right-0 z-30 flex items-center justify-center p-1.5 bg-card border border-border rounded-l-md shadow-md hover:bg-sidebar-hover text-text transition-colors"
              aria-label="Open Sidebar"
            >
              <ChevronLeft className="w-4 h-4" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
