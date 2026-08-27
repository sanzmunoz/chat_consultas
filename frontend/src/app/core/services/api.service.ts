import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ChannelSummary, ChannelMember } from '../models/channel.model';
import { Message, KeysetMessageList, SearchMessageItem } from '../models/message.model';
import { CopilotQueryResponse, CopilotUsage } from '../models/copilot.model';
import { User } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);

  // Channels
  getChannels(): Observable<ChannelSummary[]> {
    return this.http.get<ChannelSummary[]>('/api/channels');
  }

  getChannelMembers(channelId: string): Observable<ChannelMember[]> {
    return this.http.get<ChannelMember[]>(`/api/channels/${channelId}/members`);
  }

  // Messages
  getChannelMessages(
    channelId: string,
    cursorCreatedAt?: string,
    cursorId?: string,
    limit: number = 20
  ): Observable<KeysetMessageList> {
    let params = new HttpParams().set('limit', limit.toString());
    if (cursorCreatedAt) params = params.set('cursor_created_at', cursorCreatedAt);
    if (cursorId) params = params.set('cursor_id', cursorId);
    return this.http.get<KeysetMessageList>(`/api/channels/${channelId}/messages`, { params });
  }

  sendMessage(channelId: string, content: string, status: string = 'sent'): Observable<Message> {
    return this.http.post<Message>(`/api/channels/${channelId}/messages`, { content, status });
  }

  editMessage(messageId: string, content: string): Observable<any> {
    return this.http.patch(`/api/messages/${messageId}`, { content });
  }

  deleteMessage(messageId: string): Observable<any> {
    return this.http.delete(`/api/messages/${messageId}`);
  }

  searchMessages(query: string, limit: number = 20): Observable<SearchMessageItem[]> {
    const params = new HttpParams().set('q', query).set('limit', limit.toString());
    return this.http.get<SearchMessageItem[]>('/api/messages/search', { params });
  }

  // Copilot RAG
  queryCopilot(query: string): Observable<CopilotQueryResponse> {
    return this.http.post<CopilotQueryResponse>('/api/copilot/query', { query });
  }

  getCopilotUsage(): Observable<CopilotUsage> {
    return this.http.get<CopilotUsage>('/api/copilot/usage');
  }

  // Users
  getUsers(search?: string, role?: string): Observable<{ users: User[] }> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    if (role) params = params.set('role', role);
    return this.http.get<{ users: User[] }>('/api/users', { params });
  }

  updateProfile(userId: string, data: { display_name?: string; position?: string }): Observable<any> {
    return this.http.patch(`/api/users/${userId}`, data);
  }
}
