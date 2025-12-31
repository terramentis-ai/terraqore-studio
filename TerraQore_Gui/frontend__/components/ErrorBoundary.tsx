import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<React.PropsWithChildren<{}>, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Optionally log to a monitoring service
    console.error('UI ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen w-full flex items-center justify-center bg-black text-zinc-200">
          <div className="max-w-md w-full rounded-xl border border-white/10 bg-white/5 p-6 text-sm">
            <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
            <p className="text-zinc-400 mb-4">The UI hit an unexpected error. Try refreshing, or check the backend status.</p>
            {this.state.error && (
              <pre className="text-xs bg-black/40 border border-white/10 rounded-md p-3 overflow-auto text-red-300">
                {this.state.error.message}
              </pre>
            )}
          </div>
        </div>
      );
    }

    return this.props.children as React.ReactElement;
  }
}

export default ErrorBoundary;
