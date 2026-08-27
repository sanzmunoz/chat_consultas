import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationStore } from '../../store/conversation.store';
import { I18nService } from '../../../../core/services/i18n.service';

@Component({
  selector: 'app-message-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="input-container">
      <div class="input-form">
        <textarea 
          class="input-field message-textarea" 
          [placeholder]="i18n.t('messages.placeholder') + ' ' + currentChannelName()"
          [(ngModel)]="messageText"
          (keydown.enter)="handleKeyDown($event)"
          [disabled]="store.isSendingMessage()"
        ></textarea>

        <button 
          class="btn-primary send-btn"
          [disabled]="store.isSendingMessage() || !messageText.trim()"
          (click)="onSendMessage()"
        >
          @if (store.isSendingMessage()) {
            ⏳
          } @else {
            📨 {{ i18n.t('messages.send') }}
          }
        </button>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      flex-shrink: 0;
    }
    .input-container {
      background-color: #FFFFFF;
      border-top: 2px solid var(--border-color);
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
    }
    .input-form {
      display: flex;
      gap: 8px;
      align-items: flex-end;
    }
    .message-textarea {
      flex: 1;
      min-height: 48px;
      max-height: 120px;
      resize: vertical;
      font-size: 13px;
    }
    .send-btn {
      height: 48px;
      padding: 0 18px;
      font-size: 13px;
    }
    @media (max-width: 768px) {
      .input-container {
        padding: 8px 10px;
      }
      .message-textarea {
        min-height: 42px;
        font-size: 13px;
      }
      .send-btn {
        height: 42px;
        padding: 0 12px;
        font-size: 12px;
      }
    }
  `]
})
export class MessageInputComponent {
  store = inject(ConversationStore);
  i18n = inject(I18nService);

  messageText: string = '';

  currentChannelName(): string {
    const selectedId = this.store.selectedChannelId();
    const chan = this.store.channels().find((c) => c.channel_id === selectedId);
    return chan ? chan.channel_name : '';
  }

  handleKeyDown(event: any) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSendMessage();
    }
  }

  onSendMessage() {
    if (!this.messageText.trim()) return;
    this.store.sendMessage(this.messageText.trim(), 'sent');
    this.messageText = '';
  }
}
