import { useTranslation } from 'react-i18next';
import { Cloud, Droplets, Wind, Thermometer, Loader2 } from 'lucide-react';
import type { WeatherData } from '../types/dashboard';

interface WeatherCardProps {
  data?: WeatherData;
  isLoading?: boolean;
  error?: string | null;
}

const weatherIcons: Record<string, string> = {
  '☀️': '☀️',
  '🌤️': '🌤️',
  '⛅': '⛅',
  '☁️': '☁️',
  '🌧️': '🌧️',
  '⛈️': '⛈️',
  '🌩️': '🌩️',
  '🌨️': '🌨️',
  '❄️': '❄️',
  '🌫️': '🌫️',
  '🌡️': '🌡️',
};

export function WeatherCard({ data, isLoading, error }: WeatherCardProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cloud className="w-5 h-5 text-sky-400" />
            <h3 className="text-lg font-semibold text-white">{t('cards.weather.title')}</h3>
          </div>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-red-700/50 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <Cloud className="w-5 h-5 text-sky-400" />
          <h3 className="text-lg font-semibold text-white">{t('cards.weather.title')}</h3>
        </div>
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    );
  }

  const current = data?.current;
  const temp = current?.temperature ?? 0;
  const feelsLike = current?.feels_like ?? 0;
  const humidity = current?.humidity ?? 0;
  const condition = current?.description ?? t('cards.weather.unknown');
  const icon = current?.icon ?? '🌡️';
  const windSpeed = current?.wind_speed;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg hover:border-sky-500/50 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-sky-500/20 rounded-lg">
            <Cloud className="w-5 h-5 text-sky-400" />
          </div>
          <h3 className="text-lg font-semibold text-white">{t('cards.weather.title')}</h3>
        </div>
        <span className="text-2xl">{weatherIcons[icon] || icon}</span>
      </div>

      <div className="flex items-end gap-2 mb-4">
        <p className="text-4xl font-bold text-white">{Math.round(temp)}°</p>
        <span className="text-slate-400 mb-1">{condition}</span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <Thermometer className="w-4 h-4 text-orange-400 mx-auto mb-1" />
          <p className="text-xs text-slate-400">{t('cards.weather.feelsLike')}</p>
          <p className="text-sm font-medium text-white">{Math.round(feelsLike)}°</p>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <Droplets className="w-4 h-4 text-blue-400 mx-auto mb-1" />
          <p className="text-xs text-slate-400">{t('cards.weather.humidity')}</p>
          <p className="text-sm font-medium text-white">{humidity}%</p>
        </div>

        {windSpeed !== undefined && (
          <div className="bg-slate-700/50 rounded-lg p-3 text-center">
            <Wind className="w-4 h-4 text-teal-400 mx-auto mb-1" />
            <p className="text-xs text-slate-400">{t('cards.weather.windSpeed')}</p>
            <p className="text-sm font-medium text-white">{windSpeed}km/h</p>
          </div>
        )}
      </div>

      {data?.location && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-sm text-slate-400 text-center">
            {data.location.name}, {data.location.country}
          </p>
        </div>
      )}
    </div>
  );
}
