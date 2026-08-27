import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { I18nService } from './core/services/i18n.service';
import { ConversationStore } from './features/conversation/store/conversation.store';
import { NavbarComponent } from './shared/components/navbar/navbar.component';
import { ChannelListComponent } from './features/conversation/components/channel-list/channel-list.component';
import { MessageListComponent } from './features/conversation/components/message-list/message-list.component';
import { MessageInputComponent } from './features/conversation/components/message-input/message-input.component';
import { MessageSearchComponent } from './features/conversation/components/message-search/message-search.component';
import { ChatPanelComponent } from './features/copilot/components/chat-panel/chat-panel.component';
import { UserProfileComponent } from './features/profile/components/user-profile/user-profile.component';
import { TokenUsageComponent } from './features/profile/components/token-usage/token-usage.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    NavbarComponent,
    ChannelListComponent,
    MessageListComponent,
    MessageInputComponent,
    MessageSearchComponent,
    ChatPanelComponent,
    UserProfileComponent,
    TokenUsageComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  auth = inject(AuthService);
  i18n = inject(I18nService);
  store = inject(ConversationStore);
  router = inject(Router);

  activeTab = signal<'conversation' | 'profile'>('conversation');
  showMembersModal = signal(false);
  mobileShowChat = signal(false);

  ngOnInit() {
    if (this.auth.isAuthenticated()) {
      this.store.loadChannels();
    }
  }

  onTabChange(tab: 'conversation' | 'profile') {
    this.activeTab.set(tab);
    if (tab === 'conversation' && !this.store.selectedChannelId()) {
      this.mobileShowChat.set(false);
    }
  }

  currentChannel() {
    const selectedId = this.store.selectedChannelId();
    return this.store.channels().find((c) => c.channel_id === selectedId);
  }

  toggleMembersModal() {
    this.showMembersModal.update((v) => !v);
  }
}
