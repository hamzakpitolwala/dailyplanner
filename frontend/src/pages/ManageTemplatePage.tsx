import { type FC } from 'react';
import { TemplateManager } from '../components/templates/TemplateManager';
import { FixedBlockManager } from '../components/templates/FixedBlockManager';

interface ManageTemplatePageProps {
  activeView: string;
  setAppView: (view: string) => void;
  profile: any;
  setProfile: (p: any) => void;
  setMessage: (m: string) => void;
}

export const ManageTemplatePage: FC<ManageTemplatePageProps> = ({ activeView, setAppView, profile, setProfile, setMessage }) => {
  return (
    <div className="flex flex-col gap-6 p-6 h-full overflow-y-auto bg-transparent relative z-10">
      <div className="max-w-4xl w-full mx-auto space-y-8">
        <div className="flex items-center gap-4 mb-4">
          <button 
            onClick={() => setAppView(activeView)}
            className="px-4 py-2 text-sm font-medium text-zinc-600 dark:text-zinc-300 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors shadow-sm"
          >
            &larr; Back to {activeView === 'planner' ? 'Planner' : 'Dashboard'}
          </button>
          <h2 className="text-3xl font-bold text-zinc-800 dark:text-white flex items-center gap-3">
            Template Settings
          </h2>
        </div>
        
        <TemplateManager setMessage={setMessage} profile={profile} setProfile={setProfile} setAppView={setAppView} />
        <FixedBlockManager setMessage={setMessage} />
      </div>
    </div>
  );
};
