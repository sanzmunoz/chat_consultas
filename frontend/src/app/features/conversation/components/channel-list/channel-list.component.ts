import { Component, Output, EventEmitter, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationStore } from '../../store/conversation.store';
import { AuthService } from '../../../../core/services/auth.service';
import { I18nService } from '../../../../core/services/i18n.service';

@Component({
  selector: 'app-channel-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <aside class="channels-sidebar">
      <div class="sidebar-header">
        <h3 class="sidebar-title">{{ i18n.t('channels.title') }}</h3>
        @if (auth.currentUser()?.role === 'admin') {
          <button 
            class="add-channel-btn" 
            (click)="openCreateModal()" 
            [title]="i18n.t('channels.create')"
          >
            +
          </button>
        }
      </div>

      <div class="channel-items">
        @for (channel of store.channels(); track channel.channel_id) {
          <button 
            class="channel-item" 
            [class.active]="store.selectedChannelId() === channel.channel_id"
            (click)="onSelectChannel(channel.channel_id)"
          >
            <div class="channel-main">
              <div class="channel-name-row">
                <span class="channel-hash">#</span>
                <span class="channel-name">{{ channel.channel_name.replace('#', '') }}</span>
                <span class="badge" [class.badge-blue]="channel.channel_type === 'public'" [class.badge-gray]="channel.channel_type === 'private'">
                  {{ channel.channel_type === 'public' ? i18n.t('channels.public') : i18n.t('channels.private') }}
                </span>
              </div>
              
              @if (channel.last_message_content) {
                <p class="channel-snippet">
                  <span class="snippet-author">{{ channel.last_message_author_name }}:</span> 
                  {{ channel.last_message_content }}
                </p>
              }
            </div>

            @if (channel.unread_count > 0) {
              <span class="unread-badge">{{ channel.unread_count }}</span>
            }
          </button>
        } @empty {
          <div class="no-channels">
            <p>{{ i18n.t('channels.noChannels') }}</p>
          </div>
        }
      </div>
    </aside>

    <!-- Create Channel Modal -->
    @if (showCreateModal()) {
      <div class="modal-backdrop" (click)="closeCreateModal()">
        <div class="modal-card" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h4 class="modal-title">✨ {{ i18n.t('channels.create') }}</h4>
            <button class="close-btn" (click)="closeCreateModal()">✕</button>
          </div>
          <form class="modal-body" (submit)="submitCreateChannel($event)">
            <div class="form-group">
              <label class="form-label">{{ i18n.t('channels.channelName') }} *</label>
              <div class="input-prefix-wrapper">
                <span class="prefix-hash">#</span>
                <input 
                  type="text" 
                  class="form-input prefix-input" 
                  [(ngModel)]="newChannelName" 
                  name="channelName" 
                  placeholder="ej. backend-alerts" 
                  required
                />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">{{ i18n.t('channels.description') }}</label>
              <input 
                type="text" 
                class="form-input" 
                [(ngModel)]="newChannelDesc" 
                name="channelDesc" 
                placeholder="Propósito del canal..." 
              />
            </div>
            <div class="form-group">
              <label class="form-label">{{ i18n.t('channels.type') }}</label>
              <select class="form-select" [(ngModel)]="newChannelType" name="channelType">
                <option value="public">{{ i18n.t('channels.public') }} (Visible para todos)</option>
                <option value="private">{{ i18n.t('channels.private') }} (Privado)</option>
              </select>
            </div>
            @if (createError) {
              <div class="error-msg">{{ createError }}</div>
            }
            <div class="modal-actions">
              <button type="button" class="btn-secondary" (click)="closeCreateModal()">{{ i18n.t('channels.cancel') }}</button>
              <button type="submit" class="btn-primary" [disabled]="isSubmitting || !newChannelName.trim()">
                {{ isSubmitting ? 'Creando...' : i18n.t('channels.create') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    }
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      flex-shrink: 0;
    }
    .channels-sidebar {
      width: 280px;
      background-color: var(--bg-sidebar);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    .sidebar-header {
      padding: 14px 14px 12px;
      border-bottom: 1px solid var(--border-color);
      background-color: #FFFFFF;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .sidebar-title {
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin: 0;
    }
    .add-channel-btn {
      width: 26px;
      height: 26px;
      background-color: var(--blue-primary);
      color: #FFFFFF;
      border: 1px solid var(--blue-primary);
      font-size: 16px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      line-height: 1;
      transition: background-color 0.15s ease;
    }
    .add-channel-btn:hover {
      background-color: #0369A1;
    }
    .channel-items {
      flex: 1;
      overflow-y: auto;
      padding: 8px 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .channel-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: transparent;
      border: none;
      border-left: 3px solid transparent;
      text-align: left;
      cursor: pointer;
      width: 100%;
      transition: all 0.15s ease;
    }
    .channel-item:hover {
      background-color: #E2E8F0;
    }
    .channel-item.active {
      background-color: #FFFFFF;
      border-left-color: var(--blue-primary);
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .channel-main {
      flex: 1;
      overflow: hidden;
      margin-right: 8px;
    }
    .channel-name-row {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .channel-hash {
      color: var(--text-muted);
      font-weight: 700;
    }
    .channel-name {
      font-weight: 600;
      color: var(--text-main);
      font-size: 13px;
    }
    .channel-snippet {
      margin: 3px 0 0;
      font-size: 11px;
      color: var(--text-muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .snippet-author {
      font-weight: 500;
      color: var(--text-main);
    }
    .unread-badge {
      background-color: var(--mint-green);
      color: #FFFFFF;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      min-width: 18px;
      text-align: center;
    }
    .no-channels {
      padding: 20px 14px;
      text-align: center;
      color: var(--text-muted);
      font-size: 12px;
    }
    /* Modal styles */
    .modal-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: rgba(15, 23, 42, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .modal-card {
      background: #FFFFFF;
      border: 2px solid var(--border-color);
      width: 90%;
      max-width: 440px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    }
    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 16px;
      border-bottom: 2px solid var(--border-color);
      background-color: var(--bg-surface);
    }
    .modal-title {
      font-size: 14px;
      font-weight: 700;
      margin: 0;
      color: var(--text-main);
    }
    .close-btn {
      background: transparent;
      border: none;
      font-size: 16px;
      cursor: pointer;
      color: var(--text-muted);
    }
    .modal-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .form-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-main);
    }
    .input-prefix-wrapper {
      display: flex;
      align-items: center;
      border: 1px solid var(--border-color);
      background-color: #FFFFFF;
    }
    .prefix-hash {
      padding: 0 10px;
      font-weight: 700;
      color: var(--text-muted);
      background-color: var(--bg-surface);
      border-right: 1px solid var(--border-color);
      height: 36px;
      display: flex;
      align-items: center;
    }
    .prefix-input {
      border: none !important;
      outline: none;
      flex: 1;
      height: 36px;
      padding: 0 10px;
      font-size: 13px;
    }
    .form-input {
      height: 36px;
      padding: 0 10px;
      border: 1px solid var(--border-color);
      font-size: 13px;
      outline: none;
    }
    .form-select {
      height: 36px;
      padding: 0 10px;
      border: 1px solid var(--border-color);
      font-size: 13px;
      background-color: #FFFFFF;
      outline: none;
    }
    .error-msg {
      font-size: 12px;
      color: #DC2626;
      background-color: #FEF2F2;
      padding: 6px 10px;
      border: 1px solid #FCA5A5;
    }
    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
  `]
})
export class ChannelListComponent {
  store = inject(ConversationStore);
  auth = inject(AuthService);
  i18n = inject(I18nService);

  @Output() channelSelected = new EventEmitter<string>();

  showCreateModal = signal(false);
  newChannelName = '';
  newChannelDesc = '';
  newChannelType = 'public';
  createError: string | null = null;
  isSubmitting = false;

  openCreateModal() {
    this.newChannelName = '';
    this.newChannelDesc = '';
    this.newChannelType = 'public';
    this.createError = null;
    this.showCreateModal.set(true);
  }

  closeCreateModal() {
    this.showCreateModal.set(false);
  }

  async submitCreateChannel(event: Event) {
    event.preventDefault();
    if (!this.newChannelName.trim()) return;

    this.isSubmitting = true;
    this.createError = null;

    const success = await this.store.createChannel(
      this.newChannelName.trim(),
      this.newChannelDesc.trim(),
      this.newChannelType
    );

    this.isSubmitting = false;
    if (success) {
      this.showCreateModal.set(false);
    } else {
      this.createError = this.store.error() || 'Error al crear el canal';
    }
  }

  onSelectChannel(channelId: string) {
    this.store.selectChannel(channelId);
    this.channelSelected.emit(channelId);
  }
}
