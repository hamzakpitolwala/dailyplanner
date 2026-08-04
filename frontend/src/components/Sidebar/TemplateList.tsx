import { type FC, useEffect, useState } from 'react';
import { Settings2 } from 'lucide-react';
import { TemplateCard } from './TemplateCard';
import { fetchTemplates } from '../../api/templateApi';
import { userApi } from '../../api/userApi';

interface TemplateListProps {
  profile: any;
  setProfile: (p: any) => void;
  setAppView: (view: string) => void;
}

export const TemplateList: FC<TemplateListProps> = ({ profile, setProfile, setAppView }) => {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchTemplates();
        setTemplates(data);
      } catch (err) {
        console.error('Failed to load templates for sidebar', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [profile?.active_planner_id]); // reload if active changes just in case

  const handleActivate = async (id: string) => {
    try {
      await userApi.updateUserProfile({ active_planner_id: id });
      setProfile({ ...profile, active_planner_id: id });
    } catch (err) {
      console.error('Failed to change active template', err);
    }
  };

  return (
    <div className="flex flex-col h-full mt-2">
      <div className="flex items-center justify-between mb-3 px-1">
        <h2 className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider">Workspaces</h2>
        <button 
          onClick={() => setAppView('templates')}
          className="text-[11px] flex items-center gap-1 text-zinc-500 hover:text-primary transition-colors font-medium px-2 py-1 rounded-md hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50"
        >
          <Settings2 className="w-3.5 h-3.5" />
          Manage
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 pb-4">
        {loading ? (
          <div className="text-sm text-zinc-400 p-2 text-center">Loading...</div>
        ) : templates.length === 0 ? (
          <div className="text-sm text-zinc-400 p-2 text-center">No workspaces found.</div>
        ) : (
          templates.map(t => (
            <TemplateCard 
              key={t.id} 
              template={t} 
              isActive={profile?.active_planner_id === t.id}
              onActivate={handleActivate}
            />
          ))
        )}
      </div>
    </div>
  );
};
