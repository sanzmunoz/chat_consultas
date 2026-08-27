import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ConversationStore } from '../../store/conversation.store';
import { I18nService } from '../../../../core/services/i18n.service';

@Component({
  selector: 'app-channel-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <aside class="channels-sidebar">
      <div class="sidebar-header">
        <h3 class="sidebar-title">{{ i18n.t('channels.title') }}</h3>
      </div>

      <div class="channel-items">
        @for (channel of store.channels(); track channel.channel_id) {
          <button 
            class="channel-item"
            [class.active]="store.selectedChannelId() === channel.channel_id"
            (click)="store.selectChannel(channel.channel_id)"
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
  `,
  styles: [`
    .channels-sidebar {
      width: 280px;
      background-color: var(--bg-sidebar);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    .sidebar-header {
      padding: 16px 14px 12px;
      border-bottom: 1px solid var(--border-color);
      background-color: #FFFFFF;
    }
    .sidebar-title {
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin: 0;
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
  `]
})
export class ChannelListComponent {
  store = inject(ConversationStore);
  i18n = inject(I18nService);
}
