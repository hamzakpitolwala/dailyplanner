import { type FC } from 'react';
import { CheckCircle2, ChevronRight, LayoutTemplate } from 'lucide-react';
import { cn } from '../../components/Planner/TimelineUtils'; 

interface TemplateCardProps {
  template: any;
  isActive: boolean;
  onActivate: (id: string) => void;
}

export const TemplateCard: FC<TemplateCardProps> = ({ template, isActive, onActivate }) => {
  return (
    <button
      onClick={() => onActivate(template.id)}
      className={cn(
        "w-full text-left p-2.5 rounded-lg border transition-all duration-200 group flex items-center justify-between outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
        isActive 
          ? "bg-white dark:bg-card border-border shadow-sm ring-1 ring-primary/20" 
          : "bg-transparent border-transparent hover:bg-white/50 dark:hover:bg-zinc-800/50 hover:border-border/50"
      )}
    >
      <div className="flex items-center gap-3 min-w-0">
        <div className={cn(
          "w-7 h-7 rounded-md flex items-center justify-center shrink-0 transition-colors",
          isActive ? "bg-primary/10 text-primary" : "bg-zinc-200/50 dark:bg-zinc-700/50 text-zinc-500 group-hover:text-primary"
        )}>
          <LayoutTemplate className="w-4 h-4" />
        </div>
        <div className="flex flex-col min-w-0">
          <span className={cn(
            "text-sm font-medium truncate",
            isActive ? "text-text" : "text-zinc-600 dark:text-zinc-400 group-hover:text-text"
          )}>
            {template.name}
          </span>
          <span className="text-[11px] text-zinc-500 dark:text-zinc-500">
            {template.template_tasks?.length || 0} tasks
          </span>
        </div>
      </div>
      
      {isActive ? (
        <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
      ) : (
        <ChevronRight className="w-4 h-4 text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
      )}
    </button>
  );
};
