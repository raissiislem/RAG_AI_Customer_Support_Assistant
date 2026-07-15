import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConversationService } from '../services/conversation.service';
import { ChatMessage, ConversationRecord } from '../models/chat.models';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css'
})
export class ChatComponent implements OnInit {
  @ViewChild('messagesViewport') messagesViewport?: ElementRef<HTMLDivElement>;
  activeConversation: ConversationRecord | null = null;
  messages: ChatMessage[] = [];

  readonly suggestions = [
    'Comment ouvrir un compte courant ?',
    'Quels sont les services de banque digitale ?',
    'Comment faire un virement ?',
    'Quels documents pour un crédit auto ?'
  ];

  question = '';
  isLoading = false;
  errorMessage = '';
  emptyStateTitle = 'Start a conversation';
  emptyStateMessage = 'Choose a chat on the left or create a new one to begin.';

  constructor(private readonly conversationService: ConversationService) {
    this.conversationService.activeConversation$.subscribe((conversation) => {
      this.activeConversation = conversation;
      this.scrollToBottom();
    });

    this.conversationService.messages$.subscribe((messages) => {
      this.messages = messages;
      this.scrollToBottom();
    });
  }

  ngOnInit(): void {}

  submitQuestion(): void {
    const trimmedQuestion = this.question.trim();
    if (!trimmedQuestion || this.isLoading) {
      return;
    }

    const activeConversation = this.conversationService.getActiveConversation();
    if (!activeConversation) {
      this.conversationService.createConversation().subscribe({
        next: (conversation) => this.sendConversationMessage(conversation.id, trimmedQuestion),
        error: () => {
          this.errorMessage = 'Le service de réponse est indisponible pour le moment. Vérifiez que le backend BIAT RAG tourne sur le port 8000.';
          this.isLoading = false;
        },
      });
      return;
    }

    this.sendConversationMessage(activeConversation.id, trimmedQuestion);
  }

  useSuggestion(suggestion: string): void {
    this.question = suggestion;
  }

  trackByMessageIndex(index: number): number {
    return index;
  }

  private sendConversationMessage(conversationId: string, trimmedQuestion: string): void {
    this.question = '';
    this.isLoading = true;
    this.errorMessage = '';
    this.scrollToBottom();

    this.conversationService.sendMessage(conversationId, trimmedQuestion).subscribe({
      error: () => {
        this.errorMessage = 'Le service de réponse est indisponible pour le moment. Vérifiez que le backend BIAT RAG tourne sur le port 8000.';
      },
      complete: () => {
        this.isLoading = false;
        this.scrollToBottom();
      }
    });
  }

  private scrollToBottom(): void {
    queueMicrotask(() => {
      if (!this.messagesViewport?.nativeElement) {
        return;
      }

      this.messagesViewport.nativeElement.scrollTo({
        top: this.messagesViewport.nativeElement.scrollHeight,
        behavior: 'smooth',
      });
    });
  }
}
