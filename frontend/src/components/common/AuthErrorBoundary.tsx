import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error boundary to catch authentication-related errors
 * and prevent the app from crashing
 */
class AuthErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details for debugging
    console.error('[AuthErrorBoundary] Caught error:', error);
    console.error('[AuthErrorBoundary] Error info:', errorInfo);

    // Check if this is an authentication error
    const isAuthError = 
      error.message.includes('401') ||
      error.message.includes('Unauthorized') ||
      error.message.includes('Authentication') ||
      error.message.includes('token');

    if (isAuthError) {
      console.warn('[AuthErrorBoundary] Authentication error detected');
      // Don't auto-logout here, let the API client handle it
    }

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const isAuthError = 
        this.state.error?.message.includes('401') ||
        this.state.error?.message.includes('Unauthorized') ||
        this.state.error?.message.includes('Authentication');

      return (
        <div style={{
          padding: '40px',
          maxWidth: '600px',
          margin: '0 auto',
          textAlign: 'center',
          fontFamily: 'Arial, Helvetica, sans-serif',
        }}>
          <h2 style={{ color: '#DD4B39', marginBottom: '20px' }}>
            {isAuthError ? 'Authentication Error' : 'Something went wrong'}
          </h2>
          
          <p style={{ color: '#333', marginBottom: '20px' }}>
            {isAuthError 
              ? 'There was a problem with your authentication. Please try logging in again.'
              : 'An unexpected error occurred. Please try refreshing the page.'}
          </p>

          {this.state.error && (
            <details style={{
              marginBottom: '20px',
              padding: '10px',
              background: '#f5f5f5',
              border: '1px solid #e5e5e5',
              borderRadius: '4px',
              textAlign: 'left',
            }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '10px' }}>
                Error Details
              </summary>
              <pre style={{
                fontSize: '12px',
                overflow: 'auto',
                color: '#777',
              }}>
                {this.state.error.message}
              </pre>
            </details>
          )}

          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
            <button
              onClick={this.handleReset}
              style={{
                padding: '10px 20px',
                background: '#3366CC',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Try Again
            </button>
            
            <button
              onClick={this.handleReload}
              style={{
                padding: '10px 20px',
                background: '#777',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Reload Page
            </button>

            {isAuthError && (
              <button
                onClick={() => window.location.href = '/login'}
                style={{
                  padding: '10px 20px',
                  background: '#DD4B39',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Go to Login
              </button>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default AuthErrorBoundary;
