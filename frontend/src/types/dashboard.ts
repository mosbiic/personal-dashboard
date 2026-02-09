// Dashboard 数据类型定义

export interface DashboardSummary {
  date: string;
  trello: TrelloSummary;
  github: GitHubSummary;
  stocks: StockSummary;
  weather: WeatherSummary;
}

export interface TrelloSummary {
  completed_today: number;
  pending: number;
  error?: string;
}

export interface GitHubSummary {
  commits_today: number;
  prs: number;
  error?: string;
}

export interface StockSummary {
  total_pnl: number;
  daily_change: number;
  total_value?: number;
  error?: string;
}

export interface WeatherSummary {
  temp: number;
  condition: string;
  icon?: string;
  feels_like?: number;
  humidity?: number;
  error?: string;
}

// 时间轴活动类型
export interface TimelineActivity {
  id: string;
  source_type: 'github' | 'trello' | 'stock' | 'weather' | 'session';
  source_id: string;
  activity_type: string;
  title: string;
  description: string;
  url?: string;
  metadata?: Record<string, any>;
  occurred_at: string;
  icon: string;
}

export interface TimelineData {
  start: string;
  end: string;
  count: number;
  activities: TimelineActivity[];
}

// Trello 类型
export interface TrelloBoard {
  id: string;
  name: string;
}

export interface TrelloCard {
  id: string;
  name: string;
  desc?: string;
  due?: string;
  dueComplete?: boolean;
  idList: string;
  idBoard: string;
  labels?: TrelloLabel[];
}

export interface TrelloLabel {
  id: string;
  name: string;
  color: string;
}

export interface TrelloStats {
  completed_today: number;
  pending: number;
  total_cards: number;
}

// GitHub 类型
export interface GitHubCommit {
  sha: string;
  message: string;
  author: {
    name: string;
    date: string;
  };
  committer: {
    name: string;
    date: string;
  };
  repository?: {
    full_name: string;
  };
  html_url?: string;
}

export interface GitHubPullRequest {
  number: number;
  title: string;
  state: 'open' | 'closed';
  merged: boolean;
  html_url: string;
  repository?: {
    full_name: string;
  };
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  stargazers_count: number;
  language?: string;
  updated_at: string;
}

export interface GitHubStats {
  commits_today: number;
  prs: number;
  repos?: GitHubRepo[];
  commits?: GitHubCommit[];
}

// 股票类型
export interface StockHolding {
  symbol: string;
  name: string;
  shares: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  pnl?: number;
  pnl_pct?: number;
  market?: string;
  currency?: string;
}

export interface PortfolioSummary {
  total_cost: number;
  total_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  holdings_count: number;
}

export interface PortfolioData {
  holdings: StockHolding[];
  summary: PortfolioSummary;
}

export interface StockPrice {
  symbol: string;
  price: number;
  change?: number;
  change_pct?: number;
  name?: string;
  currency?: string;
  market?: string;
}

// 天气类型
export interface WeatherCurrent {
  temperature: number;
  feels_like: number;
  humidity: number;
  description: string;
  icon: string;
  wind_speed?: number;
  pressure?: number;
  uv_index?: number;
}

export interface WeatherForecast {
  date: string;
  max_temp: number;
  min_temp: number;
  description: string;
  icon: string;
}

export interface WeatherData {
  current: WeatherCurrent;
  forecast?: WeatherForecast[];
  location?: {
    name: string;
    country: string;
  };
}
