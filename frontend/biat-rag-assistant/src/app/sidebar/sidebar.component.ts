import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ConversationSummary } from '../models/chat.models';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css'
})
export class SidebarComponent {
  @Input() conversations: ConversationSummary[] = [];
  @Input() activeConversationId: string | null = null;
  @Output() conversationSelected = new EventEmitter<string>();
  @Output() newChat = new EventEmitter<void>();
  @Output() logout = new EventEmitter<void>();
}
