import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { I18nService } from '../../../core/services/i18n.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="navbar-header">
      <div class="navbar-brand">
        <div class="brand-logo">RW</div>
        <div class="brand-info">
          <h1 class="brand-title">Riwi Co.</h1>
          <span class="brand-tag">Mensajería & Copiloto IA</span>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <nav class="nav-tabs">
        <button 
          class="tab-btn" 
          [class.active]="activeTab === 'conversation'"
          (click)="tabChange.emit('conversation')"
        >
          💬 {{ i18n.t('nav.conversations') }}
        </button>
        <button 
          class="tab-btn" 
          [class.active]="activeTab === 'profile'"
          (click)="tabChange.emit('profile')"
        >
          👤 {{ i18n.t('nav.profile') }}
        </button>
      </nav>

      <!-- Right Actions: Language Switcher & User Profile -->
      <div class="navbar-actions">
        <!-- Language Switcher -->
        <div class="lang-switch">
          <button 
            class="lang-btn" 
            [class.active]="i18n.currentLang() === 'es'"
            (click)="i18n.setLanguage('es')"
          >
            ES
          </button>
          <button 
            class="lang-btn" 
            [class.active]="i18n.currentLang() === 'en'"
            (click)="i18n.setLanguage('en')"
          >
            EN
          </button>
        </div>

        <!-- User Profile Pill -->
        @if (auth.currentUser(); as user) {
          <div class="user-pill">
            <div class="user-avatar">{{ user.display_name.charAt(0) }}</div>
            <div class="user-details">
              <span class="user-name">{{ user.display_name }}</span>
              <span class="user-position">{{ user.position }} ({{ user.role }})</span>
            </div>
            <button class="logout-btn" (click)="auth.logout()" [title]="i18n.t('auth.logout')">
              Salir ->
            </button>
          </div>
        }
      </div>
    </header>
  `,
  styles: [`
    .navbar-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 60px;
      padding: 0 20px;
      background-color: #FFFFFF;
      border-bottom: 2px solid var(--border-color);
      gap: 16px;
    }
    .navbar-brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .brand-logo {
      width: 34px;
      height: 34px;
      background-color: var(--blue-primary);
      color: #FFFFFF;
      font-weight: 700;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--blue-primary);
    }
    .brand-title {
      font-size: 16px;
      font-weight: 700;
      margin: 0;
      color: var(--text-main);
      line-height: 1.2;
    }
    .brand-tag {
      font-size: 11px;
      color: var(--text-muted);
    }
    .nav-tabs {
      display: flex;
      gap: 4px;
      height: 100%;
      align-items: flex-end;
    }
    .tab-btn {
      height: 48px;
      padding: 0 16px;
      background: transparent;
      border: none;
      border-bottom: 3px solid transparent;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .tab-btn:hover {
      color: var(--blue-primary);
      background-color: var(--bg-surface);
    }
    .tab-btn.active {
      color: var(--blue-primary);
      border-bottom-color: var(--blue-primary);
      background-color: var(--blue-surface);
    }
    .navbar-actions {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .lang-switch {
      display: flex;
      border: 1px solid var(--border-color);
    }
    .lang-btn {
      background: #FFFFFF;
      border: none;
      padding: 4px 8px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      color: var(--text-muted);
    }
    .lang-btn.active {
      background-color: var(--blue-primary);
      color: #FFFFFF;
    }
    .user-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 10px;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
    }
    .user-avatar {
      width: 28px;
      height: 28px;
      background-color: var(--mint-green);
      color: #FFFFFF;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
    }
    .user-details {
      display: flex;
      flex-direction: column;
      text-align: left;
    }
    .user-name {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-main);
      line-height: 1.1;
    }
    .user-position {
      font-size: 10px;
      color: var(--text-muted);
    }
    .logout-btn {
      background: #FEF2F2;
      border: 1px solid #FECACA;
      cursor: pointer;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      margin-left: 6px;
      color: #DC2626;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .logout-btn:hover {
      background-color: #FEE2E2;
      border-color: #F87171;
    }
    @media (max-width: 768px) {
      .brand-info, .user-position {
        display: none;
      }
      .tab-btn {
        padding: 0 10px;
        font-size: 12px;
      }
    }
  `]
})
export class NavbarComponent {
  auth = inject(AuthService);
  i18n = inject(I18nService);

  @Input() activeTab: 'conversation' | 'profile' = 'conversation';
  @Output() tabChange = new EventEmitter<'conversation' | 'profile'>();
}
