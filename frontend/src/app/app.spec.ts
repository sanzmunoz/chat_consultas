import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { AuthService } from './core/services/auth.service';
import { I18nService } from './core/services/i18n.service';
import { CitationCardComponent } from './features/copilot/components/citation-card/citation-card.component';
import { LoginComponent } from './features/auth/login.component';

describe('Riwi Internal Chat & Copilot Frontend Suite', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App, CitationCardComponent, LoginComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([])
      ]
    }).compileComponents();
  });

  it('1. should create the root App component', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('2. should initialize I18nService with default Spanish language', () => {
    const i18n = TestBed.inject(I18nService);
    expect(i18n.currentLang()).toBe('es');
    expect(i18n.t('nav.conversations')).toBeDefined();
  });

  it('3. should support language switching in I18nService', async () => {
    const i18n = TestBed.inject(I18nService);
    await i18n.setLanguage('en');
    expect(i18n.currentLang()).toBe('en');
  });

  it('4. should render CitationCardComponent with channel, author and similarity score', () => {
    const fixture = TestBed.createComponent(CitationCardComponent);
    fixture.componentRef.setInput('citation', {
      msg_ref: 'msg-1001',
      channel_name: '#general',
      author_name: 'Santiago Muñoz',
      content_snippet: 'Prueba de cita RAG',
      similarity_score: 0.8845
    });
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('msg-1001');
    expect(compiled.textContent).toContain('#general');
    expect(compiled.textContent).toContain('Santiago Muñoz');
    expect(compiled.textContent).toContain('88.4% sim');
  });

  it('5. should create the LoginComponent for authentication', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    const loginComp = fixture.componentInstance;
    expect(loginComp).toBeTruthy();
    expect(loginComp.identifier).toBe('smunoz');
  });
});
