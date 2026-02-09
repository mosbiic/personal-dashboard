import { format, parseISO, isToday, isYesterday } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import type { TimelineActivity } from '../types/dashboard';

interface TimelineItemProps {
  activity: TimelineActivity;
  isLast?: boolean;
}

function formatTime(dateStr: string): string {
  const date = parseISO(dateStr);
  
  if (isToday(date)) {
    return format(date, 'HH:mm');
  } else if (isYesterday(date)) {
    return `昨天 ${format(date, 'HH:mm')}`;
  } else {
    return format(date, 'MM/dd HH:mm', { locale: zhCN });
  }
}

const sourceColors: Record<string, string> = {
  github: 'bg-purple-500/20 text-purple-400 border-purple-500/50',
  trello: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
  stock: 'bg-green-500/20 text-green-400 border-green-500/50',
  weather: 'bg-sky-500/20 text-sky-400 border-sky-500/50',
  session: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
};

export function TimelineItem({ activity, isLast = false }: TimelineItemProps) {
  const colorClass = sourceColors[activity.source_type] || 'bg-slate-500/20 text-slate-400 border-slate-500/50';
  
  return (
    <div className="relative flex gap-4 group">
      {/* Timeline line */}
      {!isLast && (
        <div className="absolute left-[19px] top-10 bottom-0 w-px bg-slate-700 group-hover:bg-slate-600 transition-colors" />
      )}
      
      {/* Icon */}
      <div className={`
        relative z-10 flex-shrink-0 w-10 h-10 rounded-full border-2 
        flex items-center justify-center text-lg
        transition-transform group-hover:scale-110
        ${colorClass}
      `}>
        {activity.icon}
      </div>
      
      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <p className="text-white font-medium text-sm">
              {activity.title}
            </p>
            {activity.description && (
              <p className="text-slate-400 text-sm mt-0.5 line-clamp-2">
                {activity.description}
              </p>
            )}
            
            {/* Metadata */}
            {activity.metadata && Object.keys(activity.metadata).length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {activity.metadata.repository && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                    📁 {activity.metadata.repository}
                  </span>
                )}
                {activity.metadata.sha && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300 font-mono">
                    {activity.metadata.sha}
                  </span>
                )}
                {activity.metadata.board && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                    📋 {activity.metadata.board}
                  </span>
                )}
              </div>
            )}
          </div>
          
          <time className="text-xs text-slate-500 flex-shrink-0">
            {formatTime(activity.occurred_at)}
          </time>
        </div>
        
        {/* Link */}
        {activity.url && (
          <a
            href={activity.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 mt-2 transition-colors"
          >
            查看详情 →
          </a>
        )}
      </div>
    </div>
  );
}
