"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

// Define available languages
type Language = 'en' | 'jp' | 'vn' | 'th';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  dir: 'ltr' | 'rtl';
}

// Mock Translations (In production, load from JSON files)
const translations: Record<Language, Record<string, string>> = {
  en: { "hello": "Hello", "currency": "USD" },
  jp: { "hello": "こんにちは", "currency": "JPY" },
  vn: { "hello": "Xin chào", "currency": "VND" },
  th: { "hello": "Sawasdee", "currency": "THB" }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  // Persist language preference
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    const saved = localStorage.getItem('sbi_lang') as Language;
    if (saved) setLanguageState(saved);
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('sbi_lang', lang);
    document.documentElement.lang = lang;
  };

  const t = (key: string) => {
    return translations[language][key] || key;
  };

  const dir = language === 'ar' ? 'rtl' : 'ltr'; // Example for future RTL support

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, dir }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
