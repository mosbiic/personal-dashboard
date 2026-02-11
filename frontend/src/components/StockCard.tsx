import { useTranslation } from 'react-i18next';
import { TrendingUp, TrendingDown, DollarSign, Loader2 } from 'lucide-react';
import type { PortfolioData } from '../types/dashboard';

interface StockCardProps {
  data?: PortfolioData;
  isLoading?: boolean;
  error?: string | null;
}

export function StockCard({ data, isLoading, error }: StockCardProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-green-400" />
            <h3 className="text-lg font-semibold text-white">{t('cards.stock.title')}</h3>
          </div>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-green-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-red-700/50 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="w-5 h-5 text-green-400" />
          <h3 className="text-lg font-semibold text-white">{t('cards.stock.title')}</h3>
        </div>
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    );
  }

  const summary = data?.summary;
  const totalPnl = summary?.total_pnl ?? 0;
  const totalPnlPct = summary?.total_pnl_pct ?? 0;
  const totalValue = summary?.total_value ?? 0;
  const isProfit = totalPnl >= 0;

  const holdings = data?.holdings ?? [];
  const topHoldings = holdings
    .slice()
    .sort((a, b) => Math.abs(b.pnl ?? 0) - Math.abs(a.pnl ?? 0))
    .slice(0, 3);

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg hover:border-green-500/50 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <DollarSign className="w-5 h-5 text-green-400" />
          </div>
          <h3 className="text-lg font-semibold text-white">{t('cards.stock.title')}</h3>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${
          isProfit ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
          {isProfit ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span className="text-sm font-medium">{totalPnlPct.toFixed(2)}%</span>
        </div>
      </div>

      <div className="mb-4">
        <p className={`text-3xl font-bold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
          {isProfit ? '+' : ''}${totalPnl.toFixed(2)}
        </p>
        <p className="text-sm text-slate-400 mt-1">
          {t('cards.stock.totalValue')}: ${totalValue.toFixed(2)}
        </p>
      </div>

      {topHoldings.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-sm text-slate-400 mb-3">{t('cards.stock.topHoldings')}</p>
          <div className="space-y-2">
            {topHoldings.map((holding) => {
              const pnl = holding.pnl ?? 0;
              const isHoldingProfit = pnl >= 0;
              return (
                <div key={holding.symbol} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{holding.symbol}</span>
                    <span className="text-slate-500">{holding.shares} {t('cards.stock.shares')}</span>
                  </div>
                  <span className={isHoldingProfit ? 'text-green-400' : 'text-red-400'}>
                    {isHoldingProfit ? '+' : ''}${pnl.toFixed(0)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
