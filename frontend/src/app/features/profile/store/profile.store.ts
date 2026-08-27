import { signalStore, withState, withMethods, patchState } from '@ngrx/signals';
import { inject } from '@angular/core';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { User } from '../../../core/models/user.model';
import { CopilotUsage } from '../../../core/models/copilot.model';
import { firstValueFrom } from 'rxjs';

interface ProfileState {
  user: User | null;
  usage: CopilotUsage | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  successMessage: string | null;
}

const initialState: ProfileState = {
  user: null,
  usage: null,
  isLoading: false,
  isSaving: false,
  error: null,
  successMessage: null
};

export const ProfileStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withMethods((store, api = inject(ApiService), auth = inject(AuthService)) => ({
    async loadProfile() {
      patchState(store, { isLoading: true, error: null });
      const current = auth.currentUser();
      if (current) {
        patchState(store, { user: current });
      }
      try {
        const usage = await firstValueFrom(api.getCopilotUsage());
        patchState(store, { usage, isLoading: false });
      } catch (err: any) {
        patchState(store, { isLoading: false });
      }
    },

    async updateProfile(displayName: string, position: string) {
      const current = store.user();
      if (!current) return;

      patchState(store, { isSaving: true, error: null, successMessage: null });
      try {
        await firstValueFrom(api.updateProfile(current.id, {
          display_name: displayName,
          position: position
        }));

        const updatedUser: User = {
          ...current,
          display_name: displayName,
          position: position
        };

        patchState(store, {
          user: updatedUser,
          isSaving: false,
          successMessage: 'Perfil actualizado con éxito.'
        });

        // Update AuthService user
        auth.currentUser.set(updatedUser);
      } catch (err: any) {
        patchState(store, {
          isSaving: false,
          error: err.message || 'Error actualizando el perfil.'
        });
      }
    }
  }))
);
