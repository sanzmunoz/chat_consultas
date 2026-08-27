import { Component, inject, signal, computed, ViewChild, ElementRef, effect } from '@angular/core';
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
    <div class="message-list-wrapper">
      <div class="message-list-container" #scrollContainer (scroll)="onContainerScroll()">
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
          @for (msg of displayedMessages(); track msg.id) {
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

      <!-- Floating Scroll-To-Bottom Button -->
      @if (showScrollBottom()) {
        <button class="scroll-bottom-btn" (click)="scrollToBottom(true)" [title]="'Ir al final'">
          ⬇️
        </button>
      }
    </div>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      overflow: hidden;
      position: relative;
    }
    .message-list-wrapper {
      position: relative;
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }
    .message-list-container {
      flex: 1 1 0%;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      overflow-x: hidden;
      overscroll-behavior-y: contain;
      min-height: 0;
      padding: 16px;
      background-color: var(--bg-surface);
      gap: 12px;
      scrollbar-width: thin;
      scrollbar-color: #94A3B8 #F1F5F9;
    }
    .message-list-container::-webkit-scrollbar {
      width: 6px;
    }
    .message-list-container::-webkit-scrollbar-track {
      background: #F1F5F9;
    }
    .message-list-container::-webkit-scrollbar-thumb {
      background: #94A3B8;
    }
    .message-list-container::-webkit-scrollbar-thumb:hover {
      background: var(--blue-primary);
    }
    .load-more-wrapper {
      display: flex;
      justify-content: center;
      margin-bottom: 8px;
      flex-shrink: 0;
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
    .scroll-bottom-btn {
      position: absolute;
      bottom: 20px;
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
  `]
})
export class MessageListComponent {
  store = inject(ConversationStore);
  auth = inject(AuthService);
  i18n = inject(I18nService);

  @ViewChild('scrollContainer') private scrollContainer?: ElementRef<HTMLDivElement>;

  editingMessageId = signal<string | null>(null);
  editContent: string = '';
  showScrollBottom = signal<boolean>(false);

  displayedMessages = computed(() => [...this.store.messages()].reverse());

  private previousChannelId: string | null = null;
  private isPrepending = false;
  private savedScrollHeight = 0;
  private savedScrollTop = 0;
  private userScrolledUp = false;

  constructor() {
    effect(() => {
      const channelId = this.store.selectedChannelId();
      const msgs = this.displayedMessages();

      setTimeout(() => {
        if (!this.scrollContainer) return;
        const el = this.scrollContainer.nativeElement;

        if (channelId !== this.previousChannelId) {
          this.previousChannelId = channelId;
          this.isPrepending = false;
          this.userScrolledUp = false;
          this.showScrollBottom.set(false);
          el.scrollTop = el.scrollHeight;
        } else if (this.isPrepending) {
          const heightDiff = el.scrollHeight - this.savedScrollHeight;
          el.scrollTop = this.savedScrollTop + heightDiff;
          this.isPrepending = false;
        } else if (!this.userScrolledUp) {
          el.scrollTop = el.scrollHeight;
        }
      }, 50);
    });
  }

  onContainerScroll() {
    if (!this.scrollContainer) return;
    const el = this.scrollContainer.nativeElement;
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
    if (!this.scrollContainer) return;
    const el = this.scrollContainer.nativeElement;
    if (smooth) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    } else {
      el.scrollTop = el.scrollHeight;
    }
    this.userScrolledUp = false;
    this.showScrollBottom.set(false);
  }

  isMyMessage(msg: Message): boolean {
    const current = this.auth.currentUser();
    return current ? current.id === msg.author_id : false;
  }

  onLoadMore() {
    const channelId = this.store.selectedChannelId();
    if (channelId && this.scrollContainer) {
      const el = this.scrollContainer.nativeElement;
      this.savedScrollHeight = el.scrollHeight;
      this.savedScrollTop = el.scrollTop;
      this.isPrepending = true;
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
