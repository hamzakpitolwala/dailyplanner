import { type FC } from 'react';
import { LayoutDashboard } from 'lucide-react';

export const DashboardPage: FC = () => {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-8 bg-zinc-50/50 dark:bg-zinc-900/50">
      <div className="flex flex-col items-center text-center max-w-md">
        <div className="w-16 h-16 bg-orange-100 text-orange-600 rounded-2xl flex items-center justify-center mb-6 shadow-sm border border-orange-200">
          <LayoutDashboard className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-bold text-zinc-800 tracking-tight mb-3">Dashboard</h2>
        <p className="text-zinc-500 text-lg">
          Detailed analytics and insights are coming soon. Stay tuned!
        </p>
      </div>
    </div>
  );
};
