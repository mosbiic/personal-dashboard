import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useDashboardStore } from '../store/useDashboardStore';
import {
  dashboardApi,
  timelineApi,
  trelloApi,
  githubApi,
  stockApi,
  weatherApi,
} from '../api/config';

// Query keys
export const queryKeys = {
  summary: ['dashboard', 'summary'] as const,
  timeline: ['timeline'] as const,
  todayTimeline: ['timeline', 'today'] as const,
  trelloStats: ['trello', 'stats'] as const,
  githubStats: ['github', 'stats'] as const,
  portfolio: ['stocks', 'portfolio'] as const,
  weather: ['weather', 'current'] as const,
};

// Dashboard Summary Hook
export function useDashboardSummary() {
  const { setSummary, setLoading, setError, autoRefresh, refreshInterval } = useDashboardStore();
  
  const query = useQuery({
    queryKey: queryKeys.summary,
    queryFn: async () => {
      setLoading('summary', true);
      setError('summary', null);
      try {
        const response = await dashboardApi.getSummary();
        const data = response.data;
        setSummary(data);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch summary';
        setError('summary', message);
        throw error;
      } finally {
        setLoading('summary', false);
      }
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
    staleTime: 30000, // 30秒
  });
  
  return query;
}

// Timeline Hook
export function useTimeline(options?: { start?: string; end?: string; limit?: number }) {
  const { setTimeline, setLoading, setError } = useDashboardStore();
  
  return useQuery({
    queryKey: [...queryKeys.timeline, options],
    queryFn: async () => {
      setLoading('timeline', true);
      setError('timeline', null);
      try {
        const response = await timelineApi.getTimeline(options);
        const data = response.data;
        setTimeline(data);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch timeline';
        setError('timeline', message);
        throw error;
      } finally {
        setLoading('timeline', false);
      }
    },
    staleTime: 60000,
  });
}

// Today Timeline Hook
export function useTodayTimeline() {
  const { setTimeline, setLoading, setError, autoRefresh, refreshInterval } = useDashboardStore();
  
  return useQuery({
    queryKey: queryKeys.todayTimeline,
    queryFn: async () => {
      setLoading('timeline', true);
      setError('timeline', null);
      try {
        const response = await timelineApi.getToday();
        const data = response.data;
        setTimeline(data);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch today timeline';
        setError('timeline', message);
        throw error;
      } finally {
        setLoading('timeline', false);
      }
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
    staleTime: 30000,
  });
}

// Trello Stats Hook
export function useTrelloStats(days: number = 7) {
  const { setTrelloStats, setLoading, setError } = useDashboardStore();
  
  return useQuery({
    queryKey: [...queryKeys.trelloStats, days],
    queryFn: async () => {
      setLoading('trello', true);
      setError('trello', null);
      try {
        const response = await trelloApi.getStats(days);
        const data = response.data;
        setTrelloStats(data);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch Trello stats';
        setError('trello', message);
        throw error;
      } finally {
        setLoading('trello', false);
      }
    },
    staleTime: 60000,
  });
}

// GitHub Stats Hook
export function useGithubStats(days: number = 7) {
  const { setGithubStats, setLoading, setError } = useDashboardStore();
  
  return useQuery({
    queryKey: [...queryKeys.githubStats, days],
    queryFn: async () => {
      setLoading('github', true);
      setError('github', null);
      try {
        const response = await githubApi.getStats(days);
        const data = response.data;
        setGithubStats(data);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch GitHub stats';
        setError('github', message);
        throw error;
      } finally {
        setLoading('github', false);
      }
    },
    staleTime: 60000,
  });
}

// Portfolio Hook
export function usePortfolio() {
  const { setPortfolio, setLoading, setError, autoRefresh, refreshInterval } = useDashboardStore();
  
  return useQuery({
    queryKey: queryKeys.portfolio,
    queryFn: async () => {
      setLoading('stocks', true);
      setError('stocks', null);
      try {
        const response = await stockApi.getPortfolio();
        const data = response.data.data;
        setPortfolio(data);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch portfolio';
        setError('stocks', message);
        throw error;
      } finally {
        setLoading('stocks', false);
      }
    },
    refetchInterval: autoRefresh ? refreshInterval * 2 : false, // 股票刷新间隔更长
    staleTime: 60000,
  });
}

// Weather Hook
export function useWeather() {
  const { setWeather, setLoading, setError, autoRefresh, refreshInterval } = useDashboardStore();
  
  return useQuery({
    queryKey: queryKeys.weather,
    queryFn: async () => {
      setLoading('weather', true);
      setError('weather', null);
      try {
        const response = await weatherApi.getCurrent();
        const data = response.data.data;
        setWeather(data);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch weather';
        setError('weather', message);
        throw error;
      } finally {
        setLoading('weather', false);
      }
    },
    refetchInterval: autoRefresh ? refreshInterval * 5 : false, // 天气刷新间隔更长
    staleTime: 300000, // 5分钟
  });
}

// 手动刷新 Hook
export function useRefreshDashboard() {
  const queryClient = useQueryClient();
  
  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.summary }),
      queryClient.invalidateQueries({ queryKey: queryKeys.todayTimeline }),
      queryClient.invalidateQueries({ queryKey: queryKeys.portfolio }),
      queryClient.invalidateQueries({ queryKey: queryKeys.weather }),
    ]);
  };
  
  return { refresh };
}

// 组合 Hook - 获取所有仪表板数据
export function useDashboardData() {
  const summary = useDashboardSummary();
  const timeline = useTodayTimeline();
  const portfolio = usePortfolio();
  const weather = useWeather();
  
  const isLoading = summary.isLoading || timeline.isLoading || portfolio.isLoading || weather.isLoading;
  const isError = summary.isError || timeline.isError || portfolio.isError || weather.isError;
  
  return {
    summary: summary.data,
    timeline: timeline.data,
    portfolio: portfolio.data,
    weather: weather.data,
    isLoading,
    isError,
    refetch: () => {
      summary.refetch();
      timeline.refetch();
      portfolio.refetch();
      weather.refetch();
    },
  };
}
