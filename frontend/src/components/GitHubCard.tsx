import { useTranslation } from 'react-i18next';
import { GitCommit, GitPullRequest, GitBranch, Loader2 } from 'lucide-react';
import type { GitHubSummary } from '../types/dashboard';

interface GitHubCardProps {
  data?: GitHubSummary;
  isLoading?: boolean;
  error?: string | null;
}

export function GitHubCard({ data, isLoading, error }: GitHubCardProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">{t('cards.github.title')}</h3>
          </div>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-red-700/50 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <GitBranch className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">{t('cards.github.title')}</h3>
        </div>
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    );
  }

  const commits = data?.commits_today ?? 0;
  const prs = data?.prs ?? 0;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg hover:border-purple-500/50 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <GitBranch className="w-5 h-5 text-purple-400" />
          </div>
          <h3 className="text-lg font-semibold text-white">{t('cards.github.title')}</h3>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <GitCommit className="w-4 h-4 text-green-400" />
            <span className="text-sm text-slate-400">{t('cards.github.commitsToday')}</span>
          </div>
          <p className="text-2xl font-bold text-white">{commits}</p>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <GitPullRequest className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-slate-400">{t('cards.github.openPRs')}</span>
          </div>
          <p className="text-2xl font-bold text-white">{prs}</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-400"></div>
            <span className="text-slate-400">{t('cards.github.active')}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-blue-400"></div>
            <span className="text-slate-400">{t('cards.github.collaborating')}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
