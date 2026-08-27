import { signalStore, withState, withMethods, patchState } from '@ngrx/signals';
import { inject } from '@angular/core';
import { ApiService } from '../../../core/services/api.service';
import { CopilotCitation, CopilotUsage } from '../../../core/models/copilot.model';
import { firstValueFrom } from 'rxjs';

export interface CopilotChatMessage {
  id: string;
  sender: 'user' | 'copilot';
  content: string;
  citations?: CopilotCitation[];
  timestamp: string;
  tokensUsed?: number;
}

interface CopilotState {
  chatHistory: CopilotChatMessage[];
  usage: CopilotUsage | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: CopilotState = {
  chatHistory: [],
  usage: null,
  isLoading: false,
  error: null
};

export const CopilotStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withMethods((store, api = inject(ApiService)) => ({
    async askQuestion(query: string) {
      if (!query.trim()) return;

      const userMsg: CopilotChatMessage = {
        id: crypto.randomUUID(),
        sender: 'user',
        content: query.trim(),
        timestamp: new Date().toISOString()
      };

      patchState(store, {
        chatHistory: [...store.chatHistory(), userMsg],
        isLoading: true,
        error: null
      });

      try {
        const response = await firstValueFrom(api.queryCopilot(query.trim()));
        
        const copilotMsg: CopilotChatMessage = {
          id: crypto.randomUUID(),
          sender: 'copilot',
          content: response.response,
          citations: response.citations,
          timestamp: new Date().toISOString(),
          tokensUsed: response.total_tokens
        };

        patchState(store, {
          chatHistory: [...store.chatHistory(), copilotMsg],
          isLoading: false
        });

        // Refresh token usage metrics
        this.loadUsage();
      } catch (err: any) {
        patchState(store, {
          isLoading: false,
          error: err.message || 'Error consultando al copiloto'
        });
      }
    },

    async loadUsage() {
      try {
        const usage = await firstValueFrom(api.getCopilotUsage());
        patchState(store, { usage });
      } catch {
        // Silent fail on metrics load
      }
    },

    clearHistory() {
      patchState(store, { chatHistory: [] });
    }
  }))
);
