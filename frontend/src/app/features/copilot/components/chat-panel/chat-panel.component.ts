import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CopilotStore } from '../../store/copilot.store';
import { I18nService } from '../../../../core/services/i18n.service';
import { CitationCardComponent } from '../citation-card/citation-card.component';

@Component({
  selector: 'app-chat-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, CitationCardComponent],
  template: `
    <div class="copilot-panel-container">
      <!-- Copilot Header -->
      <div class="copilot-header">
        <div class="copilot-title-row">
          <div class="copilot-avatar">🤖</div>
          <div>
            <h3 class="copilot-title">{{ i18n.t('copilot.title') }}</h3>
            <p class="copilot-subtitle">{{ i18n.t('copilot.subtitle') }}</p>
          </div>
          <div class="model-badge-group">
            <span class="badge badge-blue">{{ i18n.t('copilot.model') }}: gpt-4o-mini</span>
            <span class="badge badge-mint">v1.yaml</span>
          </div>
        </div>

        <div class="disclaimer-banner">
          🔒 {{ i18n.t('copilot.disclaimer') }}
        </div>
      </div>

      <!-- Quick Suggested Questions -->
      <div class="suggested-section">
        <span class="suggested-label">{{ i18n.t('copilot.suggestedQuestions') }}</span>
        <div class="suggested-chips">
          <button class="chip-btn" (click)="askPrompt('¿Cuál es el estado actual de la integración del copiloto?')">
            💡 ¿Estado de integración del copiloto?
          </button>
          <button class="chip-btn" (click)="askPrompt('¿Qué bloqueos tiene el equipo backend?')">
            ⚙️ ¿Bloqueos del equipo backend?
          </button>
          <button class="chip-btn" (click)="askPrompt('¿Qué se ha discutido sobre las políticas RLS?')">
            🛡️ ¿Políticas RLS discutidas?
          </button>
          <button class="chip-btn" (click)="askPrompt('¿Cuál es el estado del deploy en Render?')">
            🚀 ¿Estado del deploy en Render?
          </button>
        </div>
      </div>

      <!-- Chat Stream -->
      <div class="copilot-stream">
        @for (msg of store.chatHistory(); track msg.id) {
          <div class="chat-bubble" [class.user-bubble]="msg.sender === 'user'" [class.copilot-bubble]="msg.sender === 'copilot'">
            <div class="bubble-header">
              <span class="bubble-sender">{{ msg.sender === 'user' ? 'Tú' : 'Copiloto Riwi' }}</span>
              <span class="bubble-time">{{ msg.timestamp | date:'shortTime' }}</span>
              @if (msg.tokensUsed) {
                <span class="bubble-tokens">{{ msg.tokensUsed }} tokens</span>
              }
            </div>

            <div class="bubble-content">
              <p>{{ msg.content }}</p>
            </div>

            <!-- Citations -->
            @if (msg.citations && msg.citations.length > 0) {
              <div class="citations-container">
                <div class="citations-title">{{ i18n.t('copilot.citations') }} ({{ msg.citations.length }}):</div>
                @for (citation of msg.citations; track citation.msg_ref) {
                  <app-citation-card [citation]="citation"></app-citation-card>
                }
              </div>
            }
          </div>
        }

        @if (store.isLoading()) {
          <div class="copilot-thinking-box">
            <div class="spinner"></div>
            <p>{{ i18n.t('copilot.thinking') }}</p>
          </div>
        }
      </div>

      <!-- Input Form -->
      <div class="copilot-input-area">
        <div class="copilot-input-row">
          <input 
            type="text" 
            class="input-field" 
            [placeholder]="i18n.t('copilot.askPlaceholder')"
            [(ngModel)]="queryInput"
            (keydown.enter)="onSendQuery()"
            [disabled]="store.isLoading()"
          />
          <button 
            class="btn-primary copilot-ask-btn"
            [disabled]="store.isLoading() || !queryInput.trim()"
            (click)="onSendQuery()"
          >
            {{ i18n.t('copilot.askButton') }}
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .copilot-panel-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      background-color: #FFFFFF;
      border-left: 1px solid var(--border-color);
    }
    .copilot-header {
      padding: 16px;
      border-bottom: 1px solid var(--border-color);
      background-color: var(--bg-surface);
    }
    .copilot-title-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .copilot-avatar {
      font-size: 24px;
      width: 40px;
      height: 40px;
      background-color: var(--blue-surface);
      border: 1px solid var(--blue-primary);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .copilot-title {
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      color: var(--text-main);
    }
    .copilot-subtitle {
      margin: 2px 0 0;
      font-size: 11px;
      color: var(--text-muted);
    }
    .model-badge-group {
      margin-left: auto;
      display: flex;
      gap: 6px;
    }
    .disclaimer-banner {
      margin-top: 10px;
      padding: 6px 10px;
      background-color: #EFF6FF;
      border: 1px solid #BFDBFE;
      color: #1E40AF;
      font-size: 11px;
      line-height: 1.35;
    }
    .suggested-section {
      padding: 10px 16px;
      background-color: #FFFFFF;
      border-bottom: 1px solid var(--border-color);
    }
    .suggested-label {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      display: block;
      margin-bottom: 6px;
    }
    .suggested-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .chip-btn {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      padding: 4px 8px;
      font-size: 11px;
      cursor: pointer;
      color: var(--text-main);
      transition: all 0.15s ease;
    }
    .chip-btn:hover {
      border-color: var(--blue-primary);
      background-color: var(--blue-surface);
    }
    .copilot-stream {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      background-color: #F8FAFC;
    }
    .chat-bubble {
      padding: 12px 14px;
      border: 1px solid var(--border-color);
      max-width: 90%;
    }
    .user-bubble {
      align-self: flex-end;
      background-color: var(--blue-surface);
      border-color: var(--blue-light);
    }
    .copilot-bubble {
      align-self: flex-start;
      background-color: #FFFFFF;
      border-color: var(--border-color);
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .bubble-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
      font-size: 11px;
    }
    .bubble-sender {
      font-weight: 700;
      color: var(--text-main);
    }
    .bubble-time {
      color: var(--text-muted);
    }
    .bubble-tokens {
      margin-left: auto;
      font-size: 10px;
      color: var(--mint-dark);
      font-weight: 600;
    }
    .bubble-content p {
      margin: 0;
      font-size: 13.5px;
      line-height: 1.45;
      color: var(--text-main);
    }
    .citations-container {
      margin-top: 10px;
      padding-top: 8px;
      border-top: 1px solid var(--border-color);
    }
    .citations-title {
      font-size: 11px;
      font-weight: 700;
      color: var(--mint-dark);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }
    .copilot-thinking-box {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      background-color: #FFFFFF;
      border: 1px dashed var(--blue-primary);
      font-size: 12px;
      color: var(--blue-primary);
    }
    .copilot-input-area {
      padding: 12px 16px;
      background-color: #FFFFFF;
      border-top: 2px solid var(--border-color);
    }
    .copilot-input-row {
      display: flex;
      gap: 8px;
    }
    .copilot-ask-btn {
      padding: 0 18px;
      font-size: 13px;
    }
  `]
})
export class ChatPanelComponent implements OnInit {
  store = inject(CopilotStore);
  i18n = inject(I18nService);

  queryInput: string = '';

  ngOnInit() {
    this.store.loadUsage();
  }

  askPrompt(promptText: string) {
    this.queryInput = promptText;
    this.onSendQuery();
  }

  onSendQuery() {
    if (!this.queryInput.trim()) return;
    this.store.askQuestion(this.queryInput);
    this.queryInput = '';
  }
}
