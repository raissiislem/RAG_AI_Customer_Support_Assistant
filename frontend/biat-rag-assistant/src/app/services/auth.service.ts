import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { AuthSession, AuthUser, LoginPayload, RegisterPayload } from '../models/chat.models';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly tokenKey = 'biat_jwt';
  private readonly userKey = 'biat_user';
  private readonly apiBaseUrl = 'http://localhost:8000';
  private readonly currentUserSubject = new BehaviorSubject<AuthUser | null>(this.readUser());

  readonly currentUser$ = this.currentUserSubject.asObservable();

  constructor(private readonly http: HttpClient) {}

  login(payload: LoginPayload): Observable<AuthSession> {
    return this.http.post<AuthSession>(`${this.apiBaseUrl}/auth/login`, payload).pipe(
      tap((session) => this.storeSession(session))
    );
  }

  register(payload: RegisterPayload): Observable<AuthSession> {
    return this.http.post<AuthSession>(`${this.apiBaseUrl}/auth/register`, payload).pipe(
      tap((session) => this.storeSession(session))
    );
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    this.currentUserSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isAuthenticated(): boolean {
    return Boolean(this.getToken());
  }

  getCurrentUser(): AuthUser | null {
    return this.currentUserSubject.value;
  }

  private storeSession(session: AuthSession): void {
    localStorage.setItem(this.tokenKey, session.access_token);
    if (session.user) {
      localStorage.setItem(this.userKey, JSON.stringify(session.user));
      this.currentUserSubject.next(session.user);
    }
  }

  private readUser(): AuthUser | null {
    const rawUser = localStorage.getItem(this.userKey);
    if (!rawUser) {
      return null;
    }

    try {
      return JSON.parse(rawUser) as AuthUser;
    } catch {
      localStorage.removeItem(this.userKey);
      return null;
    }
  }
}
