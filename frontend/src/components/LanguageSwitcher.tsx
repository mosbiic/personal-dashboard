import { useTranslation } from 'react-i18next';
import { Globe, Check } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
];

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const currentLang = languages.find(l => l.code === i18n.language) || languages[0];
  
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  const handleLanguageChange = (code: string) => {
    i18n.changeLanguage(code);
    setIsOpen(false);
  };
  
  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
        title="Switch Language"
      >
        <Globe className="w-4 h-4" />
        <span className="hidden sm:inline">{currentLang.flag}</span>
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-40 bg-slate-800 rounded-lg border border-slate-700 shadow-xl z-50">
          <div className="py-1">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`
                  w-full flex items-center justify-between px-4 py-2 text-sm transition-colors
                  ${i18n.language === lang.code 
                    ? 'bg-indigo-500/20 text-indigo-400' 
                    : 'text-slate-300 hover:bg-slate-700'}
                `}
              >
                <span className="flex items-center gap-2">
                  <span>{lang.flag}</span>
                  <span>{lang.name}</span>
                </span>
                {i18n.language === lang.code && (
                  <Check className="w-4 h-4" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
