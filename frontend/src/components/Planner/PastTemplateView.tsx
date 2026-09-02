import { type FC } from 'react';
import { PastTaskCard } from './PastTaskCard';

interface Task {
  id: string;
  title: string;
  description?: string;
  start_time?: string;
  due_date?: string;
  status: string;
  subtasks?: any[];
  checkins?: any[];
  source_template_id?: string;
  source_template_task_id?: string;
}

interface PastTemplateViewProps {
  tasks: Task[];
  templates: any[];
  onDelete?: (id: string) => void;
}

export const PastTemplateView: FC<PastTemplateViewProps> = ({ tasks, templates, onDelete }) => {
  // Group tasks by template ID
  const groupedTasks: Record<string, { templateTasks: Task[], manualTasks: Task[] }> = {};
  const globalManualTasks: Task[] = [];

  tasks.forEach(task => {
    if (task.source_template_id) {
      if (!groupedTasks[task.source_template_id]) {
        groupedTasks[task.source_template_id] = { templateTasks: [], manualTasks: [] };
      }
      if (task.source_template_task_id) {
        groupedTasks[task.source_template_id].templateTasks.push(task);
      } else {
        groupedTasks[task.source_template_id].manualTasks.push(task);
      }
    } else {
      globalManualTasks.push(task);
    }
  });

  const templateIds = Object.keys(groupedTasks);

  return (
    <div className="w-full h-full overflow-y-auto bg-zinc-50/50 p-6 flex flex-col gap-8">
      {templateIds.map(templateId => {
        const { templateTasks, manualTasks } = groupedTasks[templateId];
        
        // Find the template name from the passed templates list
        const templateObj = templates.find(t => t.id === templateId);
        const templateName = templateObj ? templateObj.name : 'Unknown Template';
        
        // Sort time-wise
        const sortByTime = (a: Task, b: Task) => {
          const timeA = a.start_time ? new Date(a.start_time).getTime() : 0;
          const timeB = b.start_time ? new Date(b.start_time).getTime() : 0;
          return timeA - timeB;
        };

        templateTasks.sort(sortByTime);
        manualTasks.sort(sortByTime);

        return (
          <div key={templateId} className="flex flex-col gap-4">
            <h2 className="text-xl font-bold text-zinc-800 border-b border-zinc-200 pb-2">{templateName}</h2>
            
            {templateTasks.length > 0 && (
              <div className="flex flex-col gap-3">
                {templateTasks.map(t => <PastTaskCard key={t.id} task={t} onDelete={onDelete} />)}
              </div>
            )}

            {manualTasks.length > 0 && (
              <div className="flex flex-col gap-3 mt-2 pl-4 border-l-2 border-zinc-200">
                <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider mb-1">Manual Tasks</h3>
                {manualTasks.map(t => <PastTaskCard key={t.id} task={t} onDelete={onDelete} />)}
              </div>
            )}
          </div>
        );
      })}

      {globalManualTasks.length > 0 && (
        <div className="flex flex-col gap-4">
          <h2 className="text-xl font-bold text-zinc-800 border-b border-zinc-200 pb-2">Other Manual Tasks</h2>
          <div className="flex flex-col gap-3">
            {globalManualTasks
              .sort((a, b) => {
                const timeA = a.start_time ? new Date(a.start_time).getTime() : 0;
                const timeB = b.start_time ? new Date(b.start_time).getTime() : 0;
                return timeA - timeB;
              })
              .map(t => <PastTaskCard key={t.id} task={t} onDelete={onDelete} />)}
          </div>
        </div>
      )}

      {tasks.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-zinc-500 py-20">
          <p className="text-lg font-medium">No tasks found for this date.</p>
        </div>
      )}
    </div>
  );
};
