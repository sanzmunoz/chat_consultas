import { Component, inject, OnInit, ViewChild, ElementRef, signal, effect } from '@angular/core';
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

      <!-- Chat Stream (Scrollable mouse / manual) -->
      <div class="copilot-stream" #copilotStream (scroll)="onStreamScroll()">
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

      <!-- Floating Scroll-To-Bottom Button -->
      @if (showScrollBottom()) {
        <button class="scroll-bottom-btn" (click)="scrollToBottom(true)" [title]="'Ir al final'">
          ⬇️
        </button>
      }

      <!-- Input Form (Fixed at the bottom) -->
      <div class="copilot-input-area">
        <div class="copilot-input-row">
          <textarea 
            class="input-field copilot-textarea" 
            [placeholder]="i18n.t('copilot.askPlaceholder')"
            [(ngModel)]="queryInput"
            (keydown.enter)="handleKeyDown($event)"
            [disabled]="store.isLoading()"
            rows="1"
          ></textarea>
          <button 
            class="btn-primary copilot-ask-btn"
            [disabled]="store.isLoading() || !queryInput.trim()"
            (click)="onSendQuery()"
          >
            @if (store.isLoading()) {
              ⏳
            } @else {
              {{ i18n.t('copilot.askButton') }}
            }
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      height: 100%;
      overflow: hidden;
    }
    .copilot-panel-container {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      height: 100%;
      background-color: #FFFFFF;
      border-left: 1px solid var(--border-color);
      overflow: hidden;
      position: relative;
    }
    .copilot-header {
      flex-shrink: 0;
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
      flex-shrink: 0;
      padding: 10px 16px;
      background-color: #FFFFFF;
      border-bottom: 1px solid var(--border-color);
      max-height: 110px;
      overflow-y: auto;
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
      flex: 1 1 0%;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      overscroll-behavior-y: contain;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      background-color: #F8FAFC;
      scrollbar-width: thin;
      scrollbar-color: #94A3B8 #F1F5F9;
    }
    .copilot-stream::-webkit-scrollbar {
      width: 6px;
    }
    .copilot-stream::-webkit-scrollbar-track {
      background: #F1F5F9;
    }
    .copilot-stream::-webkit-scrollbar-thumb {
      background: #94A3B8;
    }
    .copilot-stream::-webkit-scrollbar-thumb:hover {
      background: var(--blue-primary);
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
      word-break: break-word;
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
    .spinner {
      width: 14px;
      height: 14px;
      border: 2px solid var(--blue-surface);
      border-top-color: var(--blue-primary);
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .scroll-bottom-btn {
      position: absolute;
      bottom: 74px;
      right: 20px;
      width: 32px;
      height: 32px;
      background-color: var(--blue-primary);
      color: #FFFFFF;
      border: 1px solid var(--blue-primary);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      z-index: 20;
      font-size: 12px;
      transition: background-color 0.15s ease;
    }
    .scroll-bottom-btn:hover {
      background-color: #0369A1;
    }
    .copilot-input-area {
      flex-shrink: 0;
      padding: 12px 16px;
      background-color: #FFFFFF;
      border-top: 2px solid var(--border-color);
      position: relative;
      z-index: 10;
    }
    .copilot-input-row {
      display: flex;
      gap: 8px;
      align-items: flex-end;
    }
    .copilot-textarea {
      flex: 1;
      min-height: 44px;
      max-height: 100px;
      resize: vertical;
      font-size: 13px;
      line-height: 1.4;
    }
    .copilot-ask-btn {
      height: 44px;
      padding: 0 18px;
      font-size: 13px;
      white-space: nowrap;
      flex-shrink: 0;
    }
    @media (max-width: 768px) {
      .copilot-header {
        padding: 10px 12px;
      }
      .copilot-avatar {
        width: 32px;
        height: 32px;
        font-size: 18px;
      }
      .copilot-title {
        font-size: 13px;
      }
      .copilot-subtitle {
        display: none;
      }
      .model-badge-group {
        display: none;
      }
      .suggested-section {
        padding: 8px 10px;
        max-height: 90px;
      }
      .copilot-stream {
        padding: 10px 8px;
        gap: 10px;
      }
      .chat-bubble {
        max-width: 96%;
        padding: 10px 10px;
      }
      .copilot-input-area {
        padding: 8px 10px;
      }
      .copilot-textarea {
        min-height: 40px;
        font-size: 13px;
      }
      .copilot-ask-btn {
        height: 40px;
        padding: 0 12px;
        font-size: 12px;
      }
      .scroll-bottom-btn {
        bottom: 60px;
        right: 12px;
      }
    }
  `]
})
export class ChatPanelComponent implements OnInit {
  store = inject(CopilotStore);
  i18n = inject(I18nService);

  @ViewChild('copilotStream') private copilotStream?: ElementRef<HTMLDivElement>;

  queryInput: string = '';
  showScrollBottom = signal<boolean>(false);

  private userScrolledUp = false;

  constructor() {
    effect(() => {
      this.store.chatHistory();
      const loading = this.store.isLoading();

      setTimeout(() => {
        if (!this.userScrolledUp || loading) {
          this.scrollToBottom(false);
        }
      }, 50);
    });
  }

  ngOnInit() {
    this.store.loadUsage();
  }

  onStreamScroll() {
    if (!this.copilotStream) return;
    const el = this.copilotStream.nativeElement;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;

    if (distanceFromBottom > 100) {
      this.userScrolledUp = true;
      this.showScrollBottom.set(true);
    } else {
      this.userScrolledUp = false;
      this.showScrollBottom.set(false);
    }
  }

  scrollToBottom(smooth: boolean = true) {
    if (!this.copilotStream) return;
    const el = this.copilotStream.nativeElement;
    if (smooth) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    } else {
      el.scrollTop = el.scrollHeight;
    }
    this.userScrolledUp = false;
    this.showScrollBottom.set(false);
  }

  askPrompt(promptText: string) {
    this.queryInput = promptText;
    this.onSendQuery();
  }

  handleKeyDown(event: any) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSendQuery();
    }
  }

  onSendQuery() {
    if (!this.queryInput.trim() || this.store.isLoading()) return;
    this.store.askQuestion(this.queryInput);
    this.queryInput = '';
    this.userScrolledUp = false;
    setTimeout(() => this.scrollToBottom(true), 50);
  }
}
