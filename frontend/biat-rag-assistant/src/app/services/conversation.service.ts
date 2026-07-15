import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, forkJoin, map, switchMap, tap } from 'rxjs';
import {
  AskResponse,
  ChatMessage,
  ConversationApiRead,
  ConversationRecord,
  ConversationSummary,
  MessageApiRead,
} from '../models/chat.models';

@Injectable({
  providedIn: 'root'
})
export class ConversationService {
  private readonly apiBaseUrl = 'http://localhost:8000';
  private readonly conversationsSubject = new BehaviorSubject<ConversationSummary[]>([]);
  private readonly activeConversationSubject = new BehaviorSubject<ConversationRecord | null>(null);
  private readonly activeConversationIdSubject = new BehaviorSubject<string | null>(null);
  private readonly messagesSubject = new BehaviorSubject<ChatMessage[]>([]);

  readonly conversations$ = this.conversationsSubject.asObservable();
  readonly activeConversation$ = this.activeConversationSubject.asObservable();
  readonly activeConversationId$ = this.activeConversationIdSubject.asObservable();
  readonly messages$ = this.messagesSubject.asObservable();

  constructor(private readonly http: HttpClient) {}

  loadConversations(): Observable<ConversationSummary[]> {
    return this.http.get<ConversationApiRead[]>(`${this.apiBaseUrl}/conversations`).pipe(
      map((conversations) => conversations.map((conversation) => this.mapConversationSummary(conversation))),
      tap((conversations) => this.conversationsSubject.next(conversations))
    );
  }

  bootstrapConversationContext(): Observable<ConversationRecord> {
    return this.loadConversations().pipe(
      switchMap((conversations) => {
        if (conversations.length > 0) {
          return this.selectConversation(conversations[0].id);
        }

        return this.createConversation();
      })
    );
  }

  getActiveConversationId(): string | null {
    return this.activeConversationIdSubject.value;
  }

  getActiveConversation(): ConversationRecord | null {
    return this.activeConversationSubject.value;
  }

  selectConversation(conversationId: string): Observable<ConversationRecord> {
    return forkJoin({
      conversation: this.http.get<ConversationApiRead>(`${this.apiBaseUrl}/conversations/${conversationId}`),
      messages: this.http.get<MessageApiRead[]>(`${this.apiBaseUrl}/conversations/${conversationId}/messages`),
    }).pipe(
      map(({ conversation, messages }) => ({
        ...this.mapConversationSummary(conversation),
        messages: messages.map((message) => this.mapMessage(message)),
      })),
      tap((conversation) => this.setActiveConversation(conversation))
    );
  }

  createConversation(title = 'New chat'): Observable<ConversationRecord> {
    return this.http.post<ConversationApiRead>(`${this.apiBaseUrl}/conversations`, {
      title: title.trim() || undefined,
    }).pipe(
      map((conversation) => ({
        ...this.mapConversationSummary(conversation),
        messages: [],
      })),
      tap((conversation) => {
        const conversations = this.upsertConversationSummary(conversation);
        this.conversationsSubject.next(conversations);
        this.setActiveConversation(conversation);
      })
    );
  }

  loadConversationMessages(conversationId: string): Observable<ChatMessage[]> {
    return this.http.get<MessageApiRead[]>(`${this.apiBaseUrl}/conversations/${conversationId}/messages`).pipe(
      map((messages) => messages.map((message) => this.mapMessage(message))),
      tap((messages) => this.messagesSubject.next(messages))
    );
  }

  sendMessage(conversationId: string, question: string): Observable<AskResponse> {
    return this.http.post<AskResponse>(`${this.apiBaseUrl}/ask`, {
      question,
      conversation_id: conversationId,
    }).pipe(
      switchMap((response) =>
        this.selectConversation(response.conversation_id).pipe(
          map(() => response)
        )
      )
    );
  }

  clearState(): void {
    this.conversationsSubject.next([]);
    this.activeConversationSubject.next(null);
    this.activeConversationIdSubject.next(null);
    this.messagesSubject.next([]);
  }

  private setActiveConversation(conversation: ConversationRecord): void {
    this.activeConversationIdSubject.next(conversation.id);
    this.activeConversationSubject.next(conversation);
    this.messagesSubject.next(conversation.messages);
    this.conversationsSubject.next(this.upsertConversationSummary(conversation));
  }

  private upsertConversationSummary(conversation: ConversationSummary): ConversationSummary[] {
    const current = this.conversationsSubject.value;
    const filtered = current.filter((item) => item.id !== conversation.id);
    return [
      {
        id: conversation.id,
        title: conversation.title,
        createdAt: conversation.createdAt,
        updatedAt: conversation.updatedAt,
      },
      ...filtered,
    ];
  }

  private mapConversationSummary(conversation: ConversationApiRead): ConversationSummary {
    return {
      id: conversation.id,
      title: conversation.title,
      createdAt: conversation.created_at,
      updatedAt: conversation.updated_at,
    };
  }

  private mapMessage(message: MessageApiRead): ChatMessage {
    return {
      role: message.role,
      content: message.content,
      createdAt: message.created_at,
    };
  }
}
