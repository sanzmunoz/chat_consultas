import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { I18nService } from '../../../core/services/i18n.service';

@Component({
  selector: 'app-loading-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (isLoading) {
      <div class="state-container loading-box">
        <div class="spinner"></div>
        <p>{{ message || i18n.t('common.loading') }}</p>
      </div>
    } @else if (error) {
      <div class="state-container error-box">
        <div class="error-icon">⚠️</div>
        <h4>{{ i18n.t('common.error') }}</h4>
        <p>{{ error }}</p>
        @if (showRetry) {
          <button class="btn-primary retry-btn" (click)="retry.emit()">{{ i18n.t('common.retry') }}</button>
        }
      </div>
    } @else if (isEmpty) {
      <div class="state-container empty-box">
        <div class="empty-icon">📂</div>
        <p>{{ emptyMessage || i18n.t('channels.noChannels') }}</p>
      </div>
    }
  `,
  styles: [`
    .state-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 32px 16px;
      text-align: center;
      background-color: #FFFFFF;
      border: 1px solid var(--border-color);
      margin: 16px 0;
    }
    .spinner {
      width: 32px;
      height: 32px;
      border: 3px solid var(--blue-surface);
      border-top-color: var(--blue-primary);
      animation: spin 0.8s linear infinite;
      margin-bottom: 12px;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .error-box {
      border-color: #FCA5A5;
      background-color: #FEF2F2;
      color: #991B1B;
    }
    .error-icon {
      font-size: 28px;
      margin-bottom: 8px;
    }
    .empty-box {
      border-style: dashed;
      color: var(--text-muted);
    }
    .empty-icon {
      font-size: 32px;
      margin-bottom: 8px;
    }
    .retry-btn {
      margin-top: 12px;
    }
  `]
})
export class LoadingStateComponent {
  i18n = inject(I18nService);

  @Input() isLoading: boolean = false;
  @Input() isEmpty: boolean = false;
  @Input() error: string | null = null;
  @Input() message?: string;
  @Input() emptyMessage?: string;
  @Input() showRetry: boolean = true;
  @Output() retry = new EventEmitter<void>();
}
