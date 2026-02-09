import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  DashboardSummary,
  TimelineData,
  TrelloStats,
  GitHubStats,
  PortfolioData,
  WeatherData,
} from '../types/dashboard';

interface DashboardState {
  // 数据状态
  summary: DashboardSummary | null;
  timeline: TimelineData | null;
  trelloStats: TrelloStats | null;
  githubStats: GitHubStats | null;
  portfolio: PortfolioData | null;
  weather: WeatherData | null;
  
  // 加载状态
  isLoading: {
    summary: boolean;
    timeline: boolean;
    trello: boolean;
    github: boolean;
    stocks: boolean;
    weather: boolean;
  };
  
  // 错误状态
  errors: {
    summary: string | null;
    timeline: string | null;
    trello: string | null;
    github: string | null;
    stocks: string | null;
    weather: string | null;
  };
  
  // 自动刷新设置
  autoRefresh: boolean;
  refreshInterval: number;
  
  // Actions
  setSummary: (data: DashboardSummary) => void;
  setTimeline: (data: TimelineData) => void;
  setTrelloStats: (data: TrelloStats) => void;
  setGithubStats: (data: GitHubStats) => void;
  setPortfolio: (data: PortfolioData) => void;
  setWeather: (data: WeatherData) => void;
  
  setLoading: (key: keyof DashboardState['isLoading'], value: boolean) => void;
  setError: (key: keyof DashboardState['errors'], value: string | null) => void;
  
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (interval: number) => void;
  
  // 重置状态
  reset: () => void;
}

const initialState = {
  summary: null,
  timeline: null,
  trelloStats: null,
  githubStats: null,
  portfolio: null,
  weather: null,
  
  isLoading: {
    summary: false,
    timeline: false,
    trello: false,
    github: false,
    stocks: false,
    weather: false,
  },
  
  errors: {
    summary: null,
    timeline: null,
    trello: null,
    github: null,
    stocks: null,
    weather: null,
  },
  
  autoRefresh: true,
  refreshInterval: 60000, // 60秒
};

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set) => ({
      ...initialState,
      
      setSummary: (data) => set({ summary: data }),
      setTimeline: (data) => set({ timeline: data }),
      setTrelloStats: (data) => set({ trelloStats: data }),
      setGithubStats: (data) => set({ githubStats: data }),
      setPortfolio: (data) => set({ portfolio: data }),
      setWeather: (data) => set({ weather: data }),
      
      setLoading: (key, value) => 
        set((state) => ({
          isLoading: { ...state.isLoading, [key]: value }
        })),
      
      setError: (key, value) => 
        set((state) => ({
          errors: { ...state.errors, [key]: value }
        })),
      
      setAutoRefresh: (enabled) => set({ autoRefresh: enabled }),
      setRefreshInterval: (interval) => set({ refreshInterval: interval }),
      
      reset: () => set(initialState),
    }),
    { name: 'dashboard-store' }
  )
);
