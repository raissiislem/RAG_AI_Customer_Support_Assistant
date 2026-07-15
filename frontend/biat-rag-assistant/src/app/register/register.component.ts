import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';
import { ValidationErrorDetail } from '../models/chat.models';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css'
})
export class RegisterComponent {
  @Output() authenticated = new EventEmitter<void>();

  username = '';
  email = '';
  password = '';
  errorMessage = '';
  isLoading = false;

  constructor(private readonly authService: AuthService) {}

  submit(): void {
    if (this.isLoading) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.register({
      username: this.username.trim(),
      email: this.email.trim(),
      password: this.password,
    }).subscribe({
      next: () => this.authenticated.emit(),
      error: (error: HttpErrorResponse) => {
        this.errorMessage = this.extractErrorMessage(error, 'Unable to register. Check the backend auth endpoint and try again.');
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  private extractErrorMessage(error: HttpErrorResponse, fallback: string): string {
    const detail = error.error?.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return this.formatValidationErrors(detail as ValidationErrorDetail[]);
    }

    return fallback;
  }

  private formatValidationErrors(errors: ValidationErrorDetail[]): string {
    return errors
      .map((item) => {
        const field = item.loc?.filter((entry) => typeof entry === 'string').at(-1) ?? 'field';
        return `${field}: ${item.msg ?? 'Invalid value'}`;
      })
      .join(' · ');
  }
}
