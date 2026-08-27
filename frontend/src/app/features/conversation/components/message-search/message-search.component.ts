import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationStore } from '../../store/conversation.store';
import { I18nService } from '../../../../core/services/i18n.service';
import { SafeHtmlPipe } from '../../../../shared/pipes/highlight.pipe';

@Component({
  selector: 'app-message-search',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeHtmlPipe],
  template: `
    <div class="search-container">
      <div class="search-input-wrapper">
        <span class="search-icon">🔍</span>
        <input 
          type="text" 
          class="input-field search-input"
          [placeholder]="i18n.t('messages.searchPlaceholder')"
          [(ngModel)]="query"
          (keydown.enter)="onSearch()"
        />
        @if (query) {
          <button class="clear-btn" (click)="onClear()">✕</button>
        }
        <button class="btn-primary search-action-btn" (click)="onSearch()">
          {{ i18n.t('messages.send') === 'Enviar' ? 'Buscar' : 'Search' }}
        </button>
      </div>

      <!-- Search Results Dropdown/Modal -->
      @if (store.searchResults().length > 0 || (store.searchQuery() && !store.isSearching())) {
        <div class="search-results-panel">
          <div class="results-header">
            <h4>{{ i18n.t('messages.searchResults') }} ({{ store.searchResults().length }})</h4>
            <button class="close-results-btn" (click)="onClear()">✕</button>
          </div>

          <div class="results-list">
            @for (item of store.searchResults(); track item.id) {
              <div class="result-card" (click)="onSelectResult(item)">
                <div class="result-meta">
                  <span class="badge badge-blue">{{ item.channel_name }}</span>
                  <span class="result-author">{{ item.author_name }}</span>
                  <span class="result-date">{{ item.created_at | date:'short' }}</span>
                </div>
                <div class="result-snippet" [innerHTML]="item.highlighted_content || item.content | safeHtml"></div>
              </div>
            } @empty {
              <div class="no-results">
                <p>{{ i18n.t('messages.noSearchResults') }}</p>
              </div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .search-container {
      position: relative;
      width: 100%;
    }
    .search-input-wrapper {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .search-icon {
      font-size: 14px;
      color: var(--text-muted);
    }
    .search-input {
      flex: 1;
      height: 36px;
      font-size: 13px;
    }
    .clear-btn {
      background: transparent;
      border: none;
      font-size: 14px;
      cursor: pointer;
      color: var(--text-muted);
      padding: 4px;
    }
    .search-action-btn {
      height: 36px;
      padding: 0 12px;
      font-size: 12px;
    }
    .search-results-panel {
      position: absolute;
      top: 42px;
      left: 0;
      right: 0;
      background-color: #FFFFFF;
      border: 2px solid var(--blue-primary);
      box-shadow: 0 8px 24px rgba(0,0,0,0.12);
      z-index: 100;
      max-height: 420px;
      display: flex;
      flex-direction: column;
    }
    .results-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background-color: var(--blue-surface);
      border-bottom: 1px solid var(--border-color);
    }
    .results-header h4 {
      margin: 0;
      font-size: 12px;
      font-weight: 700;
      color: var(--blue-primary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .close-results-btn {
      background: transparent;
      border: none;
      font-weight: 700;
      cursor: pointer;
      color: var(--text-muted);
    }
    .results-list {
      overflow-y: auto;
      padding: 8px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .result-card {
      padding: 10px 12px;
      border: 1px solid var(--border-color);
      background-color: #FFFFFF;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .result-card:hover {
      border-color: var(--blue-primary);
      background-color: var(--bg-surface);
    }
    .result-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
      font-size: 11px;
    }
    .result-author {
      font-weight: 600;
      color: var(--text-main);
    }
    .result-date {
      color: var(--text-muted);
      margin-left: auto;
    }
    .result-snippet {
      font-size: 13px;
      color: var(--text-main);
      line-height: 1.4;
    }
    .no-results {
      padding: 24px 16px;
      text-align: center;
      color: var(--text-muted);
      font-size: 13px;
    }
  `]
})
export class MessageSearchComponent {
  store = inject(ConversationStore);
  i18n = inject(I18nService);

  query: string = '';

  onSearch() {
    this.store.search(this.query);
  }

  onClear() {
    this.query = '';
    this.store.clearSearch();
  }

  onSelectResult(item: any) {
    this.store.selectChannel(item.channel_id);
    this.onClear();
  }
}
