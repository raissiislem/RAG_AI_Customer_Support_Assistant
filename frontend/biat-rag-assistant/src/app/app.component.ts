import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoginComponent } from './login/login.component';
import { RegisterComponent } from './register/register.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { ChatComponent } from './chat/chat.component';
import { AuthService } from './services/auth.service';
import { ConversationService } from './services/conversation.service';
import { ConversationSummary } from './models/chat.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, LoginComponent, RegisterComponent, SidebarComponent, ChatComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  readonly title = 'BIAT RAG Assistant';
  showRegister = false;
  conversations: ConversationSummary[] = [];
  activeConversationId: string | null = null;

  constructor(
    readonly authService: AuthService,
    readonly conversationService: ConversationService,
  ) {}

  ngOnInit(): void {
    this.conversationService.conversations$.subscribe((conversations) => {
      this.conversations = conversations;
    });

    this.conversationService.activeConversationId$.subscribe((conversationId) => {
      this.activeConversationId = conversationId;
    });

    if (this.authService.isAuthenticated()) {
      this.conversationService.bootstrapConversationContext().subscribe();
    }
  }

  toggleAuthMode(): void {
    this.showRegister = !this.showRegister;
  }

  onAuthenticated(): void {
    this.showRegister = false;
    this.conversationService.bootstrapConversationContext().subscribe();
  }

  logout(): void {
    this.authService.logout();
    this.conversationService.clearState();
  }

  selectConversation(conversationId: string): void {
    this.conversationService.selectConversation(conversationId).subscribe();
  }

  createConversation(): void {
    this.conversationService.createConversation().subscribe();
  }
}
