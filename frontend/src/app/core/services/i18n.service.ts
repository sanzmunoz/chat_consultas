import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class I18nService {
  currentLang = signal<'es' | 'en'>('es');
  private translations: Record<string, any> = {};

  constructor() {
    this.loadTranslations(this.currentLang());
  }

  async setLanguage(lang: 'es' | 'en') {
    this.currentLang.set(lang);
    await this.loadTranslations(lang);
  }

  async loadTranslations(lang: string) {
    try {
      const response = await fetch(`/assets/i18n/${lang}.json`);
      if (response.ok) {
        this.translations = await response.json();
      }
    } catch (e) {
      console.warn(`Failed to load translations for ${lang}`, e);
    }
  }

  translate(path: string): string {
    const keys = path.split('.');
    let current: any = this.translations;
    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return path;
      }
    }
    return typeof current === 'string' ? current : path;
  }

  t(path: string): string {
    return this.translate(path);
  }
}
