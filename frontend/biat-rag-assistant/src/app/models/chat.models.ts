export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  matched?: boolean;
  createdAt?: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface ConversationApiRead {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageApiRead {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ConversationRecord extends ConversationSummary {
  messages: ChatMessage[];
  isDraft?: boolean;
}

export interface AskResponse {
  answer: string;
  sources: string[];
  matched: boolean;
  standalone_question?: string;
  conversation_id: string;
}

export interface AuthUser {
  id?: string;
  username: string;
  email?: string;
}

export interface AuthSession {
  access_token: string;
  token_type?: string;
  user?: AuthUser;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface ValidationErrorDetail {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
}
