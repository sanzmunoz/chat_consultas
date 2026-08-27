import { signalStore, withState, withMethods, patchState } from '@ngrx/signals';
import { inject } from '@angular/core';
import { ApiService } from '../../../core/services/api.service';
import { ChannelSummary, ChannelMember } from '../../../core/models/channel.model';
import { Message, SearchMessageItem } from '../../../core/models/message.model';
import { firstValueFrom } from 'rxjs';

interface ConversationState {
  channels: ChannelSummary[];
  selectedChannelId: string | null;
  selectedChannelMembers: ChannelMember[];
  messages: Message[];
  nextCursorCreatedAt: string | null;
  nextCursorId: string | null;
  hasMoreMessages: boolean;
  isLoadingChannels: boolean;
  isLoadingMessages: boolean;
  isSendingMessage: boolean;
  searchResults: SearchMessageItem[];
  isSearching: boolean;
  searchQuery: string;
  error: string | null;
}

const initialState: ConversationState = {
  channels: [],
  selectedChannelId: null,
  selectedChannelMembers: [],
  messages: [],
  nextCursorCreatedAt: null,
  nextCursorId: null,
  hasMoreMessages: false,
  isLoadingChannels: false,
  isLoadingMessages: false,
  isSendingMessage: false,
  searchResults: [],
  isSearching: false,
  searchQuery: '',
  error: null
};

export const ConversationStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withMethods((store, api = inject(ApiService)) => ({
    async loadChannels() {
      patchState(store, { isLoadingChannels: true, error: null });
      try {
        const channels = await firstValueFrom(api.getChannels());
        patchState(store, {
          channels,
          isLoadingChannels: false,
          selectedChannelId: store.selectedChannelId() || (channels.length > 0 ? channels[0].channel_id : null)
        });
        if (store.selectedChannelId()) {
          this.loadMessages(store.selectedChannelId()!, false);
          this.loadChannelMembers(store.selectedChannelId()!);
        }
      } catch (err: any) {
        patchState(store, { isLoadingChannels: false, error: err.message || 'Error cargando canales' });
      }
    },

    async createChannel(name: string, description?: string, type: string = 'public') {
      try {
        const created = await firstValueFrom(api.createChannel({ name, description, type }));
        await this.loadChannels();
        if (created && created.id) {
          this.selectChannel(created.id);
        }
        return true;
      } catch (err: any) {
        patchState(store, { error: err.error?.detail || err.message || 'Error creando canal' });
        return false;
      }
    },

    selectChannel(channelId: string) {
      if (store.selectedChannelId() === channelId) return;
      patchState(store, {
        selectedChannelId: channelId,
        messages: [],
        nextCursorCreatedAt: null,
        nextCursorId: null,
        hasMoreMessages: false,
        searchResults: [],
        searchQuery: ''
      });
      this.loadMessages(channelId, false);
      this.loadChannelMembers(channelId);
    },

    async loadChannelMembers(channelId: string) {
      try {
        const members = await firstValueFrom(api.getChannelMembers(channelId));
        patchState(store, { selectedChannelMembers: members });
      } catch {
        patchState(store, { selectedChannelMembers: [] });
      }
    },

    async loadMessages(channelId: string, append: boolean = false) {
      patchState(store, { isLoadingMessages: true, error: null });
      try {
        const cursorAt = append ? (store.nextCursorCreatedAt() || undefined) : undefined;
        const cursorId = append ? (store.nextCursorId() || undefined) : undefined;

        const res = await firstValueFrom(api.getChannelMessages(channelId, cursorAt, cursorId, 20));
        
        patchState(store, {
          messages: append ? [...store.messages(), ...res.messages] : res.messages,
          nextCursorCreatedAt: res.next_cursor_created_at || null,
          nextCursorId: res.next_cursor_id || null,
          hasMoreMessages: res.has_more,
          isLoadingMessages: false
        });
      } catch (err: any) {
        patchState(store, { isLoadingMessages: false, error: err.message || 'Error cargando mensajes' });
      }
    },

    async sendMessage(content: string, status: string = 'sent') {
      const channelId = store.selectedChannelId();
      if (!channelId || !content.trim()) return;

      patchState(store, { isSendingMessage: true, error: null });
      try {
        const newMsg = await firstValueFrom(api.sendMessage(channelId, content.trim(), status));
        // Add to current message list top
        patchState(store, {
          messages: [newMsg, ...store.messages()],
          isSendingMessage: false
        });
        // Refresh channels list to update last message preview and unread counters
        const channels = await firstValueFrom(api.getChannels());
        patchState(store, { channels });
      } catch (err: any) {
        patchState(store, { isSendingMessage: false, error: err.message || 'Error enviando mensaje' });
      }
    },

    async editMessage(messageId: string, newContent: string) {
      try {
        await firstValueFrom(api.editMessage(messageId, newContent));
        patchState(store, {
          messages: store.messages().map((m) =>
            m.id === messageId
              ? {
                  ...m,
                  original_content: m.original_content || m.content,
                  content: newContent,
                  is_edited: true,
                  edited_at: new Date().toISOString()
                }
              : m
          )
        });
      } catch (err: any) {
        patchState(store, { error: err.message || 'Error editando mensaje' });
      }
    },

    async deleteMessage(messageId: string) {
      try {
        await firstValueFrom(api.deleteMessage(messageId));
        patchState(store, {
          messages: store.messages().filter((m) => m.id !== messageId)
        });
      } catch (err: any) {
        patchState(store, { error: err.message || 'Error eliminando mensaje' });
      }
    },

    async search(query: string) {
      if (!query.trim()) {
        patchState(store, { searchResults: [], searchQuery: '', isSearching: false });
        return;
      }
      patchState(store, { isSearching: true, searchQuery: query, error: null });
      try {
        const results = await firstValueFrom(api.searchMessages(query.trim()));
        patchState(store, { searchResults: results, isSearching: false });
      } catch (err: any) {
        patchState(store, { isSearching: false, error: err.message || 'Error en búsqueda' });
      }
    },

    clearSearch() {
      patchState(store, { searchResults: [], searchQuery: '', isSearching: false });
    }
  }))
);
