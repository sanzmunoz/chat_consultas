import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of, throwError } from 'rxjs';
import { User, AuthResponse } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private readonly ACCESS_TOKEN_KEY = 'rw_access_token';
  private readonly REFRESH_TOKEN_KEY = 'rw_refresh_token';
  private readonly USER_KEY = 'rw_user_data';

  // Signals
  currentUser = signal<User | null>(this.getStoredUser());
  accessToken = signal<string | null>(localStorage.getItem(this.ACCESS_TOKEN_KEY));
  isAuthenticated = computed(() => !!this.accessToken() && !!this.currentUser());

  private getStoredUser(): User | null {
    const raw = localStorage.getItem(this.USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  login(usernameOrEmail: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>('/api/auth/login', {
      username_or_email: usernameOrEmail,
      password: password
    }).pipe(
      tap((res) => {
        this.setSession(res);
      })
    );
  }

  refreshToken(): Observable<AuthResponse | null> {
    const refreshTok = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    if (!refreshTok) {
      this.logout();
      return of(null);
    }

    return this.http.post<AuthResponse>('/api/auth/refresh', {
      refresh_token: refreshTok
    }).pipe(
      tap((res) => {
        this.setSession(res);
      }),
      catchError((err) => {
        this.logout();
        return throwError(() => err);
      })
    );
  }

  private setSession(authRes: AuthResponse) {
    if (authRes.access_token) {
      localStorage.setItem(this.ACCESS_TOKEN_KEY, authRes.access_token);
      this.accessToken.set(authRes.access_token);
    }
    if (authRes.refresh_token) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, authRes.refresh_token);
    }
    if (authRes.user) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(authRes.user));
      this.currentUser.set(authRes.user);
    }
  }

  logout() {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.accessToken.set(null);
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }
}
