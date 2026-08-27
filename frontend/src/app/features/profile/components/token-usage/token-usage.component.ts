import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProfileStore } from '../../store/profile.store';
import { I18nService } from '../../../../core/services/i18n.service';

@Component({
  selector: 'app-token-usage',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="usage-card">
      <div class="card-header">
        <h3 class="card-title">{{ i18n.t('profile.tokenUsageTitle') }}</h3>
      </div>

      @if (store.usage(); as usage) {
        <div class="metrics-grid">
          <div class="metric-box">
            <span class="metric-value">{{ usage.total_queries }}</span>
            <span class="metric-label">{{ i18n.t('profile.totalQueries') }}</span>
          </div>

          <div class="metric-box">
            <span class="metric-value text-blue">{{ usage.total_prompt_tokens | number }}</span>
            <span class="metric-label">{{ i18n.t('profile.promptTokens') }}</span>
          </div>

          <div class="metric-box">
            <span class="metric-value text-mint">{{ usage.total_completion_tokens | number }}</span>
            <span class="metric-label">{{ i18n.t('profile.completionTokens') }}</span>
          </div>

          <div class="metric-box total-box">
            <span class="metric-value text-bold">{{ usage.total_tokens_used | number }}</span>
            <span class="metric-label">{{ i18n.t('profile.totalTokens') }}</span>
          </div>
        </div>

        @if (usage.last_query_at) {
          <div class="last-query-info">
            <span>{{ i18n.t('profile.lastQuery') }}:</span>
            <span class="font-mono">{{ usage.last_query_at | date:'medium' }}</span>
          </div>
        }
      } @else {
        <div class="no-usage-box">
          <p>No se registran consultas recientes al Copiloto.</p>
        </div>
      }
    </div>
  `,
  styles: [`
    .usage-card {
      background-color: #FFFFFF;
      border: 1px solid var(--border-color);
      padding: 20px;
    }
    .card-header {
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border-color);
    }
    .card-title {
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      color: var(--text-main);
    }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .metric-box {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      padding: 14px 10px;
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .total-box {
      border-color: var(--blue-primary);
      background-color: var(--blue-surface);
    }
    .metric-value {
      font-size: 20px;
      font-weight: 700;
      font-family: var(--font-mono);
      color: var(--text-main);
    }
    .text-blue { color: var(--blue-primary); }
    .text-mint { color: var(--mint-dark); }
    .text-bold { color: #0369A1; }

    .metric-label {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }
    .last-query-info {
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      gap: 6px;
      align-items: center;
      padding-top: 10px;
      border-top: 1px dashed var(--border-color);
    }
    .no-usage-box {
      padding: 20px;
      text-align: center;
      color: var(--text-muted);
      font-size: 13px;
    }
  `]
})
export class TokenUsageComponent implements OnInit {
  store = inject(ProfileStore);
  i18n = inject(I18nService);

  ngOnInit() {
    this.store.loadProfile();
  }
}
