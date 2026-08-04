import { type FC } from 'react';
import { Sparkles } from 'lucide-react';
import { ChatInput } from './ChatInput';

export const PlannerAIPanel: FC = () => {
  return (
    <div className="flex flex-col h-full bg-transparent w-full">
      {/* Header */}
      <div className="h-[72px] shrink-0 border-b border-border flex items-center px-6">
        <div className="flex items-center gap-2 text-zinc-800 font-semibold">
          <Sparkles className="w-5 h-5 text-orange-500" />
          Planner AI
        </div>
      </div>

      {/* Empty State Body */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center overflow-y-auto">
        <div className="text-4xl mb-4">👋</div>
        <h3 className="text-lg font-medium text-zinc-800 mb-2">Ask Planner AI anything.</h3>
        
        <ul className="text-sm text-zinc-500 space-y-3 mt-4 text-left">
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400"></span>
            Create a schedule
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400"></span>
            Rearrange tasks
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400"></span>
            Improve productivity
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-400"></span>
            Plan your day
          </li>
        </ul>
      </div>

      {/* Input */}
      <ChatInput />
    </div>
  );
};
