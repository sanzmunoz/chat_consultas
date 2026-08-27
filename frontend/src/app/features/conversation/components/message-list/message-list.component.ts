import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationStore } from '../../store/conversation.store';
import { AuthService } from '../../../../core/services/auth.service';
import { I18nService } from '../../../../core/services/i18n.service';
import { Message } from '../../../../core/models/message.model';

@Component({
  selector: 'app-message-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="message-list-container">
      <!-- Load More Keyset Button (deferred loading preserving scroll) -->
      @if (store.hasMoreMessages()) {
        <div class="load-more-wrapper">
          <button 
            class="btn-secondary load-more-btn"
            [disabled]="store.isLoadingMessages()"
            (click)="onLoadMore()"
          >
            @if (store.isLoadingMessages()) {
              ⏳ {{ i18n.t('common.loading') }}
            } @else {
              ⬆️ {{ i18n.t('messages.loadMore') }}
            }
          </button>
        </div>
      }

      <div class="messages-stream">
        @for (msg of store.messages(); track msg.id) {
          <div class="message-card" [class.is-mine]="isMyMessage(msg)">
            <div class="message-header">
              <div class="author-info">
                <span class="author-name">{{ msg.author_name || msg.author_username }}</span>
                @if (msg.author_position) {
                  <span class="author-role">{{ msg.author_position }}</span>
                }
              </div>
              <div class="message-meta">
                <span class="msg-date">{{ msg.created_at | date:'shortTime' }}</span>
                
                <!-- Status Badge -->
                <span class="status-indicator" [class]="'status-' + msg.status">
                  @if (msg.status === 'sent') { ✓ }
                  @else if (msg.status === 'pending') { ⏳ }
                  @else { ⚠️ }
                </span>

                <!-- Action Dropdown for author -->
                @if (isMyMessage(msg) || auth.currentUser()?.role === 'admin') {
                  <div class="message-actions">
                    <button class="action-icon-btn" (click)="startEditing(msg)" [title]="i18n.t('messages.edit')">✏️</button>
                    <button class="action-icon-btn" (click)="deleteMsg(msg.id)" [title]="i18n.t('messages.delete')">🗑️</button>
                  </div>
                }
              </div>
            </div>

            <!-- Content or Inline Edit Form -->
            @if (editingMessageId() === msg.id) {
              <div class="inline-edit-box">
                <textarea class="input-field edit-textarea" [(ngModel)]="editContent"></textarea>
                <div class="edit-actions">
                  <button class="btn-primary btn-sm" (click)="saveEdit(msg.id)">{{ i18n.t('common.confirm') }}</button>
                  <button class="btn-secondary btn-sm" (click)="cancelEdit()">{{ i18n.t('common.cancel') }}</button>
                </div>
              </div>
            } @else {
              <div class="message-body">
                <p class="message-text">{{ msg.content }}</p>
                
                @if (msg.is_edited) {
                  <div class="edited-flag">
                    <span class="edited-text">({{ i18n.t('messages.edited') }})</span>
                    @if (msg.original_content) {
                      <span class="original-tooltip" [title]="msg.original_content">
                        ℹ️ {{ i18n.t('messages.original') }}
                      </span>
                    }
                  </div>
                }
              </div>
            }

            <div class="message-footer">
              <span class="msg-ref-tag">{{ msg.msg_ref }}</span>
              @if (msg.read_count > 0) {
                <span class="read-receipt-tag">👁️ {{ msg.read_count }}</span>
              }
            </div>
          </div>
        } @empty {
          <div class="no-messages-box">
            <p>{{ i18n.t('messages.noMessages') }}</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .message-list-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      padding: 16px;
      background-color: var(--bg-surface);
      gap: 12px;
    }
    .load-more-wrapper {
      display: flex;
      justify-content: center;
      margin-bottom: 8px;
    }
    .load-more-btn {
      font-size: 11px;
      padding: 6px 14px;
    }
    .messages-stream {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .message-card {
      background-color: #FFFFFF;
      border: 1px solid var(--border-color);
      padding: 12px 14px;
      transition: all 0.15s ease;
      max-width: 85%;
      align-self: flex-start;
    }
    .message-card.is-mine {
      align-self: flex-end;
      border-color: var(--blue-light);
      background-color: #F0F9FF;
    }
    .message-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
      gap: 8px;
    }
    .author-info {
      display: flex;
      align-items: baseline;
      gap: 6px;
    }
    .author-name {
      font-size: 12px;
      font-weight: 700;
      color: var(--text-main);
    }
    .author-role {
      font-size: 10px;
      color: var(--text-muted);
    }
    .message-meta {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .msg-date {
      font-size: 11px;
      color: var(--text-muted);
    }
    .status-indicator {
      font-size: 11px;
      font-weight: 700;
    }
    .status-sent { color: var(--mint-dark); }
    .status-pending { color: var(--status-pending); }
    .status-failed { color: var(--status-failed); }

    .message-actions {
      display: flex;
      gap: 2px;
    }
    .action-icon-btn {
      background: transparent;
      border: none;
      font-size: 12px;
      cursor: pointer;
      padding: 2px;
      opacity: 0.6;
    }
    .action-icon-btn:hover {
      opacity: 1;
    }
    .message-body {
      margin: 4px 0;
    }
    .message-text {
      margin: 0;
      font-size: 13.5px;
      line-height: 1.45;
      color: var(--text-main);
      word-break: break-word;
    }
    .edited-flag {
      margin-top: 4px;
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .original-tooltip {
      cursor: help;
      text-decoration: underline;
      color: var(--blue-primary);
    }
    .inline-edit-box {
      margin-top: 6px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .edit-textarea {
      min-height: 60px;
      font-size: 13px;
      resize: vertical;
    }
    .edit-actions {
      display: flex;
      gap: 6px;
      justify-content: flex-end;
    }
    .btn-sm {
      padding: 4px 10px;
      font-size: 11px;
    }
    .message-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 6px;
      padding-top: 4px;
      border-top: 1px solid #F1F5F9;
      font-size: 10px;
      color: var(--text-muted);
    }
    .msg-ref-tag {
      font-family: var(--font-mono);
      letter-spacing: 0.5px;
    }
    .read-receipt-tag {
      font-weight: 500;
    }
    .no-messages-box {
      padding: 32px 16px;
      text-align: center;
      color: var(--text-muted);
      background-color: #FFFFFF;
      border: 1px dashed var(--border-color);
    }
  `]
})
export class MessageListComponent {
  store = inject(ConversationStore);
  auth = inject(AuthService);
  i18n = inject(I18nService);

  editingMessageId = signal<string | null>(null);
  editContent: string = '';

  isMyMessage(msg: Message): boolean {
    const current = this.auth.currentUser();
    return current ? current.id === msg.author_id : false;
  }

  onLoadMore() {
    const channelId = this.store.selectedChannelId();
    if (channelId) {
      this.store.loadMessages(channelId, true);
    }
  }

  startEditing(msg: Message) {
    this.editingMessageId.set(msg.id);
    this.editContent = msg.content;
  }

  cancelEdit() {
    this.editingMessageId.set(null);
    this.editContent = '';
  }

  saveEdit(msgId: string) {
    if (this.editContent.trim()) {
      this.store.editMessage(msgId, this.editContent.trim());
      this.cancelEdit();
    }
  }

  deleteMsg(msgId: string) {
    if (confirm(this.i18n.t('messages.deleteConfirm'))) {
      this.store.deleteMessage(msgId);
    }
  }
}
