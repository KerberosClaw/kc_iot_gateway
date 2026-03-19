import { useState, useEffect } from 'react';
import type { Lang } from '../lib/i18n';

export function useLang() {
  const [lang, setLang] = useState<Lang>(() => {
    const saved = localStorage.getItem('iot-lang');
    return (saved === 'en' ? 'en' : 'zh') as Lang;
  });

  useEffect(() => {
    localStorage.setItem('iot-lang', lang);
  }, [lang]);

  const toggle = () => setLang(prev => prev === 'zh' ? 'en' : 'zh');

  return { lang, toggle };
}
