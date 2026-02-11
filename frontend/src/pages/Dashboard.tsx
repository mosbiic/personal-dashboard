import { useTranslation } from 'react-i18next';
import { LayoutDashboard, RefreshCw, Settings, Loader2 } from 'lucide-react';
import { useDashboardData, useRefreshDashboard } from '../hooks/useDashboard';
import { useDashboardStore } from '../store/useDashboardStore';
import { TrelloCard } from '../components/TrelloCard';
import { GitHubCard } from '../components/GitHubCard';
import { StockCard } from '../components/StockCard';
import { WeatherCard } from '../components/WeatherCard';
import { Timeline } from '../components/Timeline';
import { LanguageSwitcher } from '../components/LanguageSwitcher';

export function Dashboard() {
  const { t, i18n } = useTranslation();
  const { summary, timeline, isLoading } = useDashboardData();
  const { refresh } = useRefreshDashboard();
  const { autoRefresh, setAutoRefresh, errors } = useDashboardStore();
  
  // Get current time display based on language
  const currentTime = new Date().toLocaleString(i18n.language === 'zh' ? 'zh-CN' : 'en-US', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
    hour: '2-digit',
    minute: '2-digit',
  });
  
  const handleRefresh = async () => {
    await refresh();
  };
  
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-500/20 rounded-lg">
                <LayoutDashboard className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">{t('app.title')}</h1>
                <p className="text-xs text-slate-400">{currentTime}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Language Switcher */}
              <LanguageSwitcher />
              
              {/* Auto refresh toggle */}
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors
                  ${autoRefresh 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-slate-700 text-slate-400'}
                `}
                title={autoRefresh ? t('header.autoRefreshOnTooltip') : t('header.autoRefreshOffTooltip')}
              >
                <div className={`w-2 h-2 rounded-full ${autoRefresh ? 'bg-green-400 animate-pulse' : 'bg-slate-500'}`} />
                <span className="hidden sm:inline">{autoRefresh ? t('header.autoRefreshOn') : t('header.autoRefreshOff')}</span>
              </button>
              
              {/* Refresh button */}
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                <span className="hidden sm:inline">{t('header.refresh')}</span>
              </button>
              
              {/* Settings placeholder */}
              <button
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                title={t('header.settings')}
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Data Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <TrelloCard 
            data={summary?.trello}
            isLoading={isLoading}
            error={errors.trello}
          />
          <GitHubCard 
            data={summary?.github}
            isLoading={isLoading}
            error={errors.github}
          />
          <StockCard 
            data={summary?.stocks ? {
              summary: {
                total_cost: summary.stocks.total_value || 0,
                total_value: summary.stocks.total_value || 0,
                total_pnl: summary.stocks.total_pnl,
                total_pnl_pct: summary.stocks.daily_change,
                holdings_count: 0,
              },
              holdings: [],
            } : undefined}
            isLoading={isLoading}
            error={errors.stocks}
          />
          <WeatherCard 
            data={summary?.weather ? {
              current: {
                temperature: summary.weather.temp,
                feels_like: summary.weather.feels_like || summary.weather.temp,
                humidity: summary.weather.humidity || 0,
                description: summary.weather.condition,
                icon: summary.weather.icon || '🌡️',
              },
            } : undefined}
            isLoading={isLoading}
            error={errors.weather}
          />
        </div>
        
        {/* Timeline Section */}
        <Timeline 
          data={timeline}
          isLoading={isLoading}
          error={errors.timeline}
          onRefresh={handleRefresh}
        />
        
        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-slate-500">
          <p>{t('app.footer')}</p>
        </footer>
      </main>
    </div>
  );
}
