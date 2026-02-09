import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:18000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// 请求拦截器 - 添加认证 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('dashboard_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 未授权，清除 token
      localStorage.removeItem('dashboard_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Dashboard API
export const dashboardApi = {
  getSummary: () => api.get('/api/dashboard/summary'),
  getCorrelations: (days: number = 7) => 
    api.get(`/api/dashboard/correlations?days=${days}`),
};

// Timeline API
export const timelineApi = {
  getTimeline: (params?: { start?: string; end?: string; sources?: string; limit?: number }) =>
    api.get('/api/timeline/', { params }),
  getToday: () => api.get('/api/timeline/today'),
  getWeek: () => api.get('/api/timeline/week'),
  getMonth: () => api.get('/api/timeline/month'),
  refresh: () => api.post('/api/timeline/refresh'),
};

// Trello API
export const trelloApi = {
  getBoards: () => api.get('/api/trello/boards'),
  getLists: (boardId: string) => api.get(`/api/trello/boards/${boardId}/lists`),
  getCards: (boardId: string, since?: string) => 
    api.get(`/api/trello/boards/${boardId}/cards`, { params: { since } }),
  sync: () => api.post('/api/trello/sync'),
  getStats: (days: number = 7) => api.get(`/api/trello/stats?days=${days}`),
  getCompletedToday: () => api.get('/api/trello/completed-today'),
};

// GitHub API
export const githubApi = {
  getRepos: () => api.get('/api/github/repos'),
  getCommits: (owner: string, repo: string) => 
    api.get(`/api/github/repos/${owner}/${repo}/commits`),
  getRecentCommits: (days: number = 30) => 
    api.get(`/api/github/commits/recent?days=${days}`),
  getMyPullRequests: (state: string = 'open') => 
    api.get(`/api/github/pulls/my?state=${state}`),
  getStats: (days: number = 30) => api.get(`/api/github/stats?days=${days}`),
  sync: () => api.post('/api/github/sync'),
};

// Stock API
export const stockApi = {
  getPortfolio: () => api.get('/api/stocks/portfolio'),
  getHoldings: () => api.get('/api/stocks/holdings'),
  getPrice: (symbol: string) => api.get(`/api/stocks/price/${symbol}`),
  getPrices: (symbols: string[]) => 
    api.get(`/api/stocks/prices?symbols=${symbols.join(',')}`),
  getMarketOverview: () => api.get('/api/stocks/market/overview'),
  getPerformance: (period: string = '1mo') => 
    api.get(`/api/stocks/performance?period=${period}`),
};

// Weather API
export const weatherApi = {
  getCurrent: () => api.get('/api/weather/current'),
  getForecast: (days: number = 7) => 
    api.get(`/api/weather/forecast?days=${days}`),
};

// Health check
export const healthApi = {
  check: () => api.get('/health'),
};

export default api;
