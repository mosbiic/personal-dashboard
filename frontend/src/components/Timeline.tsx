import { format, parseISO, isToday } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { Clock, Calendar, RefreshCw, Loader2 } from 'lucide-react';
import { TimelineItem } from './TimelineItem';
import type { TimelineData } from '../types/dashboard';

interface TimelineProps {
  data?: TimelineData;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

function getTimelineTitle(start?: string): string {
  if (!start) return '活动时间轴';
  
  const startDate = parseISO(start);
  if (isToday(startDate)) {
    return '今日活动';
  }
  return '活动时间轴';
}

function formatDateRange(start?: string, end?: string): string {
  if (!start || !end) return '';
  
  const startDate = parseISO(start);
  const endDate = parseISO(end);
  
  if (isToday(startDate) && isToday(endDate)) {
    return '今天';
  }
  
  return `${format(startDate, 'MM/dd', { locale: zhCN })} - ${format(endDate, 'MM/dd', { locale: zhCN })}`;
}

export function Timeline({ data, isLoading, error, onRefresh }: TimelineProps) {
  const activities = data?.activities ?? [];
  const hasActivities = activities.length > 0;
  
  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 rounded-lg">
              <Clock className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                {getTimelineTitle(data?.start)}
              </h3>
              {data?.start && data?.end && (
                <div className="flex items-center gap-1 text-sm text-slate-400">
                  <Calendar className="w-3 h-3" />
                  <span>{formatDateRange(data.start, data.end)}</span>
                  <span className="mx-1">•</span>
                  <span>{activities.length} 条活动</span>
                </div>
              )}
            </div>
          </div>
          
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
              title="刷新"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="p-6">
        {isLoading && !hasActivities ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-400">{error}</p>
          </div>
        ) : !hasActivities ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Clock className="w-8 h-8 text-slate-500" />
            </div>
            <p className="text-slate-400">暂无活动记录</p>
            <p className="text-sm text-slate-500 mt-1">今天还没有任何活动</p>
          </div>
        ) : (
          <div className="space-y-0">
            {activities.map((activity, index) => (
              <TimelineItem
                key={activity.id}
                activity={activity}
                isLast={index === activities.length - 1}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
