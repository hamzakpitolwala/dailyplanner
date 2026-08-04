import { type FC } from 'react';
import { Send } from 'lucide-react';

export const ChatInput: FC = () => {
  return (
    <div className="p-4 bg-transparent mt-auto relative shrink-0">
      <div className="relative flex items-center bg-white shadow-sm border border-zinc-200 rounded-full focus-within:ring-2 focus-within:ring-orange-100 focus-within:border-orange-300 transition-all">
        <input 
          type="text" 
          placeholder="Ask Planner AI..."
          className="w-full bg-transparent border-none focus:outline-none focus:ring-0 py-3 pl-5 pr-12 text-sm text-zinc-700 placeholder-zinc-400"
          disabled
        />
        <button 
          className="absolute right-2 w-8 h-8 flex items-center justify-center bg-orange-600 text-white rounded-full hover:bg-orange-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          disabled
        >
          <Send className="w-4 h-4 ml-0.5" />
        </button>
      </div>
    </div>
  );
};
