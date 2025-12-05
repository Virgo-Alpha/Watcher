import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import Signup from './Signup';
import authReducer, { register } from '../../store/slices/authSlice';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock console methods
const mockConsoleLog = jest.spyOn(console, 'log').mockImplementation();
const mockConsoleError = jest.spyOn(console, 'error').mockImplementation();

describe('Signup Component', () => {
  let store: any;

  const renderSignup = (initialState = {}) => {
    store = configureStore({
      reducer: {
        auth: authReducer,
      },
      preloadedState: {
        auth: {
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          loading: false,
          error: null,
          ...initialState,
        },
      },
    });

    return render(
      <Provider store={store}>
        <BrowserRouter>
          <Signup />
        </BrowserRouter>
      </Provider>
    );
  };

  beforeEach(() => {
    mockNavigate.mockClear();
    mockConsoleLog.mockClear();
    mockConsoleError.mockClear();
    localStorage.clear();
  });

  afterAll(() => {
    mockConsoleLog.mockRestore();
    mockConsoleError.mockRestore();
  });

  describe('Form Rendering', () => {
    it('renders all form fields', () => {
      renderSignup();

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^username$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('renders submit button with correct text', () => {
      renderSignup();
      expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
    });

    it('renders link to login page', () => {
      renderSignup();
      expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login');
    });
  });

  describe('Form Validation', () => {
    it('prevents submission when passwords do not match', async () => {
      renderSignup();

      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: 'John' },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: 'Doe' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password456' },
      });

      // Mock alert
      const alertMock = jest.spyOn(window, 'alert').mockImplementation();

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(alertMock).toHaveBeenCalledWith('Passwords do not match');
      });

      expect(mockNavigate).not.toHaveBeenCalled();
      alertMock.mockRestore();
    });

    it('requires all fields to be filled', () => {
      renderSignup();

      const submitButton = screen.getByRole('button', { name: /sign up/i });
      
      // HTML5 validation should prevent submission
      expect(screen.getByLabelText(/email/i)).toBeRequired();
      expect(screen.getByLabelText(/^username$/i)).toBeRequired();
      expect(screen.getByLabelText(/first name/i)).toBeRequired();
      expect(screen.getByLabelText(/last name/i)).toBeRequired();
      expect(screen.getByLabelText(/^password$/i)).toBeRequired();
      expect(screen.getByLabelText(/confirm password/i)).toBeRequired();
    });
  });

  describe('Registration Flow', () => {
    it('logs registration attempt and navigates on successful registration', async () => {
      // Mock successful API response
      const mockApiClient = require('../../services/api').default;
      mockApiClient.register = jest.fn().mockResolvedValue({
        user: {
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          first_name: 'John',
          last_name: 'Doe',
        },
        access: 'mock-access-token',
        refresh: 'mock-refresh-token',
      });

      renderSignup();

      // Fill out form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: 'John' },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: 'Doe' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(mockConsoleLog).toHaveBeenCalledWith('[Signup] Submitting registration...');
      });

      await waitFor(() => {
        expect(mockConsoleLog).toHaveBeenCalledWith(
          '[Signup] Registration successful, navigating to home...'
        );
      });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('logs error when registration fails', async () => {
      // Mock failed API response
      const mockApiClient = require('../../services/api').default;
      mockApiClient.register = jest.fn().mockRejectedValue(new Error('Email already exists'));

      renderSignup();

      // Fill out form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'existing@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: 'John' },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: 'Doe' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(mockConsoleLog).toHaveBeenCalledWith('[Signup] Submitting registration...');
      });

      await waitFor(() => {
        expect(mockConsoleError).toHaveBeenCalledWith(
          '[Signup] Registration failed:',
          expect.any(Object)
        );
      });

      expect(mockNavigate).not.toHaveBeenCalledWith('/');
    });

    it('dispatches register action with correct payload', async () => {
      const mockApiClient = require('../../services/api').default;
      mockApiClient.register = jest.fn().mockResolvedValue({
        user: { id: 1, email: 'test@example.com', username: 'testuser' },
        access: 'token',
        refresh: 'refresh',
      });

      renderSignup();

      const formData = {
        email: 'test@example.com',
        username: 'testuser',
        firstName: 'John',
        lastName: 'Doe',
        password: 'password123',
      };

      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: formData.email },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: formData.username },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: formData.firstName },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: formData.lastName },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: formData.password },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: formData.password },
      });

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(mockApiClient.register).toHaveBeenCalledWith({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          password_confirm: formData.password,
          first_name: formData.firstName,
          last_name: formData.lastName,
        });
      });
    });
  });

  describe('Loading State', () => {
    it('disables form fields during submission', async () => {
      const mockApiClient = require('../../services/api').default;
      mockApiClient.register = jest.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      renderSignup();

      // Fill form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: 'John' },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: 'Doe' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      // Check loading state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled();
      });
    });

    it('changes button text during loading', async () => {
      const mockApiClient = require('../../services/api').default;
      mockApiClient.register = jest.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      renderSignup();

      // Fill form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: 'John' },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: 'Doe' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' },
      });

      expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /creating account/i })).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when registration fails', async () => {
      const mockApiClient = require('../../services/api').default;
      mockApiClient.register = jest.fn().mockRejectedValue(new Error('Email already exists'));

      renderSignup();

      // Fill form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'existing@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: 'John' },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: 'Doe' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(screen.getByText(/email already exists/i)).toBeInTheDocument();
      });
    });

    it('clears error on component unmount', () => {
      const { unmount } = renderSignup();
      
      const dispatchSpy = jest.spyOn(store, 'dispatch');
      
      unmount();

      expect(dispatchSpy).toHaveBeenCalledWith(expect.objectContaining({
        type: 'auth/clearError',
      }));
    });
  });

  describe('Navigation', () => {
    it('redirects to home if already authenticated', () => {
      renderSignup({ isAuthenticated: true });

      expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    it('does not redirect if not authenticated', () => {
      renderSignup({ isAuthenticated: false });

      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Result Matching Logic', () => {
    it('uses register.fulfilled.match to check success', async () => {
      const mockApiClient = require('../../services/api').default;
      mockApiClient.register = jest.fn().mockResolvedValue({
        user: { id: 1, email: 'test@example.com', username: 'testuser' },
        access: 'token',
        refresh: 'refresh',
      });

      renderSignup();

      // Fill form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^username$/i), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByLabelText(/first name/i), {
        target: { value: 'John' },
      });
      fireEvent.change(screen.getByLabelText(/last name/i), {
        target: { value: 'Doe' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), {
        target: { value: 'password123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

      await waitFor(() => {
        expect(mockConsoleLog).toHaveBeenCalledWith(
          '[Signup] Registration result:',
          expect.any(Object)
        );
      });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });
  });
});
