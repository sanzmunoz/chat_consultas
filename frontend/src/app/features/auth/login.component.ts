import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-wrapper">
      <div class="login-card">
        <div class="login-header">
          <div class="login-logo">RW</div>
          <h2>{{ i18n.t('auth.loginTitle') }}</h2>
          <p class="login-subtitle">{{ i18n.t('auth.loginSubtitle') }}</p>
        </div>

        @if (errorMessage()) {
          <div class="error-banner">
            ⚠️ {{ errorMessage() }}
          </div>
        }

        <form (ngSubmit)="handleLogin()" class="login-form">
          <div class="form-group">
            <label>{{ i18n.t('auth.usernameOrEmail') }}</label>
            <input 
              type="text" 
              class="input-field" 
              [(ngModel)]="identifier" 
              name="identifier" 
              required
              placeholder="smunoz o santiago.munoz@riwi.co"
            />
          </div>

          <div class="form-group">
            <label>{{ i18n.t('auth.password') }}</label>
            <input 
              type="password" 
              class="input-field" 
              [(ngModel)]="password" 
              name="password" 
              required
              placeholder="••••••••"
            />
          </div>

          <button 
            type="submit" 
            class="btn-primary login-btn" 
            [disabled]="isLoading() || !identifier || !password"
          >
            @if (isLoading()) {
              {{ i18n.t('auth.loggingIn') }}
            } @else {
              {{ i18n.t('auth.loginButton') }}
            }
          </button>
        </form>

        <div class="quick-login-section">
          <span class="quick-label">{{ i18n.t('auth.quickLogin') }}</span>
          <div class="quick-buttons">
            <button class="btn-secondary quick-btn" (click)="quickLogin('smunoz')">
              👑 Santiago (Tech Lead)
            </button>
            <button class="btn-secondary quick-btn" (click)="quickLogin('crojas')">
              🎨 Camila (Frontend)
            </button>
            <button class="btn-secondary quick-btn" (click)="quickLogin('nvega')">
              ⚙️ Néstor (Backend)
            </button>
            <button class="btn-secondary quick-btn" (click)="quickLogin('vcastro')">
              🧪 Valentina (QA)
            </button>
            <button class="btn-secondary quick-btn" (click)="quickLogin('alopez')">
              🚀 Andrés (DevOps)
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-wrapper {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: var(--bg-surface);
      padding: 20px;
    }
    .login-card {
      width: 100%;
      max-width: 440px;
      background-color: #FFFFFF;
      border: 2px solid var(--border-color);
      padding: 32px 28px;
    }
    .login-header {
      text-align: center;
      margin-bottom: 24px;
    }
    .login-logo {
      width: 48px;
      height: 48px;
      background-color: var(--blue-primary);
      color: #FFFFFF;
      font-size: 20px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 12px;
      border: 1px solid var(--blue-primary);
    }
    .login-header h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      color: var(--text-main);
    }
    .login-subtitle {
      margin: 4px 0 0;
      color: var(--text-muted);
      font-size: 13px;
    }
    .error-banner {
      background-color: #FEF2F2;
      color: #991B1B;
      border: 1px solid #FCA5A5;
      padding: 10px 12px;
      font-size: 13px;
      margin-bottom: 16px;
    }
    .login-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
      text-align: left;
    }
    .form-group label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-main);
    }
    .login-btn {
      width: 100%;
      justify-content: center;
      padding: 10px;
      font-size: 14px;
      margin-top: 6px;
    }
    .quick-login-section {
      margin-top: 28px;
      padding-top: 20px;
      border-top: 1px dashed var(--border-color);
    }
    .quick-label {
      display: block;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .quick-buttons {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .quick-btn {
      font-size: 11px;
      padding: 6px 8px;
      justify-content: flex-start;
      border-color: var(--border-color);
    }
    .quick-btn:hover {
      border-color: var(--blue-primary);
      background-color: var(--blue-surface);
    }
  `]
})
export class LoginComponent {
  auth = inject(AuthService);
  i18n = inject(I18nService);
  router = inject(Router);

  identifier: string = 'smunoz';
  password: string = 'riwi2026!';
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  quickLogin(username: string) {
    this.identifier = username;
    this.password = 'riwi2026!';
    this.handleLogin();
  }

  handleLogin() {
    if (!this.identifier || !this.password) return;

    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.auth.login(this.identifier, this.password).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.detail || 'Credenciales inválidas');
      }
    });
  }
}
