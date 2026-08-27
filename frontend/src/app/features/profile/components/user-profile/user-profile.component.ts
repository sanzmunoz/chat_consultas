import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProfileStore } from '../../store/profile.store';
import { I18nService } from '../../../../core/services/i18n.service';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="profile-card">
      <div class="card-header">
        <h3 class="card-title">{{ i18n.t('profile.title') }}</h3>
      </div>

      @if (store.successMessage()) {
        <div class="success-banner">
          ✓ {{ store.successMessage() }}
        </div>
      }
      @if (store.error()) {
        <div class="error-banner">
          ⚠️ {{ store.error() }}
        </div>
      }

      @if (store.user(); as user) {
        <div class="profile-details-grid">
          <div class="info-group">
            <label>{{ i18n.t('profile.username') }}</label>
            <span class="info-value font-mono">{{ user.username }}</span>
          </div>

          <div class="info-group">
            <label>{{ i18n.t('profile.email') }}</label>
            <span class="info-value">{{ user.email }}</span>
          </div>

          <div class="info-group">
            <label>{{ i18n.t('profile.role') }}</label>
            <span class="badge" [class.badge-blue]="user.role === 'admin'" [class.badge-mint]="user.role === 'member'">
              {{ user.role }}
            </span>
          </div>

          <div class="form-field-group">
            <label>{{ i18n.t('profile.displayName') }}</label>
            <input type="text" class="input-field" [(ngModel)]="editName" />
          </div>

          <div class="form-field-group">
            <label>{{ i18n.t('profile.position') }}</label>
            <input type="text" class="input-field" [(ngModel)]="editPosition" />
          </div>
        </div>

        <button 
          class="btn-primary save-btn" 
          [disabled]="store.isSaving()"
          (click)="onSaveProfile()"
        >
          @if (store.isSaving()) {
            {{ i18n.t('profile.saving') }}
          } @else {
            💾 {{ i18n.t('profile.saveChanges') }}
          }
        </button>
      }
    </div>
  `,
  styles: [`
    .profile-card {
      background-color: #FFFFFF;
      border: 1px solid var(--border-color);
      padding: 20px;
    }
    .card-header {
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border-color);
    }
    .card-title {
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      color: var(--text-main);
    }
    .profile-details-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 20px;
    }
    .info-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .info-group label, .form-field-group label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }
    .info-value {
      font-size: 14px;
      color: var(--text-main);
      font-weight: 500;
    }
    .font-mono {
      font-family: var(--font-mono);
    }
    .form-field-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
      grid-column: span 2;
    }
    .save-btn {
      margin-top: 8px;
    }
    .success-banner {
      background-color: #ECFDF5;
      color: #065F46;
      border: 1px solid #A7F3D0;
      padding: 8px 12px;
      margin-bottom: 14px;
      font-size: 12px;
    }
    .error-banner {
      background-color: #FEF2F2;
      color: #991B1B;
      border: 1px solid #FCA5A5;
      padding: 8px 12px;
      margin-bottom: 14px;
      font-size: 12px;
    }
    @media (max-width: 640px) {
      .profile-details-grid {
        grid-template-columns: 1fr;
      }
      .form-field-group {
        grid-column: span 1;
      }
    }
  `]
})
export class UserProfileComponent implements OnInit {
  store = inject(ProfileStore);
  i18n = inject(I18nService);

  editName: string = '';
  editPosition: string = '';

  ngOnInit() {
    this.store.loadProfile();
    const user = this.store.user();
    if (user) {
      this.editName = user.display_name;
      this.editPosition = user.position;
    }
  }

  onSaveProfile() {
    if (this.editName.trim()) {
      this.store.updateProfile(this.editName.trim(), this.editPosition.trim());
    }
  }
}
