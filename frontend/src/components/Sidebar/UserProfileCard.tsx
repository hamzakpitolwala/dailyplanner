import { type FC } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface UserProfileCardProps {
  profile: any;
}

export const UserProfileCard: FC<UserProfileCardProps> = ({ profile }) => {
  const { user } = useAuth();
  
  // Extract initials for avatar fallback
  const name = user?.email?.split('@')[0] || 'User';
  const initial = name.charAt(0).toUpperCase();

  return (
    <div className="bg-transparent rounded-xl p-3 flex items-center gap-4 transition-all hover:bg-sidebar-hover group cursor-pointer mb-2">
      <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-lg shrink-0 group-hover:bg-primary group-hover:text-white transition-colors shadow-sm">
        {initial}
      </div>
      <div className="flex flex-col min-w-0">
        <h3 className="text-sm font-semibold text-text truncate">
          {name}
        </h3>
        <span className="text-xs text-zinc-500 dark:text-zinc-400 truncate">
          {profile?.active_planner_id ? 'Workspace Active' : 'No Active Planner'}
        </span>
      </div>
    </div>
  );
};
