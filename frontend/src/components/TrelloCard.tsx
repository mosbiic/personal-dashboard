import { CheckCircle2, Circle, ListTodo, Loader2 } from 'lucide-react';
import type { TrelloSummary } from '../types/dashboard';

interface TrelloCardProps {
  data?: TrelloSummary;
  isLoading?: boolean;
  error?: string | null;
}

export function TrelloCard({ data, isLoading, error }: TrelloCardProps) {
  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ListTodo className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">Trello 任务</h3>
          </div>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-red-700/50 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <ListTodo className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Trello 任务</h3>
        </div>
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    );
  }

  const completed = data?.completed_today ?? 0;
  const pending = data?.pending ?? 0;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg hover:border-blue-500/50 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <ListTodo className="w-5 h-5 text-blue-400" />
          </div>
          <h3 className="text-lg font-semibold text-white">Trello 任务</h3>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
            <span className="text-sm text-slate-400">今日完成</span>
          </div>
          <p className="text-2xl font-bold text-white">{completed}</p>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Circle className="w-4 h-4 text-amber-400" />
            <span className="text-sm text-slate-400">待办</span>
          </div>
          <p className="text-2xl font-bold text-white">{pending}</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">完成率</span>
          <span className="text-white font-medium">
            {completed + pending > 0 ? Math.round((completed / (completed + pending)) * 100) : 0}%
          </span>
        </div>
        <div className="mt-2 h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-500"
            style={{
              width: `${completed + pending > 0 ? (completed / (completed + pending)) * 100 : 0}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
